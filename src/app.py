"""
AgriSmart AI - farmer-facing web interface.

Run:
    python src/app.py
Then open http://localhost:5000, drop in a leaf photo, and see the
diagnosis, confidence score, and treatment advice.
"""
import os
import sys
import tempfile
from pathlib import Path

from flask import Flask, request, render_template, jsonify

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from model.predict import predict_proba  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
app = Flask(
    __name__,
    template_folder=str(ROOT / "templates"),
    static_folder=str(ROOT / "static"),
)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict_endpoint():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "Please choose an image."}), 400

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXT:
        return jsonify({"error": "Please upload a JPG, PNG, or WEBP image."}), 400

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    os.close(tmp_fd)
    try:
        file.save(tmp_path)
        try:
            result = predict_proba(tmp_path)
            return jsonify(result)
        except FileNotFoundError as e:
            return jsonify({"error": str(e)}), 500
        except Exception:
            return jsonify({"error": "Could not read that image. Please upload a valid leaf photo."}), 400
    finally:
        os.remove(tmp_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
