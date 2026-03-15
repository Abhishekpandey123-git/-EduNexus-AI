from flask import request, jsonify
from werkzeug.utils import secure_filename
from app.chatbot.core import handle_note_upload
import os

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/upload_notes', methods=['POST'])
def api_upload_notes():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    user_id = request.form.get("user_id", "student_demo_123")
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Extract text based on file type
        text = ""
        if filename.endswith('.pdf'):
            from pypdf import PdfReader
            reader = PdfReader(filepath)
            for page in reader.pages:
                text += page.extract_text() or ""
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()

        # Call your existing logic to learn the note
        result_message = handle_note_upload(text, user_id)
        
        # Cleanup: remove the temporary file after learning
        os.remove(filepath)
        
        return jsonify({"message": result_message})