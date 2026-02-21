import mysql.connector
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.db_config import DB_CONFIG

def load_sample_data():
    """Load sample data into the database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Truncate tables to ensure clean load
        truncate_statements = [
            "SET FOREIGN_KEY_CHECKS = 0;",
            "TRUNCATE TABLE payments;",
            "TRUNCATE TABLE loans;",
            "TRUNCATE TABLE loan_applications;",
            "TRUNCATE TABLE transactions;",
            "TRUNCATE TABLE accounts;",
            "TRUNCATE TABLE credit_scores;",
            "TRUNCATE TABLE customers;",
            "TRUNCATE TABLE employment_info;",
            "TRUNCATE TABLE model_features;",
            "SET FOREIGN_KEY_CHECKS = 1;"
        ]
        for stmt in truncate_statements:
            cursor.execute(stmt)

        # Read and execute sample data
        with open('database/sample_data.sql', 'r') as f:
            sql = f.read()

        # Split by semicolon and execute each statement
        statements = sql.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                cursor.execute(statement)

        conn.commit()
        print("Sample data loaded successfully!")

    except Exception as e:
        print(f"Error loading sample data: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    load_sample_data()
