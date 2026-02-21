import mysql.connector
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.db_config import DB_CONFIG

def fix_transactions_table():
    """Fix the transactions table by adding missing columns and removing beneficiary_id."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Check if counterparty_account_id column exists in transactions table
        cursor.execute("SHOW COLUMNS FROM transactions LIKE 'counterparty_account_id'")
        if not cursor.fetchone():
            print("Adding counterparty_account_id column to transactions table...")
            cursor.execute("ALTER TABLE transactions ADD COLUMN counterparty_account_id INT NULL")
            cursor.execute("ALTER TABLE transactions ADD CONSTRAINT fk_counterparty_account FOREIGN KEY (counterparty_account_id) REFERENCES accounts(account_id)")
            print("counterparty_account_id column added successfully.")
        else:
            print("counterparty_account_id column already exists.")

        # Add missing columns
        columns_to_add = [
            ("counterparty_account_number", "VARCHAR(30) NULL"),
            ("counterparty_bank_name", "VARCHAR(100) NULL"),
            ("counterparty_ifsc_code", "VARCHAR(20) NULL"),
            ("transfer_type", "ENUM('IMPS', 'NEFT', 'RTGS', 'UPI', 'MOBILE') NULL"),
            ("reference_number", "VARCHAR(50) NULL"),
            ("status", "ENUM('Pending', 'Completed', 'Failed', 'Cancelled') NULL"),
            ("initiated_at", "TIMESTAMP NULL"),
            ("completed_at", "TIMESTAMP NULL"),
            ("remarks", "VARCHAR(255) NULL")
        ]

        for col_name, col_def in columns_to_add:
            cursor.execute(f"SHOW COLUMNS FROM transactions LIKE '{col_name}'")
            if not cursor.fetchone():
                print(f"Adding {col_name} column to transactions table...")
                cursor.execute(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_def}")
                print(f"{col_name} column added successfully.")
            else:
                print(f"{col_name} column already exists.")

        # Check if beneficiary_id column exists and remove it
        cursor.execute("SHOW COLUMNS FROM transactions LIKE 'beneficiary_id'")
        if cursor.fetchone():
            print("Removing beneficiary_id column from transactions table...")
            # First drop the foreign key constraint
            cursor.execute("ALTER TABLE transactions DROP FOREIGN KEY fk_beneficiary_id")
            # Then drop the column
            cursor.execute("ALTER TABLE transactions DROP COLUMN beneficiary_id")
            print("beneficiary_id column removed successfully.")
        else:
            print("beneficiary_id column does not exist.")

        conn.commit()

    except Exception as e:
        print(f"Error fixing transactions table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_transactions_table()
