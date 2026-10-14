import os
import json
import uuid
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename

from config import Config
from utils.model_utils import predict, model_is_trained
from utils.report_generator import generate_report, DISEASE_INFO

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(Config.HISTORY_PATH), exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def _load_history():
    if not os.path.exists(Config.HISTORY_PATH):
        return []
    with open(Config.HISTORY_PATH) as f:
        return json.load(f)


def _save_history(entries):
    with open(Config.HISTORY_PATH, "w") as f:
        json.dump(entries, f, indent=2)


def _append_history(entry):
    entries = _load_history()
    entries.insert(0, entry)
    _save_history(entries[:200])  # keep it bounded
    return entry


def _update_history(entry_id, updates):
    entries = _load_history()
    for entry in entries:
        if entry.get("id") == entry_id:
            entry.update(updates)
            _save_history(entries)
            return entry
    return None


# ---------- Page routes ----------

@app.route("/")
def index():
    return render_template("index.html", model_trained=model_is_trained())


@app.route("/history_page")
def history_page():
    entries = _load_history()
    return render_template("history.html", entries=entries)


@app.route("/user_guide")
def user_guide():
    return render_template("user_guide.html")


@app.route("/tools")
def tools():
    return render_template("tools.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/disclaimer")
def disclaimer():
    return render_template("disclaimer.html")


# ---------- API routes ----------

@app.route("/api/predict", methods=["POST"])
def api_predict():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use JPG, PNG, or WEBP."}), 400

    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    save_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    file.save(save_path)

    try:
        disease_key, confidence, demo_mode = predict(save_path)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {e}"}), 500

    info = DISEASE_INFO.get(disease_key, {})
    image_url = url_for("uploaded_file", filename=filename)
    confidence_pct = round(confidence * 100, 1)

    # Log every analyzed leaf to history right away, even if the person
    # never requests the full AI Agronomist report.
    history_entry = _append_history({
        "id": uuid.uuid4().hex,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "crop": info.get("crop", "Unknown"),
        "condition": info.get("condition", disease_key),
        "confidence": confidence_pct,
        "image_url": image_url,
        "demo_mode": demo_mode,
        "report_excerpt": None,
        "used_ai": None,
    })

    result = {
        "disease_key": disease_key,
        "crop": info.get("crop", "Unknown"),
        "condition": info.get("condition", disease_key),
        "healthy": info.get("healthy", False),
        "confidence": confidence_pct,
        "demo_mode": demo_mode,
        "image_url": image_url,
        "image_filename": filename,
        "history_id": history_entry["id"],
    }
    return jsonify(result)


@app.route("/api/report", methods=["POST"])
def api_report():
    data = request.get_json(force=True, silent=True) or {}
    disease_key = data.get("disease_key")
    confidence = data.get("confidence", 0) / 100.0
    image_url = data.get("image_url", "")
    history_id = data.get("history_id")
    answers = data.get("answers", {})

    if not disease_key:
        return jsonify({"error": "Missing disease_key."}), 400

    try:
        report_md, used_ai = generate_report(disease_key, confidence, answers)
    except Exception as e:
        return jsonify({"error": f"Report generation failed: {e}"}), 500

    info = DISEASE_INFO.get(disease_key, {})
    updates = {
        "crop": info.get("crop", "Unknown"),
        "condition": info.get("condition", disease_key),
        "confidence": round(confidence * 100, 1),
        "report_excerpt": report_md[:180],
        "used_ai": used_ai,
    }

    # The image was already logged to history at analysis time (see
    # /api/predict); fill in the report details on that same entry instead
    # of creating a duplicate row. Fall back to a fresh entry if the
    # original history_id wasn't passed or can't be found.
    updated = _update_history(history_id, updates) if history_id else None
    if not updated:
        updates.update({
            "id": uuid.uuid4().hex,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "image_url": image_url,
        })
        _append_history(updates)

    return jsonify({"report_markdown": report_md, "used_ai": used_ai})


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(Config.UPLOAD_FOLDER, filename)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Image too large. Max size is a few MB."}), 413


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
