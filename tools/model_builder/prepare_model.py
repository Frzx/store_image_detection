import os
import shutil
from pathlib import Path

import torch
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import EntryNotFoundError
from transformers import AutoConfig, AutoImageProcessor, AutoModelForObjectDetection


MODEL_ONNX_PATH = os.getenv("MODEL_ONNX_PATH", "models/detr-resnet-50.onnx")
MODEL_REPO_ID = os.getenv("MODEL_REPO_ID", "facebook/detr-resnet-50")
MODEL_HF_ONNX_FILENAME = os.getenv("MODEL_HF_ONNX_FILENAME", "model.onnx")
MODEL_EXPORT_OPSET = int(os.getenv("MODEL_EXPORT_OPSET", "18"))
MODEL_IMAGE_SIZE = int(os.getenv("MODEL_IMAGE_SIZE", "800"))


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


def main() -> None:
    model_path = Path(MODEL_ONNX_PATH)
    model_dir = model_path.parent
    model_dir.mkdir(parents=True, exist_ok=True)

    required_files = [
        model_path,
        model_dir / "config.json",
        model_dir / "preprocessor_config.json",
    ]
    if all(path.exists() for path in required_files):
        print(f"Model assets already prepared in {model_dir}. Skipping model build.")
        return

    prepare_supporting_files(model_dir)

    if model_path.exists():
        print(f"ONNX model already exists at {model_path}")
        return

    try:
        downloaded_path = hf_hub_download(
            repo_id=MODEL_REPO_ID,
            filename=MODEL_HF_ONNX_FILENAME,
        )
        shutil.copy2(downloaded_path, model_path)
        print(f"Downloaded ONNX model to {model_path}")
        return
    except EntryNotFoundError:
        print("Hosted ONNX model not found. Exporting ONNX locally instead.")

    export_onnx_model(model_path)
    print(f"Exported ONNX model to {model_path}")


if __name__ == "__main__":
    main()
