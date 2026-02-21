import mysql.connector
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.db_config import DB_CONFIG

def alter_transfer_type_enum():
    """Alter the transfer_type column to include 'MOBILE' in the ENUM."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Alter the transfer_type column to add 'MOBILE'
        cursor.execute('''
            ALTER TABLE transactions
            MODIFY COLUMN transfer_type ENUM('IMPS', 'NEFT', 'RTGS', 'UPI', 'MOBILE') DEFAULT 'IMPS'
        ''')
        conn.commit()
        print("transfer_type ENUM updated successfully to include 'MOBILE'.")
    except Exception as e:
        print(f"Error altering transfer_type column: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    alter_transfer_type_enum()
