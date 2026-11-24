import os
import sys
import traceback

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from app.main import app as application
    print("🚀 WSGI: Successfully imported EduNexus AI app.")
except Exception as e:
    print("❌ WSGI CRITICAL ERROR: Could not load the application.")
    traceback.print_exc()

    from flask import Flask
    application = Flask(__name__)

    @application.route("/")
    def fallback():
        return f"""
        <div style="font-family: sans-serif; padding: 20px; border: 2px solid red; border-radius: 10px;">
            <h1 style="color: red;">Failed to load EduNexus AI</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Check your <code>.env</code> file and folder structure.</p>
        </div>
        """, 500

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=5000, debug=True)
