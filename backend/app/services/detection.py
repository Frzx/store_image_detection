import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw

from app.config import model_settings


SAFE_LABEL_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


class ObjectDetector:
    def __init__(self, artifact_dir: str | None = None):
        self.artifact_dir = Path(artifact_dir or model_settings.MODEL_ARTIFACT_DIR)
        self.model_path = self.artifact_dir / "model.onnx"
        self.metadata_path = self.artifact_dir / "metadata.json"
        self.preprocessor_path = self.artifact_dir / "preprocessor_config.json"
        self.model_config_path = self.artifact_dir / "config.json"
        self._validate_model_assets()
        self.metadata = self._load_json(self.metadata_path)
        self.preprocessor_config = self._load_json(self.preprocessor_path)
        model_config = self._load_json(self.model_config_path)
        id2label = model_config.get("id2label", {})
        self.classes = {int(label_id): label for label_id, label in id2label.items()}
        self.image_size = int(self.metadata.get("image_size", model_settings.MODEL_IMAGE_SIZE))
        self.score_threshold = float(
            self.metadata.get("score_threshold", model_settings.MODEL_SCORE_THRESHOLD)
        )
        self.target_labels = set(
            self.metadata.get("target_labels", ["person", "cell phone"])
        )
        self.image_mean = np.asarray(
            self.preprocessor_config.get("image_mean", [0.485, 0.456, 0.406]),
            dtype=np.float32,
        ).reshape(1, 1, 3)
        self.image_std = np.asarray(
            self.preprocessor_config.get("image_std", [0.229, 0.224, 0.225]),
            dtype=np.float32,
        ).reshape(1, 1, 3)
        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _validate_model_assets(self) -> None:
        required_files = [
            self.model_path,
            self.model_config_path,
            self.preprocessor_path,
            self.metadata_path,
        ]
        missing_files = [path for path in required_files if not path.exists()]
        if missing_files:
            missing_list = ", ".join(str(path) for path in missing_files)
            raise FileNotFoundError(
                "Missing prepared model artifact bundle. "
                "Run the model builder before starting runtime services: "
                f"{missing_list}"
            )

    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        resized_image = image.resize((self.image_size, self.image_size))
        pixel_values = np.asarray(resized_image, dtype=np.float32) / 255.0
        pixel_values = (pixel_values - self.image_mean) / self.image_std
        pixel_values = np.transpose(pixel_values, (2, 0, 1))
        return np.expand_dims(pixel_values, axis=0).astype(np.float32)

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        logits = logits - np.max(logits, axis=-1, keepdims=True)
        exp_logits = np.exp(logits)
        return exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

    @staticmethod
    def _boxes_to_xyxy(boxes: np.ndarray, img_w: int, img_h: int) -> np.ndarray:
        cx, cy, width, height = np.split(boxes, 4, axis=-1)
        x1 = (cx - (width / 2.0)) * img_w
        y1 = (cy - (height / 2.0)) * img_h
        x2 = (cx + (width / 2.0)) * img_w
        y2 = (cy + (height / 2.0)) * img_h
        return np.concatenate([x1, y1, x2, y2], axis=-1)

    def detect_frame(
        self,
        frame_path: Path,
        document_id: str,
        frame_index: int,
        timestamp_seconds: float,
    ) -> dict[str, Any]:
        image = Image.open(frame_path).convert("RGB")
        img_w, img_h = image.size
        image_tensor = self._preprocess_image(image)
        input_name = self.session.get_inputs()[0].name
        logits, pred_boxes = self.session.run(None, {input_name: image_tensor})

        probabilities = self._softmax(logits)[0, :, :-1]
        scores = probabilities.max(axis=-1)
        label_ids = probabilities.argmax(axis=-1)
        boxes = self._boxes_to_xyxy(pred_boxes[0], img_w, img_h)

        detections = []
        draw = ImageDraw.Draw(image)

        for score, label_id, box in zip(scores, label_ids, boxes):
            label = self.classes.get(int(label_id), "unknown")
            if label not in self.target_labels or float(score) < self.score_threshold:
                continue

            x1, y1, x2, y2 = [float(value) for value in box.tolist()]
            x1_i = max(0, min(int(round(x1)), img_w - 1))
            y1_i = max(0, min(int(round(y1)), img_h - 1))
            x2_i = max(x1_i + 1, min(int(round(x2)), img_w))
            y2_i = max(y1_i + 1, min(int(round(y2)), img_h))

            draw.rectangle((x1_i, y1_i, x2_i, y2_i), outline="#0f766e", width=4)
            draw.text((x1_i + 6, y1_i + 6), f"{label} {float(score):.2f}", fill="#0f172a")

            detections.append(
                {
                    "label": label,
                    "confidence": round(float(score), 4),
                    "bbox": [
                        round(x1, 2),
                        round(y1, 2),
                        round(x2, 2),
                        round(y2, 2),
                    ],
                }
            )

        safe_stem = SAFE_LABEL_PATTERN.sub("_", frame_path.stem).strip("._-") or "frame"
        annotated_dir = Path("shared") / "frames" / document_id
        annotated_dir.mkdir(parents=True, exist_ok=True)
        annotated_filename = f"{frame_index:04d}_{safe_stem}.jpg"
        annotated_path = annotated_dir / annotated_filename
        image.save(annotated_path, format="JPEG", quality=90)

        return {
            "frame_index": frame_index,
            "timestamp_seconds": round(timestamp_seconds, 2),
            "image_path": annotated_path.as_posix(),
            "image_url": f"/files/frames/{document_id}/{annotated_filename}",
            "detections_count": len(detections),
            "detections": detections,
        }


_detector: ObjectDetector | None = None


def get_detector() -> ObjectDetector:
    global _detector
    if _detector is None:
        _detector = ObjectDetector()
    return _detector
