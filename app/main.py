import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# --- 1. Load Environment ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def create_app():
    """Application Factory to initialize the Flask app."""
    app = Flask(__name__)

    # --- 2. Security Configuration ---
    app.secret_key = os.getenv("FLASK_SECRET", "dev_default_secret_123")

    # --- 3. Enable CORS ---
    CORS(app, supports_credentials=True)

    # --- 4. Register Blueprints ---
    try:
        from app.routes.chat import chat_bp
        from app.routes.health import health_bp
        from app.routes.upload import upload_bp

        app.register_blueprint(chat_bp, url_prefix="/api")
        app.register_blueprint(health_bp, url_prefix="/api")
        app.register_blueprint(upload_bp, url_prefix="/api")

        print("✅ Blueprints registered successfully.")
    except ImportError as e:
        print(f"❌ Error importing blueprints: {e}")

    # --- 5. Frontend & Static Assets ---
    @app.route("/")
    def index():
        return send_from_directory(BASE_DIR, "index.html")

    @app.route("/style.css")
    def styles():
        return send_from_directory(BASE_DIR, "style.css")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
