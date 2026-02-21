-- ============================
-- 1. Customers Table
-- ============================
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    dob DATE,
    gender ENUM('Male', 'Female', 'Other'),
    national_id VARCHAR(50) UNIQUE,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(13) UNIQUE,
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================
-- 2. Accounts Table
-- ============================
CREATE TABLE IF NOT EXISTS accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    account_number VARCHAR(30) UNIQUE,
    bank_name VARCHAR(100),
    ifsc_code VARCHAR(20),
    account_type ENUM('Savings', 'Current', 'Credit'),
    balance DECIMAL(15,2) DEFAULT 0.0,
    opened_date DATE,
    status ENUM('Active', 'Closed', 'Suspended') DEFAULT 'Active',
    is_primary BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================
-- 3. Transactions Table (account transactions and transfers)
-- ============================
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_id INT,
    transaction_date DATETIME,
    transaction_type ENUM('Credit', 'Debit'),
    amount DECIMAL(15,2),
    merchant VARCHAR(100),
    category VARCHAR(50),
    description VARCHAR(255),
    counterparty_account_id INT NULL,
    counterparty_account_number VARCHAR(30) NULL,
    counterparty_bank_name VARCHAR(100) NULL,
    counterparty_ifsc_code VARCHAR(20) NULL,
    transfer_type ENUM('IMPS', 'NEFT', 'RTGS', 'UPI', 'MOBILE') NULL,
    reference_number VARCHAR(50) NULL,
    status ENUM('Pending', 'Completed', 'Failed', 'Cancelled') NULL,
    initiated_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    remarks VARCHAR(255) NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (counterparty_account_id) REFERENCES accounts(account_id)
);


-- ============================
-- 4. Loans Table
-- ============================
CREATE TABLE IF NOT EXISTS loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    loan_type ENUM('Personal', 'Mortgage', 'Auto', 'Education', 'CreditCard'),
    principal_amount DECIMAL(15,2),
    interest_rate DECIMAL(5,2),
    issue_date DATE,
    due_date DATE,
    status ENUM('Active', 'Closed', 'Defaulted') DEFAULT 'Active',
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================
-- 4a. Loan Applications Table
-- ============================
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
);

-- ============================
-- 5. Payments Table (loan repayments)
-- ============================
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT,
    payment_date DATE,
    amount_paid DECIMAL(15,2),
    payment_status ENUM('On-Time', 'Late', 'Missed'),
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
);

-- ============================
-- 6. Employment Info
-- ============================
CREATE TABLE IF NOT EXISTS employment_info (
    employment_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    employer_name VARCHAR(100),
    job_title VARCHAR(100),
    annual_income DECIMAL(15,2),
    years_at_job INT,
    employment_type ENUM('Salaried', 'Self-Employed', 'Unemployed'),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================
-- 7. Credit Scores Table
-- ============================
CREATE TABLE IF NOT EXISTS credit_scores (
    score_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    score INT CHECK (score BETWEEN 300 AND 900),
    model_version VARCHAR(50),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    risk_level ENUM('Low', 'Medium', 'High'),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ============================
-- 8. Model Features Table (AI input features)
-- ============================
CREATE TABLE IF NOT EXISTS model_features (
    feature_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    avg_transaction_amount DECIMAL(15,2),
    total_loans INT,
    active_loans INT,
    ontime_payment_ratio DECIMAL(5,2),
    income_to_loan_ratio DECIMAL(8,4),
    credit_utilization DECIMAL(5,2),
    missed_payment_count INT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
