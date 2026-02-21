-- Sample data for testing the credit scoring system

-- Insert sample customers
INSERT INTO customers (customer_id, full_name, dob, gender, email, password_hash, phone, address, created_at) VALUES
(3, 'John Doe', '1980-01-01', 'Male', 'john.doe@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '1234567890', '123 Main St, City, State', NOW()),
(4, 'Jane Smith', '1985-05-15', 'Female', 'jane.smith@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '0987654321', '456 Elm St, City, State', NOW()),
(5, 'Bhavesh More', '1978-12-10', 'Male', 'bhavesh.1252010013@vit.edu', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '960057450', '789 Pine Rd, City, State', NOW()),
(6, 'Rahul Sharma', '1982-03-15', 'Male', 'rahul.sharma@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '1111111111', '101 Oak St, City, State', NOW()),
(7, 'Priya Patel', '1987-07-20', 'Female', 'priya.patel@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '2222222222', '202 Maple St, City, State', NOW()),
(8, 'Arjun Singh', '1979-11-05', 'Male', 'arjun.singh@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '3333333333', '303 Birch St, City, State', NOW()),
(9, 'Anjali Gupta', '1984-09-12', 'Female', 'anjali.gupta@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '4444444444', '404 Cedar St, City, State', NOW()),
(10, 'Vikram Kumar', '1981-04-18', 'Male', 'vikram.kumar@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '5555555555', '505 Pine St, City, State', NOW()),
(11, 'Meera Joshi', '1986-12-25', 'Female', 'meera.joshi@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '6666666666', '606 Elm St, City, State', NOW()),
(12, 'Rohan Agarwal', '1983-06-08', 'Male', 'rohan.agarwal@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '7777777777', '707 Ash St, City, State', NOW()),
(13, 'Kavita Desai', '1988-02-14', 'Female', 'kavita.desai@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '8888888888', '808 Willow St, City, State', NOW()),
(14, 'Sandeep Reddy', '1980-08-30', 'Male', 'sandeep.reddy@example.com', '$2b$12$SSwbWv5qZniJPKrYwLXTS.5B2IuwYELvrh3Hr/./LDqzpGJF0py56', '9999999999', '909 Poplar St, City, State', NOW());

-- Insert sample accounts
INSERT INTO accounts (customer_id, account_number, bank_name, ifsc_code, account_type, balance, opened_date, status, is_primary) VALUES
(3, '1234567890', 'BankOne', 'BKON0001234', 'Savings', 50000.00, '2020-01-01', 'Active', TRUE),
(4, '2345678901', 'BankTwo', 'BKTW0002345', 'Current', 75000.00, '2021-05-15', 'Active', TRUE),
(5, '3456789012', 'SecureBank', 'SBIN0003456', 'Savings', 30000.00, '2022-01-05', 'Active', TRUE),
(6, '4567890123', 'BankThree', 'BKTH0004567', 'Savings', 45000.00, '2020-03-15', 'Active', TRUE),
(7, '5678901234', 'BankFour', 'BKFR0005678', 'Current', 60000.00, '2021-07-20', 'Active', TRUE),
(8, '6789012345', 'BankFive', 'BKFV0006789', 'Savings', 55000.00, '2019-11-05', 'Active', TRUE),
(9, '7890123456', 'BankSix', 'BKSX0007890', 'Savings', 40000.00, '2022-09-12', 'Active', TRUE),
(10, '8901234567', 'BankSeven', 'BKSV0008901', 'Current', 70000.00, '2020-04-18', 'Active', TRUE),
(11, '9012345678', 'BankEight', 'BKET0009012', 'Savings', 50000.00, '2021-12-25', 'Active', TRUE),
(12, '0123456789', 'BankNine', 'BKNV0000123', 'Savings', 65000.00, '2022-06-08', 'Active', TRUE),
(13, '1234567891', 'BankTen', 'BKTT0001235', 'Current', 55000.00, '2020-02-14', 'Active', TRUE),
(14, '2345678902', 'BankEleven', 'BKEL0002346', 'Savings', 60000.00, '2019-08-30', 'Active', TRUE);


-- Insert sample credit scores
INSERT INTO credit_scores (customer_id, score, model_version, calculated_at, risk_level) VALUES
(3, 350, 'v1.0', NOW(), 'Low'),
(4, 780, 'v1.0', NOW(), 'High'),
(5, 450, 'v1.0', NOW(), 'Low'),
(6, 550, 'v1.0', NOW(), 'Medium'),
(7, 650, 'v1.0', NOW(), 'Medium'),
(8, 750, 'v1.0', NOW(), 'High'),
(9, 850, 'v1.0', NOW(), 'Low'),
(10, 320, 'v1.0', NOW(), 'Low'),
(11, 480, 'v1.0', NOW(), 'Low'),
(12, 620, 'v1.0', NOW(), 'Medium'),
(13, 720, 'v1.0', NOW(), 'High'),
(14, 880, 'v1.0', NOW(), 'Low');

-- Insert sample loans (disbursed loans)
INSERT INTO loans (customer_id, loan_type, principal_amount, interest_rate, issue_date, due_date, status) VALUES
(3, 'Mortgage', 150000.00, 8.5, '2022-01-01', '2032-01-01', 'Active'),
(4, 'Auto', 80000.00, 9.5, '2023-03-10', '2028-03-10', 'Active'),
(5, 'Personal', 30000.00, 11.0, '2023-08-20', '2025-08-20', 'Active');

-- Insert sample payments for loans
INSERT INTO payments (loan_id, payment_date, amount_paid, payment_status) VALUES
(2, '2022-07-01', 1500.00, 'On-Time'),
(2, '2022-08-01', 1500.00, 'On-Time'),
(2, '2022-09-01', 1500.00, 'On-Time'),
(2, '2022-10-01', 1500.00, 'On-Time'),
(2, '2022-11-01', 1500.00, 'On-Time'),
(3, '2023-04-10', 1800.00, 'On-Time'),
(3, '2023-05-10', 1800.00, 'On-Time'),
(3, '2023-06-10', 1800.00, 'On-Time'),
(3, '2023-07-10', 1800.00, 'On-Time'),
(2, '2023-09-20', 2800.00, 'On-Time'),
(2, '2023-10-20', 2800.00, 'On-Time'),
(2, '2023-11-20', 2800.00, 'On-Time');

-- Insert sample loan applications
INSERT INTO loan_applications (customer_id, loan_type, requested_amount, tenure_months, purpose, employment_type, employer_name, monthly_income, existing_loans, existing_emi, property_value, down_payment, co_applicant_name, co_applicant_income, application_status, credit_score_at_application, approved_amount, approved_interest_rate, approved_tenure_months, calculated_emi, applied_date) VALUES
(4, 'Business', 100000.00, 60, 'Business Expansion', 'Self-Employed', 'ABC Enterprises', 35000.00, 3, 3000.00, NULL, NULL, NULL, NULL, 'Under Review', 680, NULL, NULL, NULL, NULL, '2023-10-15'),
(5, 'Home', 300000.00, 240, 'Purchase Property', 'Salaried', 'Finance Ltd', 55000.00, 0, 0.00, 400000.00, 100000.00, NULL, NULL, 'Pending', 720, NULL, NULL, NULL, NULL, '2023-11-01'),
(3, 'Car', 60000.00, 48, 'Vehicle Purchase', 'Salaried', 'Tech Corp', 45000.00, 4, 6000.00, NULL, NULL, NULL, NULL, 'Approved', 750, 60000.00, 9.5, 48, 1450.00, '2023-08-15');

-- Insert sample transactions
INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, merchant, category, description) VALUES
(1, '2023-12-01 10:30:00', 'Credit', 5000.00, 'Salary', 'Income', 'Monthly Salary'),
(1, '2023-12-02 14:20:00', 'Debit', 1200.00, 'Grocery Store', 'Shopping', 'Weekly groceries'),
(1, '2023-12-03 16:45:00', 'Debit', 2500.00, 'Electricity Bill', 'Utilities', 'Monthly electricity bill'),
(2, '2023-12-01 09:00:00', 'Credit', 8000.00, 'Business Income', 'Income', 'Business revenue'),
(2, '2023-12-04 11:15:00', 'Debit', 3500.00, 'Office Supplies', 'Business', 'Office equipment'),
(1, '2023-12-01 08:30:00', 'Credit', 6000.00, 'Salary', 'Income', 'Monthly Salary'),
(2, '2023-12-01 12:00:00', 'Credit', 4000.00, 'Freelance', 'Income', 'Freelance project payment');
