import time
import random
from typing import Any

class ObjectDetector:
    def __init__(self, model_path: str = "models/mock_model.pt"):
        self.model_path = model_path
        # In a real app, you'd load your weights here:
        # self.model = yolov8.load(model_path)
        print(f"Successfully loaded model from {self.model_path}")

    def predict(self, image_path: str) -> dict[str, Any]:
        """
        Simulates ML inference on an image.
        """
        print(f"Processing image: {image_path}")
        
        # 1. Simulate "Inference Time" (Heavy CPU/GPU work)
        # Real object detection usually takes 100ms to 2s depending on the model
        time.sleep(2.5) 

        # 2. Generate Mock Detections
        # We'll pretend we found a "person" and a "dog"
        mock_results = {
            "filename": image_path.split("/")[-1],
            "status": "success",
            "detections": [
                {
                    "class": "person",
                    "confidence": round(random.uniform(0.85, 0.98), 2),
                    "bbox": [100, 50, 200, 400] # [x_min, y_min, x_max, y_max]
                },
                {
                    "class": "dog",
                    "confidence": round(random.uniform(0.70, 0.92), 2),
                    "bbox": [300, 200, 450, 350]
                }
            ],
            "metadata": {
                "model": "Mock-YOLO-v8",
                "inference_time_s": 2.5
            }
        }

        return mock_results

# Create a singleton instance to be used across the app
detector = ObjectDetector()