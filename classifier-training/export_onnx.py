"""
ONNX Export Script — convert the trained PyTorch model to ONNX for inference.

Usage:
    python export_onnx.py --checkpoint ./output/best_monument_classifier.pth --output ./output/monument_classifier.onnx
"""

import argparse

import torch
import torch.nn as nn
from torchvision import models


def export_to_onnx(checkpoint_path: str, output_path: str):
    """Export a trained MobileNetV3 checkpoint to ONNX format."""
    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    num_classes = checkpoint["num_classes"]
    classes = checkpoint.get("classes", [])

    print(f"Exporting model with {num_classes} classes: {classes}")

    # Recreate model architecture
    model = models.mobilenet_v3_large(weights=None)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, num_classes),
    )

    # Load weights
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Dummy input
    dummy_input = torch.randn(1, 3, 224, 224)

    # Export
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=13,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"},
        },
    )

    print(f"ONNX model exported to {output_path}")
    print(f"Val accuracy at export: {checkpoint.get('val_acc', 'N/A')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", default="monument_classifier.onnx")
    args = parser.parse_args()
    export_to_onnx(args.checkpoint, args.output)
