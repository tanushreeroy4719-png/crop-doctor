"""
Evaluate a trained model on a held-out test folder and write the report
artifacts required by Section 7.3 (macro-F1, confusion matrix, per-class
precision/recall).

Usage:
    python model/evaluate.py --test-dir data/test --weights model/weights.pt \
        --out report/test_metrics.json --cm-png report/confusion_matrix.png
"""
import argparse
import json
import sys
from pathlib import Path

import torch
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from torch.utils.data import DataLoader
from torchvision import datasets

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from model.labels import CLASS_NAMES  # noqa: E402
from model.train import align_class_indices, evaluate, build_model, build_transforms  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-dir", required=True)
    ap.add_argument("--weights", default="model/weights.pt")
    ap.add_argument("--out", default="report/test_metrics.json")
    ap.add_argument("--cm-png", default="report/confusion_matrix.png")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--num-workers", type=int, default=0,
                     help="DataLoader worker processes. 0 is safest on Colab/low-core machines.")
    args = ap.parse_args()

    device = torch.device(args.device)
    ckpt = torch.load(args.weights, map_location=device)
    model = build_model(len(CLASS_NAMES), pretrained=False)
    model.load_state_dict(ckpt["model_state"])
    model.to(device)

    test_ds = datasets.ImageFolder(args.test_dir, transform=build_transforms(train=False))
    align_class_indices(test_ds)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=args.num_workers)

    macro_f1, cm, report = evaluate(model, test_loader, device)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        json.dump({
            "macro_f1": macro_f1,
            "confusion_matrix": cm.tolist(),
            "class_names": CLASS_NAMES,
            "classification_report": report,
        }, f, indent=2)

    fig, ax = plt.subplots(figsize=(9, 8))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(CLASS_NAMES)))
    ax.set_yticks(range(len(CLASS_NAMES)))
    ax.set_xticklabels(CLASS_NAMES, rotation=90, fontsize=6)
    ax.set_yticklabels(CLASS_NAMES, fontsize=6)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion Matrix (Macro-F1 = {macro_f1:.3f})")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(args.cm_png, dpi=150)

    print(f"Macro-F1 on {args.test_dir}: {macro_f1:.4f}")
    print(f"Saved metrics -> {args.out}")
    print(f"Saved confusion matrix -> {args.cm_png}")


if __name__ == "__main__":
    main()
