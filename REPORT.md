# AI-Powered Credit Scoring System - Project Report

## 1. ACKNOWLEDGEMENT

I would like to express my sincere gratitude to all the individuals and organizations that contributed to the development of this AI-Powered Credit Scoring System project. Special thanks to the open-source community for providing the essential libraries and frameworks, including Flask, LightGBM, Scikit-learn, SHAP, Pandas, NumPy, and Bootstrap, which formed the backbone of this application. I am also indebted to the academic and research community for their insights into machine learning and credit risk assessment. Finally, I acknowledge the support from my mentors and peers who provided guidance and feedback throughout the project.

## 2. Introduction

The AI-Powered Credit Scoring System is a web-based application designed to predict credit scores and assess default risk for customers using advanced machine learning techniques. Built with a Flask backend, MySQL database, and a responsive HTML/CSS frontend, the system integrates data from customer profiles, transaction histories, loan records, and employment information to generate accurate credit scores. The application leverages models like LightGBM for prediction and SHAP for explainability, ensuring transparency in decision-making. This project addresses the growing need for automated, data-driven credit evaluation in financial institutions, reducing manual effort and improving accuracy while providing users with intuitive interfaces for data input, score visualization, and historical tracking.

## 3. Methodology

The methodology for developing the AI-Powered Credit Scoring System involved several key phases:

- **Data Collection and Preprocessing**: Customer data, including personal details, account information, transactions, loans, and employment records, were collected and stored in a MySQL database. Data preprocessing involved cleaning, normalization, and feature engineering using Pandas and NumPy to prepare inputs for the ML model.

- **Database Design**: The database schema was designed in MySQL with normalized tables to ensure data integrity and efficiency. Relationships between entities (e.g., customers to accounts, accounts to transactions) were established using foreign keys.

- **Model Development**: A machine learning model was trained using LightGBM on historical data to predict credit scores (ranging from 300 to 900) and risk levels (Low, Medium, High). Feature engineering included calculating metrics like average transaction amounts, on-time payment ratios, and credit utilization.

- **Explainability**: SHAP (SHapley Additive exPlanations) was integrated to provide interpretable explanations for model predictions, helping users understand the factors influencing their credit scores.

- **Web Application Development**: The backend was implemented in Flask with routes for user authentication, data input, score calculation, and API endpoints. The frontend used Jinja2 templates, Bootstrap for styling, and JavaScript for interactivity, including QR code scanning for payments.

- **Testing and Deployment**: The system was tested for functionality, security, and performance. Deployment involved setting up the database, training the model, and running the Flask app locally.

## 4. Structure of Each Table Used

The database schema consists of the following tables, each designed to store specific data entities with appropriate data types, constraints, and relationships:

- **customers**: Stores customer personal information.
  - customer_id (INT, PRIMARY KEY, AUTO_INCREMENT)
  - full_name (VARCHAR(100), NOT NULL)
  - dob (DATE)
  - gender (ENUM('Male', 'Female', 'Other'))
  - national_id (VARCHAR(50), UNIQUE)
  - email (VARCHAR(100), UNIQUE)
  - password_hash (VARCHAR(255), NOT NULL)
  - phone (VARCHAR(13), UNIQUE)
  - address (VARCHAR(255))
  - created_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

- **accounts**: Manages customer bank accounts.
  - account_id (INT, PRIMARY KEY, AUTO_INCREMENT)
  - customer_id (INT, FOREIGN KEY to customers)
  - account_number (VARCHAR(30), UNIQUE)
  - account_type (ENUM('Savings', 'Current', 'Credit'))
  - balance (DECIMAL(15,2), DEFAULT 0.0)
  - opened_date (DATE)
  - status (ENUM('Active', 'Closed', 'Suspended'), DEFAULT 'Active')
  - is_primary (BOOLEAN, DEFAULT FALSE)

- **transactions**: Records financial transactions.
  - transaction_id (BIGINT, PRIMARY KEY, AUTO_INCREMENT)
  - account_id (INT, FOREIGN KEY to accounts)
  - transaction_date (DATETIME)
  - transaction_type (ENUM('Credit', 'Debit'))
  - amount (DECIMAL(15,2))
  - merchant (VARCHAR(100))
  - category (VARCHAR(50))
  - description (VARCHAR(255))

- **loans**: Tracks loan details.
  - loan_id (INT, PRIMARY KEY, AUTO_INCREMENT)
  - customer_id (INT, FOREIGN KEY to customers)
  - loan_type (ENUM('Personal', 'Mortgage', 'Auto', 'Education', 'CreditCard'))
  - principal_amount (DECIMAL(15,2))
  - interest_rate (DECIMAL(5,2))
  - issue_date (DATE)
  - due_date (DATE)
  - status (ENUM('Active', 'Closed', 'Defaulted'), DEFAULT 'Active')

- **payments**: Records loan repayments.
  - payment_id (INT, PRIMARY KEY, AUTO_INCREMENT)
  - loan_id (INT, FOREIGN KEY to loans)
  - payment_date (DATE)
  - amount_paid (DECIMAL(15,2))
  - payment_status (ENUM('On-Time', 'Late', 'Missed'))

