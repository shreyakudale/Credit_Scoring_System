import mysql.connector
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.db_config import DB_CONFIG

def create_predictions_table():
    """Create the predictions table if it doesn't exist."""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # Check if predictions table exists
        cursor.execute("SHOW TABLES LIKE 'predictions'")
        if not cursor.fetchone():
            print("Creating predictions table...")

            # Create predictions table
            cursor.execute('''
                CREATE TABLE predictions (
                    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id INT NOT NULL,
                    score DECIMAL(6,2) NOT NULL,
                    decision ENUM('Approved', 'Declined', 'Review') NOT NULL,
                    confidence DECIMAL(3,2) NOT NULL,
                    shap_values JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                )
            ''')

            print("Predictions table created successfully.")
        else:
            print("Predictions table already exists.")

        conn.commit()

    except Exception as e:
        print(f"Error creating predictions table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_predictions_table()
