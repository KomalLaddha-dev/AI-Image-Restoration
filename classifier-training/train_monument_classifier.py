"""
Monument Classifier Training Script
====================================
Transfer learning using MobileNetV3-Large pretrained on ImageNet.
Designed to run on Google Colab (free T4 GPU).

Usage:
    python train_monument_classifier.py --data_dir ./dataset --epochs 30 --batch_size 32

Expected dataset structure:
    dataset/
    ├── train/
    │   ├── taj_mahal/
    │   │   ├── img001.jpg
    │   │   └── ...
    │   ├── colosseum/
    │   └── ...
    └── val/
        ├── taj_mahal/
        └── ...
"""

import argparse
import json
import os
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from loguru import logger


def get_transforms():
    """Training and validation transforms with augmentation."""
    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
        transforms.RandomPerspective(distortion_scale=0.2, p=0.3),
        transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    val_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    return train_transform, val_transform


def create_model(num_classes: int, freeze_backbone: bool = True) -> nn.Module:
    """
    Create MobileNetV3-Large with a custom classification head.
    Freezes the backbone for initial fine-tuning.
    """
    model = models.mobilenet_v3_large(weights="IMAGENET1K_V2")

    if freeze_backbone:
        for param in model.features.parameters():
            param.requires_grad = False

    # Replace classifier head
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Sequential(
        nn.Dropout(0.3),
        nn.Linear(in_features, num_classes),
    )

    return model


def train_one_epoch(model, loader, criterion, optimizer, device):
    """Train for one epoch, return average loss and accuracy."""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()

    return total_loss / total, correct / total


def validate(model, loader, criterion, device):
    """Validate model, return average loss and accuracy."""
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()

    return total_loss / total, correct / total


def main():
    parser = argparse.ArgumentParser(description="Train monument classifier")
    parser.add_argument("--data_dir", type=str, default="./dataset")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--unfreeze_epoch", type=int, default=10,
                        help="Epoch at which to unfreeze backbone")
    parser.add_argument("--output_dir", type=str, default="./output")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Data loaders
    train_transform, val_transform = get_transforms()
    train_dataset = datasets.ImageFolder(
        os.path.join(args.data_dir, "train"), transform=train_transform
    )
    val_dataset = datasets.ImageFolder(
        os.path.join(args.data_dir, "val"), transform=val_transform
    )

    num_classes = len(train_dataset.classes)
    logger.info(f"Found {num_classes} classes: {train_dataset.classes}")
    logger.info(f"Train: {len(train_dataset)} images, Val: {len(val_dataset)} images")

    train_loader = DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=4, pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset, batch_size=args.batch_size, shuffle=False,
        num_workers=4, pin_memory=True,
    )

    # Model
    model = create_model(num_classes, freeze_backbone=True).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=args.lr, weight_decay=1e-4,
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # Training loop
    best_val_acc = 0.0
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        # Unfreeze backbone after N epochs
        if epoch == args.unfreeze_epoch:
            logger.info("Unfreezing backbone for fine-tuning")
            for param in model.features.parameters():
                param.requires_grad = True
            optimizer = optim.AdamW(model.parameters(), lr=args.lr * 0.1, weight_decay=1e-4)
            scheduler = optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=args.epochs - epoch
            )

        train_loss, train_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, device
        )
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        scheduler.step()

        logger.info(
            f"Epoch {epoch}/{args.epochs} — "
            f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}"
        )

        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_path = output_dir / "best_monument_classifier.pth"
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_acc": val_acc,
                "num_classes": num_classes,
                "classes": train_dataset.classes,
            }, best_path)
            logger.info(f"New best model saved (val_acc={val_acc:.4f})")

    # Save label mapping
    labels = {str(i): {"id": cls, "name": cls.replace("_", " ").title()}
              for i, cls in enumerate(train_dataset.classes)}
    labels_path = output_dir / "labels.json"
    with open(labels_path, "w") as f:
        json.dump(labels, f, indent=2)

    logger.info(f"Training complete! Best val accuracy: {best_val_acc:.4f}")
    logger.info(f"Model saved to {output_dir / 'best_monument_classifier.pth'}")
    logger.info(f"Labels saved to {labels_path}")


if __name__ == "__main__":
    main()
