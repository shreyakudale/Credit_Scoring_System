# ⚙️ Database connection setup (MySQL)
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'database': os.environ.get('DB_NAME', 'credit_scoring'),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASSWORD', ''),
}

def get_db_connection():
    """Get MySQL database connection."""
    return mysql.connector.connect(**DB_CONFIG)

def get_db_cursor():
    """Get database cursor."""
    conn = get_db_connection()
    return conn.cursor(dictionary=True)
