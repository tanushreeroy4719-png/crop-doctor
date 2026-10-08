"""
AgriSmart AI - required predict interface (Section 4.1 of the problem
statement).

Exposes:
    predict(image_path: str) -> str          # class label only
    predict_proba(image_path: str) -> dict    # label + confidence + precaution

CLI:
    python model/predict.py --image path/to/leaf.jpg
    python model/predict.py --image path/to/leaf.jpg --weights model/weights.pt

Loads trained weights and runs on a single new image with no manual steps,
as required by the submission contract.
"""
import argparse
import json
import sys
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from model.labels import IDX_TO_CLASS, precaution_for  # noqa: E402
from model.train import build_model, IMG_SIZE, IMAGENET_MEAN, IMAGENET_STD  # noqa: E402

_DEFAULT_WEIGHTS = Path(__file__).resolve().parent / "weights.pt"

_transform = transforms.Compose([
    transforms.Resize(int(IMG_SIZE * 1.14)),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
])

_model_cache = {}


def _load_model(weights_path: Path, device: str = "cpu"):
    key = str(weights_path)
    if key in _model_cache:
        return _model_cache[key]

    if not weights_path.exists():
        raise FileNotFoundError(
            f"No trained weights found at {weights_path}. Run model/train.py first, "
            "or pass --weights pointing at a trained checkpoint."
        )
    ckpt = torch.load(weights_path, map_location=device)
    class_names = ckpt["class_names"]
    model = build_model(len(class_names), pretrained=False)
    model.load_state_dict(ckpt["model_state"])
    model.eval()
    model.to(device)
    _model_cache[key] = (model, class_names)
    return model, class_names


def predict_proba(image_path: str, weights_path: str = None, device: str = "cpu") -> dict:
    """Runs inference on a single image. Returns label, confidence, precaution."""
    weights_path = Path(weights_path) if weights_path else _DEFAULT_WEIGHTS
    model, class_names = _load_model(weights_path, device)

    img = Image.open(image_path).convert("RGB")
    x = _transform(img).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)[0]
        conf, idx = torch.max(probs, dim=0)

    label = class_names[idx.item()]
    return {
        "class": label,
        "confidence": round(conf.item(), 4),
        "precaution": precaution_for(label),
        "top5": sorted(
            [{"class": class_names[i], "confidence": round(p.item(), 4)}
             for i, p in enumerate(probs)],
            key=lambda d: -d["confidence"],
        )[:5],
    }


def predict(image_path: str, weights_path: str = None) -> str:
    """Minimal required interface: returns just the class label string."""
    return predict_proba(image_path, weights_path)["class"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="Path to a single leaf/crop image")
    ap.add_argument("--weights", default=str(_DEFAULT_WEIGHTS))
    args = ap.parse_args()

    result = predict_proba(args.image, args.weights)
    print(json.dumps(result, indent=2))
    print(f"\nPredicted: {result['class']}  (confidence {result['confidence']:.2%})")
    print(f"Precaution: {result['precaution']}")


if __name__ == "__main__":
    main()
