import mysql.connector
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.db_config import DB_CONFIG

def create_transections_table():
    """Create the transections table if it doesn't exist."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Create transections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transections (
                transfer_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                sender_account_id INT,
                receiver_account_id INT,
                beneficiary_id INT NULL,
                amount DECIMAL(15,2) NOT NULL,
                transfer_type ENUM('IMPS', 'NEFT', 'RTGS', 'UPI', 'MOBILE') DEFAULT 'IMPS',
                reference_number VARCHAR(50) UNIQUE,
                status ENUM('Pending', 'Completed', 'Failed', 'Cancelled') DEFAULT 'Pending',
                remarks VARCHAR(255),
                initiated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                FOREIGN KEY (sender_account_id) REFERENCES accounts(account_id),
                FOREIGN KEY (receiver_account_id) REFERENCES accounts(account_id),
                FOREIGN KEY (beneficiary_id) REFERENCES beneficiaries(beneficiary_id)
            )
        ''')
        conn.commit()
        print("Transections table created successfully!")
    except Exception as e:
        print(f"Error creating transections table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_transections_table()
