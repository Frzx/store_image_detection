import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import EntryNotFoundError
from transformers import AutoConfig, AutoImageProcessor, AutoModelForObjectDetection


MODEL_ARTIFACT_ROOT = Path(os.getenv("MODEL_ARTIFACT_ROOT", "/models"))
MODEL_NAME = os.getenv("MODEL_NAME", "object-detector")
MODEL_VERSION = os.getenv("MODEL_VERSION", "v1")
MODEL_REPO_ID = os.getenv("MODEL_REPO_ID", "facebook/detr-resnet-50")
MODEL_HF_ONNX_FILENAME = os.getenv("MODEL_HF_ONNX_FILENAME", "model.onnx")
MODEL_EXPORT_OPSET = int(os.getenv("MODEL_EXPORT_OPSET", "18"))
MODEL_IMAGE_SIZE = int(os.getenv("MODEL_IMAGE_SIZE", "800"))
MODEL_SCORE_THRESHOLD = float(os.getenv("MODEL_SCORE_THRESHOLD", "0.3"))
MODEL_TARGET_LABELS = [
    label.strip()
    for label in os.getenv("MODEL_TARGET_LABELS", "person,cell phone").split(",")
    if label.strip()
]


def prepare_supporting_files(model_dir: Path) -> None:
    AutoImageProcessor.from_pretrained(MODEL_REPO_ID).save_pretrained(model_dir)
    AutoConfig.from_pretrained(MODEL_REPO_ID).save_pretrained(model_dir)


def export_onnx_model(model_path: Path) -> None:
    model = AutoModelForObjectDetection.from_pretrained(MODEL_REPO_ID)
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
        MODEL_IMAGE_SIZE,
        MODEL_IMAGE_SIZE,
        dtype=torch.float32,
    )

    torch.onnx.export(
        export_model,
        (sample_input,),
        str(model_path),
        input_names=["pixel_values"],
        output_names=["logits", "pred_boxes"],
        opset_version=MODEL_EXPORT_OPSET,
        dynamo=True,
        external_data=False,
    )


def write_metadata(metadata_path: Path) -> None:
    metadata = {
        "model_name": MODEL_NAME,
        "model_version": MODEL_VERSION,
        "repo_id": MODEL_REPO_ID,
        "onnx_filename": "model.onnx",
        "config_filename": "config.json",
        "preprocessor_filename": "preprocessor_config.json",
        "image_size": MODEL_IMAGE_SIZE,
        "score_threshold": MODEL_SCORE_THRESHOLD,
        "target_labels": MODEL_TARGET_LABELS,
        "export_opset": MODEL_EXPORT_OPSET,
        "created_at_utc": datetime.now(UTC).isoformat(),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> None:
    model_dir = MODEL_ARTIFACT_ROOT / MODEL_NAME / MODEL_VERSION
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "model.onnx"
    metadata_path = model_dir / "metadata.json"

    required_files = [
        model_path,
        model_dir / "config.json",
        model_dir / "preprocessor_config.json",
        metadata_path,
    ]
    if all(path.exists() for path in required_files):
        print(f"Model artifacts already prepared in {model_dir}. Skipping model build.")
        return

    prepare_supporting_files(model_dir)

    if not model_path.exists():
        try:
            downloaded_path = hf_hub_download(
                repo_id=MODEL_REPO_ID,
                filename=MODEL_HF_ONNX_FILENAME,
            )
            shutil.copy2(downloaded_path, model_path)
            print(f"Downloaded ONNX model to {model_path}")
        except EntryNotFoundError:
            print("Hosted ONNX model not found. Exporting ONNX locally instead.")
            export_onnx_model(model_path)
            print(f"Exported ONNX model to {model_path}")

    write_metadata(metadata_path)
    print(f"Prepared artifact bundle in {model_dir}")


if __name__ == "__main__":
    main()
