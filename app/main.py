import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# --- 1. Load Environment ---
# This ensures that variables in .env are available via os.getenv
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def create_app():
    """Application Factory to initialize the Flask app."""
    app = Flask(__name__)

    # --- 2. Security Configuration ---
    # Secret key is required for Flask sessions (used in your Eligibility Flow)
    app.secret_key = os.getenv("FLASK_SECRET", "dev_default_secret_123")

    # --- 3. Enable CORS ---
    # Allows your HTML widget (running on a different domain or local file) 
    # to communicate with this API.
    CORS(app, supports_credentials=True)

    # --- 4. Register Blueprints ---
    try:
        from app.routes.chat import chat_bp
        from app.routes.health import health_bp

        # All chat routes will be available at /api/chat
        app.register_blueprint(chat_bp, url_prefix="/api")
        # Health check available at /api/health
        app.register_blueprint(health_bp, url_prefix="/api")
        
        print("✅ Blueprints registered successfully.")
    except ImportError as e:
        print(f"❌ Error importing blueprints: {e}")

    # --- 5. Base Route ---
    @app.route("/")
    def index():
        return {
            "status": "Online",
            "message": "FLCS Bot API is running.",
            "version": "1.0.0"
        }

    return app

# Initialize the app instance
app = create_app()

if __name__ == "__main__":
    # Running locally for development
    app.run(host="0.0.0.0", port=5000, debug=True)