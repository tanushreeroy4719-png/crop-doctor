<<<<<<< HEAD
# Crop Doctor

An AI-assisted crop disease diagnosis web app: upload a leaf photo, answer a
short questionnaire about growing conditions, and get an instant prediction
plus a plain-language AI Agronomist treatment report.

Built with Flask, a MobileNetV2 transfer-learning classifier (TensorFlow/Keras),
and Claude for report generation (with an automatic rule-based fallback so it
always works, even with no API key).

## Features

- Drag-and-drop image upload with live preview and sample images to try
- Disease/health prediction with a confidence score
- Symptom, environment, treatment-history, and pest questionnaire
- AI-generated treatment & prevention report (Claude API, or rule-based fallback)
- Diagnosis history log
- Home / History / User Guide / Tools / Privacy / Terms / Disclaimer pages
- Dark/light theme toggle
- **Demo mode**: works end-to-end with zero setup even before you've trained
  a model — predictions are clearly flagged as demo output until you train
  on your own dataset

## 1. Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Run it immediately in demo mode:

```bash
python app.py
```

Open http://localhost:5000 — upload a photo (or click a sample tile) and
you'll see the full flow, including an AI Agronomist report, even before
any model is trained. Every demo prediction is labeled "demo mode" in the UI
so it's never mistaken for a real diagnosis.

## 2. Train on your dataset

You said you have a labeled image dataset — organize it like this
(standard PlantVillage layout, one subfolder per class):

```
data/
  train/
    Apple___Apple_scab/
      img001.jpg
      ...
    Apple___healthy/
      ...
    Tomato___Late_blight/
      ...
  val/
    Apple___Apple_scab/
      ...
    ...
```

Class folder names should match the keys in `data/disease_info.json` (38
classes are already defined there, covering Apple, Blueberry, Cherry, Corn,
Grape, Orange, Peach, Bell Pepper, Potato, Raspberry, Soybean, Squash,
Strawberry, and Tomato) so the app can attach treatment/prevention info to
whatever the model predicts. If your dataset uses different class names,
add matching entries to that file.

Then train:

```bash
python train_model.py --epochs 10 --fine-tune-epochs 5
```

This does two-phase transfer learning on MobileNetV2 (frozen backbone, then
a short fine-tune of the top layers) and saves:

- `model/crop_doctor_model.keras`
- `model/class_indices.json`

Restart the app — it will automatically detect the trained model and switch
out of demo mode.

## 3. Turn on AI-generated reports (optional but recommended)

Set `ANTHROPIC_API_KEY` in `.env`. With no key set, reports are generated
from `data/disease_info.json` and your questionnaire answers using a
rule-based template — fully functional, just less tailored than an LLM
write-up.

## 4. Deploy

This app is deployment-target agnostic; it ships with what most platforms
(Render, Heroku, Railway, Fly.io) expect out of the box:

- `Procfile` — `web: gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
- `runtime.txt` — pinned Python version
- `requirements.txt` — pinned dependencies

Steps common to most platforms:

1. Push this repo to GitHub.
2. Create a new web service pointing at the repo.
3. Set environment variables from `.env.example` (at minimum `FLASK_SECRET_KEY`;
   add `ANTHROPIC_API_KEY` if you want AI-generated reports).
4. Build command: `pip install -r requirements.txt`. Start command: use the
   `Procfile` command above (some platforms auto-detect it).
5. **Model file size**: `crop_doctor_model.keras` can be tens of MB. If your
   platform has a repo size limit, use Git LFS or host the model file
   externally and download it at boot instead of committing it directly.

Note: `tensorflow-cpu` is a sizable dependency (~200MB+). If your host has a
slim-image or size limit, consider `tensorflow-cpu` alternatives like
`tflite-runtime` with a converted `.tflite` model for a much smaller footprint
— ask if you'd like that variant.

## Project structure

```
app.py                  Flask routes
config.py                App configuration
train_model.py            Model training script
utils/model_utils.py     Model loading + inference (with demo-mode fallback)
utils/report_generator.py AI report generation (Claude API + rule-based fallback)
data/disease_info.json   Knowledge base for all 38 classes
templates/               Jinja2 HTML templates
static/css/style.css     Styles
static/js/main.js        Upload/predict/report client logic
model/                   Trained model + class index land here after training
uploads/                 User-uploaded images (served back for preview/history)
```

## Known limitations

- Demo mode predictions are deterministic-but-fake — train a real model
  before relying on this for actual crop decisions.
- History is stored in a local JSON file, fine for a single instance/demo;
  swap in a real database before scaling to multiple users or dynos.
- This is a diagnostic aid, not a substitute for a professional agronomist —
  the Disclaimer page in the app says so too.
=======
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
>>>>>>> 3e0eea10511e0369da3bf0614ee4e4fb6d8e9e0d