- **employment_info**: Stores employment details.
  - employment_id (INT, PRIMARY KEY, AUTO_INCREMENT)
  - customer_id (INT, FOREIGN KEY to customers)
  - employer_name (VARCHAR(100))
  - job_title (VARCHAR(100))
  - annual_income (DECIMAL(15,2))
  - years_at_job (INT)
  - employment_type (ENUM('Salaried', 'Self-Employed', 'Unemployed'))

- **credit_scores**: Stores calculated credit scores.
  - score_id (INT, PRIMARY KEY, AUTO_INCREMENT)
  - customer_id (INT, FOREIGN KEY to customers)
  - score (INT, CHECK BETWEEN 300 AND 900)
  - model_version (VARCHAR(50))
  - calculated_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
  - risk_level (ENUM('Low', 'Medium', 'High'))

- **model_features**: Holds features for ML model input.
  - feature_id (INT, PRIMARY KEY, AUTO_INCREMENT)
  - customer_id (INT, FOREIGN KEY to customers)
  - avg_transaction_amount (DECIMAL(15,2))
  - total_loans (INT)
  - active_loans (INT)
  - ontime_payment_ratio (DECIMAL(5,2))
  - income_to_loan_ratio (DECIMAL(8,4))
  - credit_utilization (DECIMAL(5,2))
  - missed_payment_count (INT)
  - last_updated (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

- **beneficiaries**: Manages saved transfer recipients.
  - beneficiary_id (INT, PRIMARY KEY, AUTO_INCREMENT)
  - customer_id (INT, FOREIGN KEY to customers)
  - name (VARCHAR(100), NOT NULL)
  - account_number (VARCHAR(30), NOT NULL)
  - bank_name (VARCHAR(100))
  - ifsc_code (VARCHAR(20))
  - phone (VARCHAR(13))
  - email (VARCHAR(100))
  - is_verified (BOOLEAN, DEFAULT FALSE)
  - added_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
  - UNIQUE KEY on (customer_id, account_number, ifsc_code)

- **transections**: Detailed transfer records (note: likely a typo for "transactions" in schema).
  - transfer_id (BIGINT, PRIMARY KEY, AUTO_INCREMENT)
  - sender_account_id (INT, FOREIGN KEY to accounts)
  - receiver_account_id (INT, FOREIGN KEY to accounts)
  - beneficiary_id (INT, NULL, FOREIGN KEY to beneficiaries)
  - amount (DECIMAL(15,2), NOT NULL)
  - transfer_type (ENUM('IMPS', 'NEFT', 'RTGS', 'UPI', 'MOBILE'), DEFAULT 'IMPS')
  - reference_number (VARCHAR(50), UNIQUE)
  - status (ENUM('Pending', 'Completed', 'Failed', 'Cancelled'), DEFAULT 'Pending')
  - remarks (VARCHAR(255))
  - initiated_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
  - completed_at (TIMESTAMP, NULL)

## 5. Normalized Form of the Project Database

The database is designed in Third Normal Form (3NF). This normalization level ensures that:

- **First Normal Form (1NF)**: All tables have atomic values, no repeating groups, and a primary key. For example, the `customers` table has no multi-valued attributes.

- **Second Normal Form (2NF)**: All non-key attributes are fully functionally dependent on the primary key. Partial dependencies are eliminated; e.g., in `accounts`, `account_number` depends only on `account_id`.

- **Third Normal Form (3NF)**: No transitive dependencies exist. Non-key attributes do not depend on other non-key attributes. For instance, in `transactions`, `merchant` and `category` depend directly on `transaction_id`, not on each other or other attributes.

This structure minimizes redundancy, ensures data integrity through foreign keys, and supports efficient querying and updates. The use of ENUM types and CHECK constraints further enforces data consistency.

## 6. Conclusion

The AI-Powered Credit Scoring System successfully demonstrates the integration of machine learning with web development to create a practical tool for credit risk assessment. By leveraging data from multiple sources and providing explainable predictions, the system enhances transparency and trust in automated decision-making. The project highlights the potential of AI in finance, offering a scalable solution that can be adapted for real-world applications. Overall, it achieves its goals of accuracy, usability, and interpretability, paving the way for further advancements in financial technology.

## 7. Future Scope

Future enhancements could include:

- **Advanced Models**: Integration of deep learning techniques like neural networks for more complex predictions.
- **Real-Time Data**: Incorporation of real-time transaction data via APIs for dynamic score updates.
- **Mobile App**: Development of a companion mobile application for on-the-go access.
- **Regulatory Compliance**: Addition of features to ensure compliance with financial regulations like GDPR or CCPA.
- **Scalability**: Migration to cloud platforms (e.g., AWS, Azure) for handling larger datasets and user bases.
- **Additional Features**: Expansion to include fraud detection, personalized loan recommendations, and integration with third-party credit bureaus.

This report provides a comprehensive overview of the project, from conceptualization to implementation and potential future developments.
