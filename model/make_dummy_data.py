"""
DEV/TEST UTILITY ONLY -- NOT PART OF THE SUBMISSION PIPELINE.

Generates a tiny synthetic image dataset (colored shapes) so the full
train -> predict pipeline can be smoke-tested without downloading the real
PlantVillage / field-test datasets. Swap data/train and data/val for the
real, organizer-provided folders before actually training a submission
model -- this dummy data has no relationship to real crop diseases and a
model trained on it has zero real-world accuracy.

Usage:
    python model/make_dummy_data.py --per-class 12
"""
import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from model.labels import CLASS_NAMES  # noqa: E402


def make_image(seed: int, color) -> Image.Image:
    random.seed(seed)
    img = Image.new("RGB", (256, 256), color="white")
    draw = ImageDraw.Draw(img)
    for _ in range(6):
        x0, y0 = random.randint(0, 200), random.randint(0, 200)
        x1, y1 = x0 + random.randint(20, 55), y0 + random.randint(20, 55)
        draw.ellipse([x0, y0, x1, y1], fill=color)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=12)
    ap.add_argument("--out-root", default="data")
    args = ap.parse_args()

    root = Path(args.out_root)
    rng = random.Random(42)

    for split, n in [("train", args.per_class), ("val", max(4, args.per_class // 3))]:
        for ci, cname in enumerate(CLASS_NAMES):
            cdir = root / split / cname
            cdir.mkdir(parents=True, exist_ok=True)
            base_color = (
                (ci * 37) % 256, (ci * 91) % 256, (ci * 53) % 256,
            )
            for i in range(n):
                img = make_image(seed=ci * 1000 + i, color=base_color)
                img.save(cdir / f"{cname}_{i:03d}.jpg", quality=90)

    # A couple of sample images for a manual predict.py smoke test
    sample_dir = root / "test_sample"
    sample_dir.mkdir(parents=True, exist_ok=True)
    for ci in [0, 4, 9]:
        img = make_image(seed=ci * 1000 + 999, color=((ci * 37) % 256, (ci * 91) % 256, (ci * 53) % 256))
        img.save(sample_dir / f"sample_{CLASS_NAMES[ci]}.jpg", quality=90)

    print(f"Dummy dataset written under {root}/train, {root}/val, {root}/test_sample")


if __name__ == "__main__":
    main()
