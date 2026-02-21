import mysql.connector
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.db_config import DB_CONFIG

def add_missing_columns():
    """Add missing columns to existing tables."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Check if is_primary column exists in accounts table
        cursor.execute("SHOW COLUMNS FROM accounts LIKE 'is_primary'")
        if not cursor.fetchone():
            print("Adding is_primary column to accounts table...")
            cursor.execute("ALTER TABLE accounts ADD COLUMN is_primary BOOLEAN DEFAULT FALSE")
            print("Column added successfully.")
        else:
            print("is_primary column already exists.")

        # Check if bank_name column exists in accounts table
        cursor.execute("SHOW COLUMNS FROM accounts LIKE 'bank_name'")
        if not cursor.fetchone():
            print("Adding bank_name column to accounts table...")
            cursor.execute("ALTER TABLE accounts ADD COLUMN bank_name VARCHAR(100)")
            print("bank_name column added successfully.")
        else:
            print("bank_name column already exists.")

        # Check if ifsc_code column exists in accounts table
        cursor.execute("SHOW COLUMNS FROM accounts LIKE 'ifsc_code'")
        if not cursor.fetchone():
            print("Adding ifsc_code column to accounts table...")
            cursor.execute("ALTER TABLE accounts ADD COLUMN ifsc_code VARCHAR(20)")
            print("ifsc_code column added successfully.")
        else:
            print("ifsc_code column already exists.")

        conn.commit()

    except Exception as e:
        print(f"Error adding column: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_missing_columns()
