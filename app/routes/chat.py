from flask import Blueprint, request, jsonify, session
from app.chatbot.core import process_message
import os

chat_bp = Blueprint("chat", __name__)

AUTH_TOKEN = os.getenv("CHAT_API_KEY", "e292c93fcbd938004b0cf7f4bceaec9fc494defc8b4ef567")


@chat_bp.route("/chat", methods=["POST"])
def chat():
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {AUTH_TOKEN}":
        return jsonify({
            "markdown": "⚠️ **Unauthorized Access.** Please check your API configuration.",
            "buttons": []
        }), 401

    try:
        data = request.get_json(silent=True) or {}
        user_query = (data.get("query") or "").strip()
        mode = data.get("mode", "josaa")
        user_id = data.get("user_id", "student_demo_123")

        if not user_query:
            return jsonify({
                "markdown": "How can I help you today?",
                "buttons": ["Check Eligibility 🎓", "Main Menu"]
            }), 400

        response_data = process_message(user_query, session, mode=mode, user_id=user_id)

        return jsonify({
            "markdown": response_data.get("markdown", "I'm sorry, I'm having trouble processing that."),
            "buttons": response_data.get("buttons", [])
        }), 200

    except Exception as e:
        print(f"Server Error in /chat: {e}")
        return jsonify({
            "markdown": "⚠️ **Service Interruption.** Please try again in a moment.",
            "buttons": ["Main Menu"]
        }), 500
