# Script to initialize or reset database
import mysql.connector
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.db_config import DB_CONFIG

def initialize_database():
    """Initialize the MySQL database with schema and sample data."""
    # Connect to MySQL server (without specifying database to create it if needed)
    config_without_db = DB_CONFIG.copy()
    config_without_db.pop('database', None)

    conn = mysql.connector.connect(**config_without_db)
    cursor = conn.cursor()

    try:
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.commit()

        # Switch to the database
        cursor.execute(f"USE {DB_CONFIG['database']}")

        # Get script directory and file paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(script_dir, 'schema.sql')
        sample_path = os.path.join(script_dir, 'sample_data.sql')

        # Read and execute schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        for statement in statements:
            cursor.execute(statement)

        # Read and execute sample data
        with open(sample_path, 'r', encoding='utf-8') as f:
            sample_sql = f.read()
        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sample_sql.split(';') if stmt.strip()]
        for statement in statements:
            cursor.execute(statement)

        conn.commit()
        print("Database initialized successfully!")

    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

def reset_database():
    """Reset the database by dropping and recreating it."""
    config_without_db = DB_CONFIG.copy()
    config_without_db.pop('database', None)

    conn = mysql.connector.connect(**config_without_db)
    cursor = conn.cursor()

    try:
        # Drop database if exists
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_CONFIG['database']}")
        conn.commit()
        print(f"Database {DB_CONFIG['database']} dropped.")
    except Exception as e:
        print(f"Error dropping database: {e}")
    finally:
        conn.close()

    # Reinitialize
    initialize_database()

if __name__ == "__main__":
    initialize_database()
