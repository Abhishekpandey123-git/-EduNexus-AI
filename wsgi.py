import os
import sys
import traceback

# --- 1. Path Configuration ---
# Get the absolute path of the directory containing wsgi.py
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# Add the project root to sys.path so 'app' can be imported correctly
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- 2. Application Import ---
try:
    # We import 'app' from app/main.py
    from app.main import app as application
    print("🚀 WSGI: Successfully imported FLCS Assistant app.")
    
except Exception as e:
    # This block captures errors like missing .env keys or syntax errors in other files
    print("❌ WSGI CRITICAL ERROR: Could not load the application.")
    traceback.print_exc()
    
    # Fallback app to display the error in the browser for easier debugging
    from flask import Flask
    application = Flask(__name__)
    
    @application.route('/')
    def fallback():
        return f"""
        <div style="font-family: sans-serif; padding: 20px; border: 2px solid red; border-radius: 10px;">
            <h1 style="color: red;">Failed to load FLCS Assistant</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <p>Check your <code>.env</code> file and folder structure.</p>
        </div>
        """, 500

# --- 3. Local Development Runner ---
if __name__ == "__main__":
    # This only runs if you execute 'python wsgi.py' directly.
    # In production, Gunicorn will ignore this and use the 'application' variable above.
    application.run(host="0.0.0.0", port=5000, debug=True)