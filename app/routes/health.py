from flask import Blueprint, jsonify
from app.chatbot.core import get_status

# Define the blueprint
health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health():
    """
    Checks the connectivity status of all AI services.
    This endpoint is used for monitoring the bot's health.
    """
    try:
        # Calls the status checker we wrote in core.py
        is_healthy, issues = get_status()
        
        if is_healthy:
            return jsonify({
                "status": "healthy",
                "message": "All systems operational (Groq, Pinecone, Cohere).",
                "issues": []
            }), 200
        else:
            return jsonify({
                "status": "degraded",
                "message": "One or more AI services are disconnected.",
                "issues": issues
            }), 503  # 503 Service Unavailable
            
    except Exception as e:
        # Fallback if the health check itself fails
        return jsonify({
            "status": "critical_error",
            "message": str(e)
        }), 500