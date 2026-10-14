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
