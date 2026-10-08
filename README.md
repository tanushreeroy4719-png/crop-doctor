# AgriSmart AI — Intelligent Agriculture for a Sustainable Future

SIH 2026 [Internal Hackathon] — L. J. Institute of Engineering and Technology [C-433]
Problem Statement 1 — AgriSmart AI

## 1. Modules Built

| Module | Status |
|---|---|
| **Core — Crop Disease Detection (Computer Vision)** | ✅ Built |
| A. Crop Recommendation | ⬜ Not built |
| B. Smart Irrigation | ⬜ Not built |
| C. Weather-Based Intelligence | ⬜ Not built |
| D. Sustainability Score | ⬜ Not built |
| E. Farmer Assistant (GenAI) | ⬜ Not built |
| F. IoT Integration | ⬜ Not built |
| G. Agentic Advisor | ⬜ Not built |

_Update this table as bonus modules are added._

## 2. Setup & Run Instructions

### Install
```bash
pip install -r requirements.txt
```

### Get the data
This repo does **not** ship the real dataset. Place the organizer-provided
data (or PlantVillage for training/val) into:
```
data/train/<ClassName>/*.jpg
data/val/<ClassName>/*.jpg
```
`<ClassName>` folder names must match `model/labels.py` exactly — **replace
the placeholder class list in `model/labels.py` with the organizers'
published list before training**, so class indices match the held-out set.

For a quick, offline smoke test of the whole pipeline (no real data needed):
```bash
python model/make_dummy_data.py --per-class 20
```
This generates synthetic placeholder images only to prove the code runs —
it has no relationship to real crop diseases and yields no meaningful
accuracy.

### Train
```bash
python model/train.py --train-dir data/train --val-dir data/val --epochs 10 --out model/weights.pt
```
Add `--freeze-backbone` for a fast classifier-head-only baseline. Requires
internet access on first run to download ImageNet-pretrained MobileNetV2
weights (falls back to random init if unavailable, with a warning — do not
submit a model trained this way).

### Predict on a single new image (required interface)
```bash
python model/predict.py --image path/to/leaf.jpg
```
Or from Python:
```python
from model.predict import predict
predict("path/to/leaf.jpg")   # -> class label string
```

### Evaluate on a held-out test set (metrics + confusion matrix)
```bash
python model/evaluate.py --test-dir data/test --weights model/weights.pt
```
Writes `report/test_metrics.json` (macro-F1, confusion matrix, per-class
precision/recall) and `report/confusion_matrix.png`.

### Run the farmer-facing web app
```bash
python src/app.py
```
Open `http://localhost:5000`, upload a leaf photo, get a prediction plus
plain-language precaution guidance.

**A judge should be able to go from clone → trained-or-provided weights →
a prediction on a new image in under ~10 minutes**, per the submission
contract.

## 3. Dataset Used & Licence
- **Training/validation:** PlantVillage (lab-condition leaf images).
- **Held-out test (core score):** organizers' field-condition set, evaluated
  only by organizers via `model/predict.py` — never trained on locally.
- _List any additional public datasets added to training here, with
  citation and licence._

## 4. Reported Metrics
See `report/model_report.md` for the full one-page report and
`report/test_metrics.json` / `report/confusion_matrix.png` once trained on
real data.

## 5. Architecture Overview
```
Leaf/crop image
      │
      ▼
Pre-processing (resize, normalize, augment on train)
      │
      ▼
MobileNetV2 backbone (ImageNet-pretrained, transfer learning)
      │
      ▼
Linear classifier head → disease class / healthy
      │
      ▼
predict.py → {class, confidence, precaution}
      │
      ▼
Flask web app → farmer-friendly result
```

### Known Limitations
See "Limitations" in `report/model_report.md` — most notably the deliberate
lab-to-field generalization gap the challenge is designed around.

## 6. Demo Video
_Link here once recorded (3–5 min, shows core prediction on a new image)._

## 7. Repository Structure
```
/README.md
/src/app.py              — minimal farmer-facing web interface
/model/labels.py         — shared class list + precaution text
/model/train.py          — transfer-learning training script (core task)
/model/predict.py        — required predict(image_path) interface + CLI
/model/evaluate.py       — held-out test metrics + confusion matrix
/model/make_dummy_data.py — offline pipeline smoke-test utility only
/report/model_report.md  — required one-page model report
/requirements.txt
```

## 8. Originality Declaration
This code was written for this hackathon window (10–15 September). It uses:
- `torchvision`'s MobileNetV2 architecture and ImageNet-pretrained weights
  (standard transfer-learning backbone, cited above).
- Standard open-source libraries (PyTorch, scikit-learn, Flask, Pillow,
  matplotlib) per `requirements.txt`.
- No third-party notebooks or solutions were copied.

_List any additional references, tutorials consulted, or third-party code
snippets here as they're added._
