"""
Migration script to add loan_applications table to existing database
Run this script to update your database schema
"""

import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_db_connection

def add_loan_applications_table():
    """Add loan_applications table to the database"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("Creating loan_applications table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loan_applications (
                application_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT,
                loan_type ENUM('Personal', 'Home', 'Car', 'Education', 'Business', 'Credit') NOT NULL,
                requested_amount DECIMAL(15,2) NOT NULL,
                tenure_months INT NOT NULL,
                purpose VARCHAR(255),
                employment_type ENUM('Salaried', 'Self-Employed', 'Business', 'Professional', 'Retired', 'Student') NOT NULL,
                employer_name VARCHAR(100),
                monthly_income DECIMAL(15,2) NOT NULL,
                existing_loans DECIMAL(15,2) DEFAULT 0.0,
                existing_emi DECIMAL(15,2) DEFAULT 0.0,
                property_value DECIMAL(15,2),
                down_payment DECIMAL(15,2),
                co_applicant_name VARCHAR(100),
                co_applicant_income DECIMAL(15,2),
                application_status ENUM('Pending', 'Under Review', 'Approved', 'Rejected', 'Cancelled') DEFAULT 'Pending',
                credit_score_at_application INT,
                approved_amount DECIMAL(15,2),
                approved_interest_rate DECIMAL(5,2),
                approved_tenure_months INT,
                calculated_emi DECIMAL(15,2),
                documents_submitted BOOLEAN DEFAULT FALSE,
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_date TIMESTAMP NULL,
                reviewer_notes TEXT,
                rejection_reason VARCHAR(255),
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
            )
        """)
        
        conn.commit()
        print("✓ loan_applications table created successfully!")
        
    except Exception as e:
        print(f"✗ Error creating table: {str(e)}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration: Add Loan Applications Table")
    print("=" * 60)
    add_loan_applications_table()
    print("=" * 60)
    print("Migration completed!")
