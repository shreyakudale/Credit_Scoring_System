# 🧠 Main Flask Application (runs the web server)
from flask import Flask, session
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database on startup
from database.db_init import initialize_database
try:
    initialize_database()
    print("Database initialized successfully on app startup.")
except Exception as e:
    print(f"Failed to initialize database on startup: {e}")

# Register blueprints
from routes.main_routes import main_bp
from routes.api_routes import api_bp

app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)
