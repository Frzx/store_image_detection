import re
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import onnxruntime as ort
import torch
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import EntryNotFoundError
from PIL import Image, ImageDraw
from transformers import AutoConfig, AutoImageProcessor, AutoModelForObjectDetection

from app.config import model_settings


SAFE_LABEL_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
TARGET_LABELS = {"person", "cell phone"}


class ObjectDetector:
    def __init__(self, model_path: str | None = None):
        self.model_path = Path(model_path or model_settings.MODEL_ONNX_PATH)
        self.repo_id = model_settings.MODEL_REPO_ID
        self.hf_onnx_filename = model_settings.MODEL_HF_ONNX_FILENAME
        self.image_size = model_settings.MODEL_IMAGE_SIZE
        self.score_threshold = model_settings.MODEL_SCORE_THRESHOLD
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_model_exists()
        self.image_processor = AutoImageProcessor.from_pretrained(self.repo_id)
        self.model_config = AutoConfig.from_pretrained(self.repo_id)
        self.classes = getattr(self.model_config, "id2label", {})
        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=["CPUExecutionProvider"],
        )

    def _ensure_model_exists(self) -> None:
        if self.model_path.exists():
            return

        try:
            downloaded_path = hf_hub_download(
                repo_id=self.repo_id,
                filename=self.hf_onnx_filename,
            )
            shutil.copy2(downloaded_path, self.model_path)
            return
        except EntryNotFoundError:
            pass

        model = AutoModelForObjectDetection.from_pretrained(self.repo_id)
        model = model.to("cpu")
        model.eval()

        class ExportWrapper(torch.nn.Module):
            def __init__(self, detection_model):
                super().__init__()
                self.detection_model = detection_model

            def forward(self, pixel_values):
                outputs = self.detection_model(pixel_values=pixel_values)
                return outputs.logits, outputs.pred_boxes

        export_model = ExportWrapper(model)
        export_model.eval()
        sample_input = torch.randn(
            1,
            3,
            self.image_size,
            self.image_size,
            dtype=torch.float32,
        )

        torch.onnx.export(
            export_model,
            (sample_input,),
            str(self.model_path),
            input_names=["pixel_values"],
            output_names=["logits", "pred_boxes"],
            opset_version=model_settings.MODEL_EXPORT_OPSET,
            dynamo=True,
            external_data=False,
        )

    def detect_frame(
        self,
        frame_path: Path,
        document_id: str,
        frame_index: int,
        timestamp_seconds: float,
    ) -> dict[str, Any]:
        image = Image.open(frame_path).convert("RGB")
        img_w, img_h = image.size
        processor_inputs = self.image_processor(
            images=image,
            return_tensors="np",
            do_resize=True,
            size={"height": self.image_size, "width": self.image_size},
        )
        image_tensor = processor_inputs["pixel_values"].astype(np.float32)
        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: image_tensor})
        target_sizes = torch.tensor([[img_h, img_w]])
        post_processed = self.image_processor.post_process_object_detection(
            SimpleNamespace(
                logits=torch.from_numpy(outputs[0]),
                pred_boxes=torch.from_numpy(outputs[1]),
            ),
            threshold=self.score_threshold,
            target_sizes=target_sizes,
        )[0]

        detections = []
        draw = ImageDraw.Draw(image)

        for score, label_id, box in zip(
            post_processed["scores"],
            post_processed["labels"],
            post_processed["boxes"],
        ):
            label = self.classes.get(int(label_id), "unknown")
            if label not in TARGET_LABELS:
                continue

            x1, y1, x2, y2 = [float(value) for value in box.tolist()]
            x1_i = max(0, min(int(round(x1)), img_w - 1))
            y1_i = max(0, min(int(round(y1)), img_h - 1))
            x2_i = max(x1_i + 1, min(int(round(x2)), img_w))
            y2_i = max(y1_i + 1, min(int(round(y2)), img_h))

            draw.rectangle((x1_i, y1_i, x2_i, y2_i), outline="#0f766e", width=4)
            draw.text((x1_i + 6, y1_i + 6), f"{label} {float(score.item()):.2f}", fill="#0f172a")

            detections.append(
                {
                    "label": label,
                    "confidence": round(float(score.item()), 4),
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
