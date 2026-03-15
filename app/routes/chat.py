from flask import Blueprint, request, jsonify, session
from app.chatbot.core import process_message
import os

# --- 1. Blueprint Configuration ---
chat_bp = Blueprint("chat", __name__)

# This token must match the one in your HTML widget's JavaScript
AUTH_TOKEN = os.getenv("CHAT_API_KEY", "flcs_sk_a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")

@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    Main messaging endpoint. 
    Receives user query, validates auth, and returns AI/Logic response.
    """
    
    # --- 2. Authorization Check ---
    auth_header = request.headers.get("Authorization")
    
    # Check if the header exists and matches the Bearer token format
    if not auth_header or auth_header != f"Bearer {AUTH_TOKEN}":
        return jsonify({
            "markdown": "⚠️ **Unauthorized Access.** Please check your API configuration.",
            "buttons": []
        }), 401

    try:
        # --- 3. Extract Request Data ---
        data = request.get_json(silent=True) or {}
        user_query = (data.get("query") or "").strip()
        
        if not user_query:
            return jsonify({
                "markdown": "How can I help you today?",
                "buttons": ["Check Eligibility 🎓", "Services"]
            }), 400

        # --- 4. Process Message ---
        # We pass the 'session' object to 'process_message'.
        # This allows the bot to remember if you are in the middle of the 
        # University Eligibility form without needing a database.
        response_data = process_message(user_query, session)

        # --- 5. Return Response ---
        # Ensures the response always contains 'markdown' and 'buttons' 
        # to prevent frontend errors.
        return jsonify({
            "markdown": response_data.get("markdown", "I'm sorry, I'm having trouble processing that."),
            "buttons": response_data.get("buttons", [])
        }), 200

    except Exception as e:
        # Log the error on the server for debugging
        print(f"Server Error in /chat: {e}")
        return jsonify({
            "markdown": "⚠️ **Service Interruption.** My brain is currently undergoing maintenance. Please try again in a moment.",
            "buttons": ["Main Menu"]
        }), 500