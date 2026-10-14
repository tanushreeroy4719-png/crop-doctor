"""
AgriSmart AI - Core Task training script.

Trains a transfer-learning image classifier (MobileNetV2 backbone, ImageNet
pretrained) on the lab-condition training set (PlantVillage-style folders),
validates on a held-out split of the SAME source, and reports Macro-F1 +
confusion matrix.

IMPORTANT (per problem statement Section 4.1): NEVER train on the field-
condition held-out test set. This script only ever reads from --train-dir /
--val-dir. Evaluation against the organizers' field test set happens only
through predict.py's predict() function, using the weights this script saves.

Usage:
    python model/train.py \
        --train-dir data/train \
        --val-dir data/val \
        --epochs 10 \
        --out model/weights.pt

Expected folder layout (ImageFolder style):
    data/train/<ClassName>/<image>.jpg
    data/val/<ClassName>/<image>.jpg
Class folder names must match model/labels.py CLASS_NAMES exactly.
"""
import argparse
import json
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from sklearn.metrics import f1_score, confusion_matrix, classification_report

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from model.labels import CLASS_NAMES, CLASS_TO_IDX  # noqa: E402

IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_transforms(train: bool):
    if train:
        return transforms.Compose([
            transforms.RandomResizedCrop(IMG_SIZE, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(0.15, 0.15, 0.15),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])
    return transforms.Compose([
        transforms.Resize(int(IMG_SIZE * 1.14)),
        transforms.CenterCrop(IMG_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def build_model(num_classes: int, pretrained: bool = True) -> nn.Module:
    """MobileNetV2 backbone, new classifier head.

    pretrained=True (default, used for training) downloads ImageNet
    weights for transfer learning. Falls back to random init if the
    download fails (e.g. no internet access in a sandboxed environment) --
    real training runs must have internet access so transfer learning
    actually applies; this fallback exists only so the pipeline can be
    smoke-tested offline.

    pretrained=False (used by predict.py) skips the download entirely,
    since inference immediately overwrites the weights with a trained
    checkpoint anyway.
    """
    if pretrained:
        try:
            net = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
        except Exception as e:
            print(f"[warn] Could not download ImageNet-pretrained weights ({e}). "
                  f"Falling back to randomly-initialized MobileNetV2. "
                  f"Real training runs must have internet access so transfer "
                  f"learning actually applies.")
            net = models.mobilenet_v2(weights=None)
    else:
        net = models.mobilenet_v2(weights=None)
    in_features = net.classifier[-1].in_features
    net.classifier[-1] = nn.Linear(in_features, num_classes)
    return net


def align_class_indices(dataset: datasets.ImageFolder):
    """
    torchvision's ImageFolder assigns indices alphabetically from whatever
    folders exist on disk. We remap to the canonical CLASS_TO_IDX from
    labels.py so saved weights always agree with predict.py, even if a
    class folder is missing locally (e.g. partial local test data).
    """
    missing = [c for c in dataset.classes if c not in CLASS_TO_IDX]
    if missing:
        raise ValueError(
            f"Found class folder(s) not in model/labels.py CLASS_NAMES: {missing}. "
            "Update labels.py to match the organizers' published class list."
        )
    remap = {dataset.class_to_idx[name]: CLASS_TO_IDX[name] for name in dataset.classes}
    dataset.targets = [remap[t] for t in dataset.targets]
    dataset.samples = [(p, remap[t]) for p, t in dataset.samples]
    return dataset


def evaluate(model, loader, device):
    model.eval()
    y_true, y_pred = [], []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            logits = model(x)
            preds = logits.argmax(dim=1).cpu().tolist()
            y_pred.extend(preds)
            y_true.extend(y.tolist())
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(CLASS_NAMES))))
    report = classification_report(
        y_true, y_pred, labels=list(range(len(CLASS_NAMES))),
        target_names=CLASS_NAMES, zero_division=0, output_dict=True,
    )
    return macro_f1, cm, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-dir", default="data/train")
    ap.add_argument("--val-dir", default="data/val")
    ap.add_argument("--epochs", type=int, default=10)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--freeze-backbone", action="store_true",
                     help="Freeze pretrained backbone, train classifier head only (fast).")
    ap.add_argument("--out", default="model/weights.pt")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--num-workers", type=int, default=0,
                     help="DataLoader worker processes. 0 is safest on Colab/low-core "
                          "machines; raise to 2-4 on a multi-core machine with a real dataset.")
    args = ap.parse_args()

    device = torch.device(args.device)
    print(f"Using device: {device}")

    train_ds = datasets.ImageFolder(args.train_dir, transform=build_transforms(train=True))
    val_ds = datasets.ImageFolder(args.val_dir, transform=build_transforms(train=False))
    align_class_indices(train_ds)
    align_class_indices(val_ds)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers)

    model = build_model(len(CLASS_NAMES)).to(device)

    if args.freeze_backbone:
        for p in model.features.parameters():
            p.requires_grad = False

    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=args.lr
    )
    criterion = nn.CrossEntropyLoss()

    best_f1 = -1.0
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * x.size(0)
        train_loss = running_loss / len(train_ds)

        val_f1, cm, report = evaluate(model, val_loader, device)
        print(f"Epoch {epoch}/{args.epochs}  train_loss={train_loss:.4f}  val_macro_f1={val_f1:.4f}")

        if val_f1 > best_f1:
            best_f1 = val_f1
            torch.save({
                "model_state": model.state_dict(),
                "class_names": CLASS_NAMES,
                "img_size": IMG_SIZE,
                "val_macro_f1": val_f1,
            }, args.out)
            with open(Path(args.out).with_suffix(".metrics.json"), "w") as f:
                json.dump({
                    "val_macro_f1": val_f1,
                    "confusion_matrix": cm.tolist(),
                    "classification_report": report,
                }, f, indent=2)
            print(f"  -> new best model saved to {args.out}")

    print(f"Training complete. Best val macro-F1: {best_f1:.4f}")


if __name__ == "__main__":
    main()
