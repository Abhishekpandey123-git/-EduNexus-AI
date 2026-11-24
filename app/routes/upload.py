from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.chatbot.core import handle_note_upload
import os

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@upload_bp.route("/upload_notes", methods=["POST"])
def api_upload_notes():
    if "file" not in request.files:
        return jsonify({"message": "⚠️ No file received."}), 400

    file = request.files["file"]
    user_id = request.form.get("user_id", "student_demo_123")

    if file.filename == "":
        return jsonify({"message": "⚠️ No file selected."}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        text = ""
        if filename.lower().endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            for page in reader.pages:
                text += page.extract_text() or ""
        else:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        result_message = handle_note_upload(text, user_id)
        return jsonify({"message": result_message}), 200
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
