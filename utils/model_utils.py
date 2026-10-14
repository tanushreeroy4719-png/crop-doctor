"""
Loads the trained Keras classifier and runs predictions.

If no trained model file exists yet (e.g. you haven't run train_model.py
against your dataset), the app still runs in "demo mode": predictions are
generated deterministically from the image itself (same image always gives
the same result) and every response is clearly flagged with
`"demo_mode": true` so the front end can show an honest disclaimer instead
of silently pretending to be a trained model.
"""
import os
import json
import hashlib

import numpy as np
from PIL import Image

from config import Config

_model = None
_class_names = None


def _load_class_names():
    global _class_names
    if _class_names is not None:
        return _class_names

    if os.path.exists(Config.CLASS_INDEX_PATH):
        with open(Config.CLASS_INDEX_PATH) as f:
            index_to_class = json.load(f)
        # class_indices.json is saved as {class_name: index}; invert it.
        _class_names = [None] * len(index_to_class)
        for name, idx in index_to_class.items():
            _class_names[int(idx)] = name
    else:
        # Fall back to the disease knowledge base so demo mode still has
        # a full, correctly ordered label set.
        info_path = os.path.join(Config.BASE_DIR, "data", "disease_info.json")
        with open(info_path) as f:
            _class_names = sorted(json.load(f).keys())

    return _class_names


def model_is_trained():
    return os.path.exists(Config.MODEL_PATH)


def _load_model():
    global _model
    if _model is not None:
        return _model
    if not model_is_trained():
        return None

    # Imported lazily so the app can boot (and run in demo mode) even in
    # environments where tensorflow isn't installed yet.
    import tensorflow as tf
    _model = tf.keras.models.load_model(Config.MODEL_PATH)
    return _model


def _preprocess(image_path):
    img = Image.open(image_path).convert("RGB").resize(Config.IMG_SIZE)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def _demo_prediction(image_path, class_names):
    """Deterministic pseudo-classification used only when no trained model
    is present, so the full app flow (upload -> result -> report) can be
    exercised end-to-end before training finishes."""
    with open(image_path, "rb") as f:
        digest = hashlib.sha256(f.read()).digest()
    seed = int.from_bytes(digest[:4], "big")
    rng = np.random.default_rng(seed)

    idx = int(rng.integers(0, len(class_names)))
    # Confidence in a plausible-looking but clearly-not-real range.
    confidence = float(rng.uniform(0.55, 0.93))

    scores = rng.dirichlet(np.ones(len(class_names)) * 0.3)
    scores = scores * (1 - confidence)
    scores[idx] = confidence
    scores = scores / scores.sum()

    return idx, scores


def predict(image_path):
    """Returns (predicted_class_name, confidence_float, demo_mode_bool)."""
    class_names = _load_class_names()
    model = _load_model()

    if model is None:
        idx, scores = _demo_prediction(image_path, class_names)
        return class_names[idx], float(scores[idx]), True

    x = _preprocess(image_path)
    preds = model.predict(x, verbose=0)[0]
    idx = int(np.argmax(preds))
    return class_names[idx], float(preds[idx]), False
