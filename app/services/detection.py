from pathlib import Path
from typing import Any

import cv2
import numpy as np
import onnxruntime as ort


COCO_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    4: "airplane",
    5: "bus",
    6: "train",
    7: "truck",
    8: "boat",
    9: "traffic light",
    10: "fire hydrant",
    11: "stop sign",
    12: "parking meter",
    13: "bench",
    14: "bird",
    15: "cat",
    16: "dog",
    17: "horse",
    18: "sheep",
    19: "cow",
    20: "elephant",
    21: "bear",
    22: "zebra",
    23: "giraffe",
    24: "backpack",
    25: "umbrella",
    26: "handbag",
    27: "tie",
    28: "suitcase",
    29: "frisbee",
    30: "skis",
    31: "snowboard",
    32: "sports ball",
    33: "kite",
    34: "baseball bat",
    35: "baseball glove",
    36: "skateboard",
    37: "surfboard",
    38: "tennis racket",
    39: "bottle",
    40: "wine glass",
    41: "cup",
    42: "fork",
    43: "knife",
    44: "spoon",
    45: "bowl",
    46: "banana",
    47: "apple",
    48: "sandwich",
    49: "orange",
    50: "broccoli",
    51: "carrot",
    52: "hot dog",
    53: "pizza",
    54: "donut",
    55: "cake",
    56: "chair",
    57: "couch",
    58: "potted plant",
    59: "bed",
    60: "dining table",
    61: "toilet",
    62: "tv",
    63: "laptop",
    64: "mouse",
    65: "remote",
    66: "keyboard",
    67: "cell phone",
    68: "microwave",
    69: "oven",
    70: "toaster",
    71: "sink",
    72: "refrigerator",
    73: "book",
    74: "clock",
    75: "vase",
    76: "scissors",
    77: "teddy bear",
    78: "hair drier",
    79: "toothbrush",
}


def preprocess_image(image: np.ndarray, size: tuple[int, int] = (640, 640)) -> np.ndarray:
    image = cv2.resize(image, size)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.transpose(2, 0, 1)
    image = image.reshape(1, 3, size[0], size[1])
    return image.astype(np.float32) / 255.0


def normalize_output(output: np.ndarray) -> np.ndarray:
    output = np.squeeze(output)

    if output.shape[0] < output.shape[1]:
        output = output.T

    return output


def filter_detections(results: np.ndarray, conf_threshold: float = 0.25) -> np.ndarray:
    processed = []

    for det in results:
        # YOLO format: cx, cy, w, h, class scores...
        class_scores = det[4:]

        if len(class_scores) == 1:
            class_id = 0
            confidence = float(class_scores[0])
        else:
            class_id = int(np.argmax(class_scores))
            confidence = float(np.max(class_scores))

        if confidence >= conf_threshold:
            processed.append([det[0], det[1], det[2], det[3], class_id, confidence])

    return np.array(processed)


def nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.55):
    if len(boxes) == 0:
        return [], []

    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
    order = scores.argsort()

    keep = []
    keep_scores = []

    while len(order) > 0:
        idx = order[-1]
        keep.append(boxes[idx])
        keep_scores.append(scores[idx])

        order = order[:-1]
        if len(order) == 0:
            break

        xx1 = np.maximum(x1[idx], x1[order])
        yy1 = np.maximum(y1[idx], y1[order])
        xx2 = np.minimum(x2[idx], x2[order])
        yy2 = np.minimum(y2[idx], y2[order])

        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)

        intersection = w * h
        union = areas[idx] + areas[order] - intersection
        iou = intersection / np.maximum(union, 1e-6)

        order = order[iou < iou_threshold]

    return keep, keep_scores


def rescale_back(results: np.ndarray, img_w: int, img_h: int):
    if len(results) == 0:
        return [], []

    cx = results[:, 0] / 640.0 * img_w
    cy = results[:, 1] / 640.0 * img_h
    w = results[:, 2] / 640.0 * img_w
    h = results[:, 3] / 640.0 * img_h
    class_id = results[:, 4]
    confidence = results[:, 5]

    x1 = cx - w / 2
    y1 = cy - h / 2
    x2 = cx + w / 2
    y2 = cy + h / 2

    boxes = np.column_stack((x1, y1, x2, y2, class_id))
    return nms(boxes, confidence)


class ObjectDetector:
    def __init__(self, model_path: str = "models/yolo11l.onnx"):
        self.model_path = model_path
        self.session = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
        )
        self.classes = COCO_CLASSES

    def predict(self, image_path: str) -> dict[str, Any]:
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        img_h, img_w = image.shape[:2]

        image_tensor = preprocess_image(image)
        input_name = self.session.get_inputs()[0].name
        outputs = self.session.run(None, {input_name: image_tensor})

        results = normalize_output(outputs[0])
        results = filter_detections(results)
        boxes, scores = rescale_back(results, img_w, img_h)

        detections = []

        for box, score in zip(boxes, scores):
            x1, y1, x2, y2, class_id = box

            detections.append({
                "class": self.classes.get(int(class_id), "unknown"),
                "confidence": round(float(score), 4),
                "bbox": [
                    round(float(x1), 2),
                    round(float(y1), 2),
                    round(float(x2), 2),
                    round(float(y2), 2),
                ],
            })

        return {
            "filename": Path(image_path).name,
            "status": "success",
            "detections": detections,
            "metadata": {
                "model": self.model_path,
                "runtime": "onnxruntime",
                "provider": "CPUExecutionProvider",
            },
        }


detector = ObjectDetector()
