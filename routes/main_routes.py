# 🌐 Handles all Flask routes (views)
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import pandas as pd
import numpy as np
import json

import bcrypt
from config.db_config import get_db_connection, get_db_cursor
from datetime import datetime, date

main_bp = Blueprint('main', __name__)

# Import model prediction functions
from model.feature_engineering import predict_credit_score

@main_bp.route('/')
def index():
    recent_transactions = []
    if 'customer_id' in session:
        customer_id = session['customer_id']
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch recent bank transfers (last 3)
        cursor.execute('''
            SELECT transaction_date, transaction_type, amount, description
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.customer_id = %s AND t.category = 'Transfer'
            ORDER BY t.transaction_date DESC
            LIMIT 3
        ''', (customer_id,))

        transactions = cursor.fetchall()
        conn.close()

        # Process transactions for display
        from datetime import datetime, date
        today = date.today()

        for row in transactions:
            transaction_date = row[0]
            transaction_type = row[1]
            amount = row[2]
            description = row[3] or ''

            # Format display date
            if transaction_date.date() == today:
                display_date = f"Today, {transaction_date.strftime('%I:%M %p')}"
            elif (today - transaction_date.date()).days == 1:
                display_date = f"Yesterday, {transaction_date.strftime('%I:%M %p')}"
            else:
                days_ago = (today - transaction_date.date()).days
                display_date = f"{days_ago} days ago"

            recent_transactions.append({
                'type': transaction_type,
                'amount': amount,
                'description': description,
                'display_date': display_date
            })

    return render_template('index.html', recent_transactions=recent_transactions)

@main_bp.route('/predict', methods=['POST'])
def predict():
    customer_id = request.form.get('customer_id')
    if not customer_id:
        flash('Please enter a customer ID.', 'error')
        return redirect(url_for('main.index'))

    try:
        customer_id = int(customer_id)
    except ValueError:
        flash('Invalid customer ID format.', 'error')
        return redirect(url_for('main.index'))

    # Fetch customer from database
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM customers WHERE customer_id = %s', (customer_id,))
    customer_row = cursor.fetchone()

    if not customer_row:
        conn.close()
        flash('Customer not found!', 'error')
        return redirect(url_for('main.index'))

    # Convert row to dict (MySQL returns tuple)
    customer = dict(zip([desc[0] for desc in cursor.description], customer_row))

    # Use trained model for prediction
    prediction_result = predict_credit_score(customer)

    if prediction_result is None:
        # Fallback to mock prediction if model fails
        if customer['credit_score'] >= 750:
            score = 780.5
            decision = 'Approved'
            confidence = 0.92
        elif customer['credit_score'] >= 650:
            score = 720.5
            decision = 'Approved'
            confidence = 0.85
        elif customer['credit_score'] >= 600:
            score = 650.0
            decision = 'Review'
            confidence = 0.65
        else:
            score = 580.0
            decision = 'Declined'
            confidence = 0.45

        prediction = {
            'score': score,
            'decision': decision,
            'confidence': confidence
        }

        # Mock SHAP values
        shap_values = [
            {'feature': 'Income', 'value': 0.15},
            {'feature': 'Credit History', 'value': 0.12},
            {'feature': 'Debt-to-Income Ratio', 'value': -0.08},
            {'feature': 'Employment Length', 'value': 0.06},
            {'feature': 'Age', 'value': 0.03}
        ]
    else:
        prediction = prediction_result
        # Convert SHAP dict to list format for template
        shap_values = [{'feature': k, 'value': v} for k, v in prediction_result.get('shap_values', {}).items()]

    # Save prediction to database
    shap_json = json.dumps(shap_values)
    cursor.execute('''
        INSERT INTO predictions (customer_id, score, decision, confidence, shap_values)
        VALUES (%s, %s, %s, %s, %s)
    ''', (customer_id, prediction['predicted_score'], prediction['decision'], prediction['confidence'], shap_json))

    conn.commit()
    conn.close()

    return render_template('result.html',
                         customer=customer,
                         prediction=prediction,
                         shap_values=shap_values)

@main_bp.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        age = request.form.get('age')
        income = request.form.get('income')
        credit_score = request.form.get('credit_score')
        debt_to_income = request.form.get('debt_to_income')
        employment_years = request.form.get('employment_years')
        loan_amount = request.form.get('loan_amount')
        loan_term = request.form.get('loan_term')
        home_ownership = request.form.get('home_ownership')
        purpose = request.form.get('purpose')
        address = request.form.get('address')

        # Validate required fields
        if not all([name, age, income, credit_score, debt_to_income, employment_years, loan_amount, loan_term, home_ownership, purpose, address]):
            flash('All fields are required!', 'error')
            return redirect(url_for('main.add_customer'))

        try:
            # Convert numeric fields
            age = int(age)
            income = float(income)
            credit_score = int(credit_score)
            debt_to_income = float(debt_to_income)
            employment_years = float(employment_years)
            loan_amount = float(loan_amount)
            loan_term = int(loan_term)

            # Insert into database
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO customers (name, age, income, credit_score, debt_to_income, employment_years, loan_amount, loan_term, home_ownership, purpose, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (name, age, income, credit_score, debt_to_income, employment_years, loan_amount, loan_term, home_ownership, purpose, address))

            conn.commit()
            conn.close()

            flash('Customer added successfully!', 'success')
            return redirect(url_for('main.index'))

        except ValueError:
            flash('Invalid numeric values provided!', 'error')
            return redirect(url_for('main.add_customer'))
        except Exception as e:
            flash(f'Error adding customer: {str(e)}', 'error')
            return redirect(url_for('main.add_customer'))

    return render_template('add_customer.html')

@main_bp.route('/manage_accounts', methods=['GET', 'POST'])
def manage_accounts():
    if 'customer_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']

    if request.method == 'POST':
        # Check if it's a primary account update or new account addition
        if 'set_primary' in request.form:
            account_id = request.form.get('account_id')
            try:
                account_id = int(account_id)
            except ValueError:
                flash('Invalid account ID!', 'error')
                return redirect(url_for('main.manage_accounts'))

            # Set all accounts to non-primary first
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('UPDATE accounts SET is_primary = FALSE WHERE customer_id = %s', (customer_id,))
            # Set the selected account as primary
            cursor.execute('UPDATE accounts SET is_primary = TRUE WHERE account_id = %s AND customer_id = %s', (account_id, customer_id))
            conn.commit()
            conn.close()

            flash('Primary account updated successfully!', 'success')
            return redirect(url_for('main.manage_accounts'))

        # Handle new account addition
        account_number = request.form.get('account_number')
        account_type = request.form.get('account_type')
        bank_name = request.form.get('bank_name')
        ifsc_code = request.form.get('ifsc_code')
        initial_balance = request.form.get('initial_balance', 0.0)

        if not all([account_number, account_type, bank_name, ifsc_code]):
            flash('Account number, type, bank name, and IFSC code are required!', 'error')
            return redirect(url_for('main.manage_accounts'))

        try:
            initial_balance = float(initial_balance)
        except ValueError:
            flash('Invalid initial balance!', 'error')
            return redirect(url_for('main.manage_accounts'))

        # Check if account number already exists
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT account_id FROM accounts WHERE account_number = %s', (account_number,))
        if cursor.fetchone():
            conn.close()
            flash('Account number already exists!', 'error')
            return redirect(url_for('main.manage_accounts'))

        # Add new account
        cursor.execute('''
            INSERT INTO accounts (customer_id, account_number, bank_name, ifsc_code, account_type, balance, opened_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, CURDATE(), 'Active')
        ''', (customer_id, account_number, bank_name, ifsc_code, account_type, initial_balance))

        conn.commit()
        conn.close()

        flash('Account added successfully!', 'success')
        return redirect(url_for('main.manage_accounts'))

    # Fetch user's accounts
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT account_id, account_number, account_type, balance, opened_date, status, is_primary
        FROM accounts
        WHERE customer_id = %s
        ORDER BY opened_date DESC
    ''', (customer_id,))

    accounts = cursor.fetchall()
    conn.close()

    # Convert to list of dicts
    accounts_list = []
    for row in accounts:
        accounts_list.append({
            'account_id': row[0],
            'account_number': row[1],
            'account_type': row[2],
            'balance': row[3],
            'opened_date': row[4],
            'status': row[5],
            'is_primary': bool(row[6])
        })

    return render_template('manage_accounts.html', accounts=accounts_list)

@main_bp.route('/history')
def history():
    # Fetch predictions from database
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.*, c.full_name as customer_name
        FROM predictions p
        JOIN customers c ON p.customer_id = c.customer_id
        ORDER BY p.created_at DESC
        LIMIT 50
    ''')

    predictions = cursor.fetchall()

    # Convert to list of dicts
    history_data = []
    approved_count = 0
    declined_count = 0
    total_count = 0

    for row in predictions:
        pred_dict = dict(row)
        pred_dict['created_at'] = pd.to_datetime(pred_dict['created_at'])
        history_data.append(pred_dict)

        total_count += 1
        if pred_dict['decision'] == 'Approved':
            approved_count += 1
        elif pred_dict['decision'] == 'Declined':
            declined_count += 1

    conn.close()

    # Calculate stats
    stats = {
        'approved': approved_count,
        'declined': declined_count,
        'total': total_count,
        'approved_rate': approved_count / total_count if total_count > 0 else 0,
        'declined_rate': declined_count / total_count if total_count > 0 else 0
    }

    return render_template('history.html', history=history_data, stats=stats)

@main_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form.get('full_name').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone').strip()
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        address = request.form.get('address').strip()

        # Validation
        if not all([full_name, email, password, confirm_password, phone, dob, gender, address]):
            flash('All fields are required.', 'error')
            return redirect(url_for('main.signup'))

        if len(full_name) < 2:
            flash('Full name must be at least 2 characters long.', 'error')
            return redirect(url_for('main.signup'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return redirect(url_for('main.signup'))

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('main.signup'))

        # Validate date of birth (must be at least 18 years old)
        from datetime import datetime, date
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            today = date.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

            if age < 18:
                flash('You must be at least 18 years old to create an account.', 'error')
                return redirect(url_for('main.signup'))
        except ValueError:
            flash('Invalid date of birth format.', 'error')
            return redirect(url_for('main.signup'))

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if email already exists
            cursor.execute('SELECT customer_id FROM customers WHERE email = %s', (email,))
            if cursor.fetchone():
                conn.close()
                flash('Email already exists.', 'error')
                return redirect(url_for('main.signup'))

            # Insert new customer
            cursor.execute('''
                INSERT INTO customers (full_name, dob, gender, email, password_hash, phone, address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (full_name, dob, gender, email, password_hash, phone, address))

            conn.commit()
            customer_id = cursor.lastrowid
            conn.close()

            # Log user in (store customer_id in session)
            session['customer_id'] = customer_id
            session['customer_name'] = full_name
            session['customer_email'] = email

            flash('Account created successfully! Welcome to SecureBank!', 'success')
            return redirect(url_for('main.index'))

        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'error')
            return redirect(url_for('main.signup'))

    return render_template('signup.html')

@main_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')

        if not all([email, password]):
            flash('Email and password are required.', 'error')
            return redirect(url_for('main.signin'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Fetch customer by email
            cursor.execute('SELECT customer_id, full_name, email, password_hash FROM customers WHERE email = %s', (email,))
            customer_row = cursor.fetchone()
            conn.close()

            if not customer_row:
                flash('Invalid email or password.', 'error')
                return redirect(url_for('main.signin'))

            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), customer_row[3].encode('utf-8')):
                flash('Invalid email or password.', 'error')
                return redirect(url_for('main.signin'))

            # Log customer in
            session['customer_id'] = customer_row[0]
            session['customer_name'] = customer_row[1]
            session['customer_email'] = customer_row[2]

            flash(f'Welcome back, {customer_row[1]}!', 'success')
            return redirect(url_for('main.index'))

        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
            return redirect(url_for('main.signin'))

    return render_template('signin.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/transfer', methods=['GET', 'POST'])
def transfer():
    import qrcode
    import base64
    import io

    if 'customer_id' not in session:
        flash('Please sign in to access this feature.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']

    if request.method == 'POST':
        # Handle transfer submission
        sender_account_id = request.form.get('sender_account')
        recipient_name = request.form.get('recipientName')
        recipient_account = request.form.get('recipientAccount')
        recipient_bank = request.form.get('recipientBank')
        recipient_ifsc = request.form.get('recipientIFSC')
        amount = request.form.get('amount')
        transfer_type = request.form.get('transferType')
        remarks = request.form.get('remarks')

        # Validate required fields
        if not all([sender_account_id, recipient_name, recipient_account, recipient_bank, recipient_ifsc, amount, transfer_type]):
            flash('All fields are required!', 'error')
            return redirect(url_for('main.transfer'))

        try:
            sender_account_id = int(sender_account_id)
            amount = float(amount)
        except ValueError:
            flash('Invalid numeric values!', 'error')
            return redirect(url_for('main.transfer'))

        if amount <= 0:
            flash('Amount must be greater than 0!', 'error')
            return redirect(url_for('main.transfer'))

        # Verify sender account belongs to user
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT balance FROM accounts WHERE account_id = %s AND customer_id = %s AND status = "Active"', (sender_account_id, customer_id))
        account_row = cursor.fetchone()

        if not account_row:
            conn.close()
            flash('Invalid sender account!', 'error')
            return redirect(url_for('main.transfer'))

        sender_balance = account_row[0]

        if sender_balance < amount:
            conn.close()
            flash('Insufficient balance!', 'error')
            return redirect(url_for('main.transfer'))

        # Check if receiver account exists
        cursor.execute('SELECT account_id FROM accounts WHERE account_number = %s AND status = "Active"', (recipient_account,))
        receiver_row = cursor.fetchone()

        if not receiver_row:
            conn.close()
            flash('Recipient account not found!', 'error')
            return redirect(url_for('main.transfer'))

        receiver_account_id = receiver_row[0]

        # Generate reference number
        import uuid
        reference_number = f"TXN{uuid.uuid4().hex[:16].upper()}"

        # Process transfer
        conn.rollback()
        conn.start_transaction()

        try:
            # Debit sender
            cursor.execute('UPDATE accounts SET balance = balance - %s WHERE account_id = %s', (amount, sender_account_id))

            # Credit receiver
            cursor.execute('UPDATE accounts SET balance = balance + %s WHERE account_id = %s', (amount, receiver_account_id))

            # Record debit transaction for sender
            cursor.execute('''
                INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, merchant, category, description, counterparty_account_id, counterparty_account_number, counterparty_bank_name, counterparty_ifsc_code, transfer_type, reference_number, status, remarks, initiated_at, completed_at)
                VALUES (%s, NOW(), 'Debit', %s, 'Money Transfer', 'Transfer', %s, %s, %s, %s, %s, %s, %s, 'Completed', %s, NOW(), NOW())
            ''', (sender_account_id, amount, f'Transfer to {recipient_account}', receiver_account_id, recipient_account, recipient_bank, recipient_ifsc, transfer_type, reference_number, remarks))

            # Record credit transaction for receiver
            cursor.execute('''
                INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, merchant, category, description, counterparty_account_id, counterparty_account_number, counterparty_bank_name, counterparty_ifsc_code, transfer_type, reference_number, status, remarks, initiated_at, completed_at)
                VALUES (%s, NOW(), 'Credit', %s, 'Money Transfer', 'Transfer', %s, %s, %s, %s, %s, %s, %s, 'Completed', %s, NOW(), NOW())
            ''', (receiver_account_id, amount, f'Received from transfer', sender_account_id, None, None, None, transfer_type, reference_number, remarks))

            conn.commit()
            flash(f'Transfer completed successfully! Reference: {reference_number}', 'success')

        except Exception as e:
            conn.rollback()
            flash(f'Transfer failed: {str(e)}', 'error')

        finally:
            conn.close()

        return redirect(url_for('main.transfer'))

    # GET request - show transfer form with user's accounts and beneficiaries
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get user's accounts
    cursor.execute('''
        SELECT account_id, account_number, account_type, balance
        FROM accounts
        WHERE customer_id = %s AND status = 'Active'
        ORDER BY account_type
    ''', (customer_id,))

    accounts = cursor.fetchall()

    # Get recent transfers (no beneficiaries table)
    cursor.execute('''
        SELECT t.reference_number, t.amount, t.transfer_type, t.completed_at, t.counterparty_account_number as recipient_account, t.counterparty_bank_name as recipient_bank
        FROM transactions t
        WHERE t.account_id IN (SELECT account_id FROM accounts WHERE customer_id = %s) AND t.transaction_type = 'Debit' AND t.category = 'Transfer'
        ORDER BY t.completed_at DESC
        LIMIT 10
    ''', (customer_id,))

    recent_transfers = cursor.fetchall()

    # Generate QR code for primary account
    cursor.execute('''
        SELECT account_number, account_type, c.full_name
        FROM accounts a
        JOIN customers c ON a.customer_id = c.customer_id
        WHERE a.customer_id = %s AND a.is_primary = TRUE AND a.status = 'Active'
        LIMIT 1
    ''', (customer_id,))

    primary_account = cursor.fetchone()
    conn.close()

    if primary_account:
        account_number, account_type, full_name = primary_account

        qr_data = f"{account_number}|{account_type}|{full_name}"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    else:
        qr_code_base64 = None

    # Convert to dicts for template
    accounts_list = []
    for row in accounts:
        accounts_list.append({
            'account_id': row[0],
            'account_number': row[1],
            'account_type': row[2],
            'balance': row[3]
        })

    recent_transfers_list = []
    for row in recent_transfers:
        recent_transfers_list.append({
            'reference_number': row[0],
            'amount': row[1],
            'transfer_type': row[2],
            'completed_at': row[3],
            'recipient_name': row[4],
            'account_number': row[5]
        })

    return render_template('transfer.html',
                         accounts=accounts_list,
                         recent_transfers=recent_transfers_list,
                         qr_code_base64=qr_code_base64)
@main_bp.route('/balance')
def balance():
    if 'customer_id' not in session:
        flash('Please sign in to access this feature.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']
    selected_account_id = request.args.get('account_id', type=int)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all active accounts for the customer
    cursor.execute('''
        SELECT account_id, account_number, account_type, balance, opened_date, status, is_primary
        FROM accounts
        WHERE customer_id = %s AND status = 'Active'
        ORDER BY is_primary DESC, opened_date DESC
    ''', (customer_id,))

    accounts_rows = cursor.fetchall()

    if not accounts_rows:
        conn.close()
        flash('No active accounts found.', 'error')
        return redirect(url_for('main.index'))

    # Convert accounts to list of dicts
    accounts = []
    primary_account_id = None
    for row in accounts_rows:
        account_dict = {
            'account_id': row[0],
            'account_number': row[1],
            'account_type': row[2],
            'balance': row[3],
            'opened_date': row[4],
            'status': row[5],
            'is_primary': bool(row[6])
        }
        accounts.append(account_dict)
        if account_dict['is_primary']:
            primary_account_id = account_dict['account_id']

    # Determine which account to show details for
    if selected_account_id:
        # Verify the selected account belongs to the user
        if not any(acc['account_id'] == selected_account_id for acc in accounts):
            selected_account_id = None

    if not selected_account_id:
        selected_account_id = primary_account_id or accounts[0]['account_id']

    # Get detailed information for selected account
    cursor.execute('''
        SELECT a.account_id, a.account_number, a.account_type, a.balance, a.opened_date, a.status,
               a.bank_name, a.ifsc_code, c.full_name, c.email
        FROM accounts a
        JOIN customers c ON a.customer_id = c.customer_id
        WHERE a.account_id = %s
    ''', (selected_account_id,))

    account_row = cursor.fetchone()

    if not account_row:
        conn.close()
        flash('Selected account not found.', 'error')
        return redirect(url_for('main.balance'))

    account = {
        'account_id': account_row[0],
        'account_number': account_row[1],
        'account_type': account_row[2],
        'balance': account_row[3],
        'opened_date': account_row[4],
        'status': account_row[5],
        'bank_name': account_row[6],
        'ifsc_code': account_row[7],
        'holder_name': account_row[8],
        'email': account_row[9]
    }

    # Get recent transactions for selected account (last 5)
    cursor.execute('''
        SELECT transaction_date, transaction_type, amount, merchant, category, description
        FROM transactions
        WHERE account_id = %s
        ORDER BY transaction_date DESC
        LIMIT 5
    ''', (selected_account_id,))

    transactions = cursor.fetchall()
    conn.close()

    # Convert transactions to list of dicts
    recent_transactions = []
    for row in transactions:
        recent_transactions.append({
            'date': row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else '',
            'type': row[1],
            'amount': row[2],
            'merchant': row[3] or '',
            'category': row[4] or '',
            'description': row[5] or ''
        })

    return render_template('balance.html',
                         accounts=accounts,
                         account=account,
                         selected_account_id=selected_account_id,
                         recent_transactions=recent_transactions)


@main_bp.route('/verify_account_password', methods=['POST'])
def verify_account_password():
    if 'customer_id' not in session:
        return {'success': False, 'message': 'Not authenticated'}, 401

    customer_id = session['customer_id']
    data = request.get_json()
    if not data or 'password' not in data:
        return {'success': False, 'message': 'Password is required'}, 400

    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT password_hash FROM customers WHERE customer_id = %s', (customer_id,))
    user_row = cursor.fetchone()

    if not user_row:
        conn.close()
        return {'success': False, 'message': 'User not found'}, 404

    password_hash = user_row[0]

    import bcrypt
    if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
        # Password correct - get full account number for selected account
        selected_account_id = request.args.get('account_id', type=int)
        if not selected_account_id:
            # If account_id param not sent, fallback to primary account
            cursor.execute('SELECT account_id FROM accounts WHERE customer_id = %s AND is_primary = TRUE AND status = "Active" LIMIT 1', (customer_id,))
            account_id_row = cursor.fetchone()
            if account_id_row:
                selected_account_id = account_id_row[0]

        if not selected_account_id:
            conn.close()
            return {'success': False, 'message': 'Account not found'}, 404

        cursor.execute('SELECT account_number FROM accounts WHERE account_id = %s AND customer_id = %s AND status = "Active"', (selected_account_id, customer_id))
        account_row = cursor.fetchone()
        conn.close()

        if not account_row:
            return {'success': False, 'message': 'Account not found or inaccessible'}, 404

        full_account_number = account_row[0]

        return {'success': True, 'account_number': full_account_number}
    else:
        conn.close()
        return {'success': False, 'message': 'Invalid password'}, 403

@main_bp.route('/loans')
def loans():
    if 'customer_id' not in session:
        flash('Please sign in to access this feature.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']

    # Get user's primary account balance
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT balance FROM accounts
        WHERE customer_id = %s AND is_primary = TRUE AND status = 'Active'
        LIMIT 1
    ''', (customer_id,))

    account_balance_row = cursor.fetchone()
    account_balance = account_balance_row[0] if account_balance_row else 0.0

    conn.close()

    return render_template('loans.html', account_balance=account_balance)

@main_bp.route('/apply_loan', methods=['GET', 'POST'])
def apply_loan():
    if 'customer_id' not in session:
        flash('Please sign in to apply for a loan.', 'error')
        return redirect(url_for('main.signin'))
    
    customer_id = session['customer_id']
    
    if request.method == 'POST':
        # Get form data
        loan_type = request.form.get('loan_type')
        requested_amount = request.form.get('requested_amount')
        tenure_months = request.form.get('tenure_months')
        purpose = request.form.get('purpose')
        employment_type = request.form.get('employment_type')
        employer_name = request.form.get('employer_name')
        monthly_income = request.form.get('monthly_income')
        existing_loans = request.form.get('existing_loans', 0)
        existing_emi = request.form.get('existing_emi', 0)
        property_value = request.form.get('property_value')
        down_payment = request.form.get('down_payment')
        co_applicant_name = request.form.get('co_applicant_name')
        co_applicant_income = request.form.get('co_applicant_income')
        
        # Validate required fields
        if not all([loan_type, requested_amount, tenure_months, purpose, employment_type, monthly_income]):
            flash('Please fill in all required fields!', 'error')
            return redirect(url_for('main.apply_loan'))
        
        try:
            # Convert to appropriate types
            requested_amount = float(requested_amount)
            tenure_months = int(tenure_months)
            monthly_income = float(monthly_income)
            existing_loans = float(existing_loans) if existing_loans else 0.0
            existing_emi = float(existing_emi) if existing_emi else 0.0
            property_value = float(property_value) if property_value else None
            down_payment = float(down_payment) if down_payment else None
            co_applicant_income = float(co_applicant_income) if co_applicant_income else None
            
            # Validate loan amount ranges
            loan_limits = {
                'Personal': (1000, 50000, 10.5),
                'Home': (50000, 500000, 8.5),
                'Car': (10000, 100000, 9.5),
                'Education': (10000, 200000, 7.5),
                'Business': (10000, 250000, 12.5),
                'Credit': (1000, 25000, 14.5)
            }
            
            if loan_type in loan_limits:
                min_amount, max_amount, interest_rate = loan_limits[loan_type]
                if requested_amount < min_amount or requested_amount > max_amount:
                    flash(f'Loan amount must be between ₹{min_amount:,.0f} and ₹{max_amount:,.0f} for {loan_type} loan.', 'error')
                    return redirect(url_for('main.apply_loan'))
            else:
                flash('Invalid loan type selected.', 'error')
                return redirect(url_for('main.apply_loan'))
            
            # Calculate EMI
            monthly_rate = interest_rate / 100 / 12
            emi = (requested_amount * monthly_rate * pow(1 + monthly_rate, tenure_months)) / (pow(1 + monthly_rate, tenure_months) - 1)
            
            # Calculate eligibility
            total_income = monthly_income + (co_applicant_income if co_applicant_income else 0)
            total_emi = existing_emi + emi
            emi_to_income_ratio = (total_emi / total_income) * 100
            
            # Determine application status based on eligibility
            if emi_to_income_ratio <= 40:
                application_status = 'Under Review'  # High chance of approval
            elif emi_to_income_ratio <= 50:
                application_status = 'Under Review'  # Moderate chance
            else:
                application_status = 'Pending'  # Needs manual review
            
            # Get customer's credit score if available
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT score FROM credit_scores 
                WHERE customer_id = %s 
                ORDER BY calculated_at DESC 
                LIMIT 1
            ''', (customer_id,))
            
            credit_score_row = cursor.fetchone()
            credit_score = credit_score_row[0] if credit_score_row else None
            
            # Insert loan application
            cursor.execute('''
                INSERT INTO loan_applications (
                    customer_id, loan_type, requested_amount, tenure_months, purpose,
                    employment_type, employer_name, monthly_income, existing_loans, existing_emi,
                    property_value, down_payment, co_applicant_name, co_applicant_income,
                    application_status, credit_score_at_application, calculated_emi,
                    approved_interest_rate
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            ''', (
                customer_id, loan_type, requested_amount, tenure_months, purpose,
                employment_type, employer_name, monthly_income, existing_loans, existing_emi,
                property_value, down_payment, co_applicant_name, co_applicant_income,
                application_status, credit_score, emi, interest_rate
            ))
            
            application_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            flash(f'Loan application submitted successfully! Application ID: {application_id}. We will review your application and get back to you soon.', 'success')
            return redirect(url_for('main.loans'))
            
        except ValueError as e:
            flash(f'Invalid input values: {str(e)}', 'error')
            return redirect(url_for('main.apply_loan'))
        except Exception as e:
            flash(f'Error submitting application: {str(e)}', 'error')
            return redirect(url_for('main.apply_loan'))
    
    # GET request - show application form
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get customer details
    cursor.execute('''
        SELECT full_name, email, phone, dob, address
        FROM customers
        WHERE customer_id = %s
    ''', (customer_id,))
    
    customer_row = cursor.fetchone()
    conn.close()
    
    if not customer_row:
        flash('Customer information not found.', 'error')
        return redirect(url_for('main.index'))
    
    customer = {
        'full_name': customer_row[0],
        'email': customer_row[1],
        'phone': customer_row[2],
        'dob': customer_row[3],
        'address': customer_row[4]
    }
    
    # Get loan type from query parameter (if coming from loans page)
    loan_type = request.args.get('type', '')
    
    return render_template('apply_loan.html', customer=customer, loan_type=loan_type)

@main_bp.route('/transaction_history')
def transaction_history():
    if 'customer_id' not in session:
        flash('Please sign in to access this feature.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']

    # Handle export requests
    export_format = request.args.get('export')
    if export_format:
        date_range = request.args.get('date_range', 'month')
        transaction_type = request.args.get('transaction_type', 'all')
        search_term = request.args.get('search', '').strip()
        return handle_export(customer_id, date_range, transaction_type, search_term, export_format)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get primary account balance
    cursor.execute('''
        SELECT balance FROM accounts
        WHERE customer_id = %s AND is_primary = TRUE AND status = 'Active'
        LIMIT 1
    ''', (customer_id,))

    primary_balance_row = cursor.fetchone()
    primary_balance = primary_balance_row[0] if primary_balance_row else 0.0

    # Get initial summary stats (for all time, no filters)
    cursor.execute('''
        SELECT
            SUM(CASE WHEN transaction_type = 'Credit' THEN amount ELSE 0 END) as total_credits,
            SUM(CASE WHEN transaction_type = 'Debit' THEN amount ELSE 0 END) as total_debits,
            COUNT(*) as total_transactions
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE a.customer_id = %s
    ''', (customer_id,))

    stats_row = cursor.fetchone()
    total_credits = float(stats_row[0] or 0.0)
    total_debits = float(stats_row[1] or 0.0)
    total_transactions = stats_row[2] or 0
    net_flow = total_credits - total_debits

    conn.close()

    summary_stats = {
        'total_credits': total_credits,
        'total_debits': total_debits,
        'total_transactions': total_transactions,
        'net_flow': net_flow
    }

    # Pass empty grouped_transactions since data will be loaded via AJAX
    grouped_transactions = {}

    return render_template('transaction_history.html',
                         available_balance=primary_balance,
                         summary_stats=summary_stats,
                         grouped_transactions=grouped_transactions)

def handle_export(customer_id, date_range, transaction_type, search_term, export_format):
    """Handle export functionality for transactions"""
    from flask import Response
    import csv
    import io

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build filters (same as above)
    date_filter = ""
    if date_range == 'today':
        date_filter = "AND t.transaction_date >= CURDATE()"
    elif date_range == 'week':
        date_filter = "AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    elif date_range == 'month':
        date_filter = "AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
    elif date_range == '3months':
        date_filter = "AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)"
    elif date_range == 'year':
        date_filter = "AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)"

    type_filter = ""
    if transaction_type != 'all':
        type_filter = f"AND t.transaction_type = '{transaction_type}'"

    search_filter = ""
    if search_term:
        search_filter = f"AND (t.merchant LIKE '%{search_term}%' OR t.category LIKE '%{search_term}%' OR t.description LIKE '%{search_term}%')"

    # Fetch all transactions for export (no pagination)
    cursor.execute(f'''
        SELECT t.transaction_date, t.transaction_type, t.amount,
               t.merchant, t.category, t.description
        FROM transactions t
        JOIN accounts a ON t.account_id = a.account_id
        WHERE a.customer_id = %s {date_filter} {type_filter} {search_filter}
        ORDER BY t.transaction_date DESC, t.transaction_id DESC
    ''', (customer_id,))

    transactions = cursor.fetchall()
    conn.close()

    if export_format == 'csv':
        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Type', 'Amount', 'Merchant', 'Category', 'Description'])

        for row in transactions:
            writer.writerow([
                row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else '',
                row[1],
                f"{row[2]:.2f}",
                row[3] or '',
                row[4] or '',
                row[5] or ''
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=transactions.csv'}
        )

    elif export_format == 'pdf':
        # For PDF export, we'll use a simple HTML to PDF approach
        # In a real app, you'd use a library like reportlab or weasyprint
        html_content = f"""
        <html>
        <head><title>Transaction History</title></head>
        <body>
        <h1>Transaction History</h1>
        <table border="1">
        <tr><th>Date</th><th>Type</th><th>Amount</th><th>Merchant</th><th>Category</th><th>Description</th></tr>
        """

        for row in transactions:
            html_content += f"""
            <tr>
            <td>{row[0].strftime('%Y-%m-%d %H:%M:%S') if row[0] else ''}</td>
            <td>{row[1]}</td>
            <td>₹{row[2]:.2f}</td>
            <td>{row[3] or ''}</td>
            <td>{row[4] or ''}</td>
            <td>{row[5] or ''}</td>
            </tr>
            """

        html_content += "</table></body></html>"

        return Response(
            html_content,
            mimetype='text/html',
            headers={'Content-Disposition': 'attachment; filename=transactions.html'}
        )

    return redirect(url_for('main.transaction_history'))

@main_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'customer_id' not in session:
        flash('Please sign in to access this feature.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']

    if request.method == 'POST':
        # Handle profile update
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        dob = request.form.get('dob')
        gender = request.form.get('gender')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Update customer profile information
            cursor.execute('''
                UPDATE customers
                SET full_name = %s, email = %s, phone = %s, address = %s, dob = %s, gender = %s
                WHERE customer_id = %s
            ''', (full_name, email, phone, address, dob, gender, customer_id))

            conn.commit()
            conn.close()

            # Update session data
            session['customer_name'] = full_name
            session['customer_email'] = email

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.profile'))

        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'error')
            return redirect(url_for('main.profile'))

    # GET request - fetch current profile data
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT full_name, email, phone, address, dob, gender, created_at FROM customers WHERE customer_id = %s', (customer_id,))
        customer_data = cursor.fetchone()
        conn.close()

        if customer_data:
            customer_profile = {
                'full_name': customer_data[0] or '',
                'email': customer_data[1] or '',
                'phone': customer_data[2] or '',
                'address': customer_data[3] or '',
                'dob': customer_data[4] or '',
                'gender': customer_data[5] or '',
                'created_at': customer_data[6]
            }
        else:
            customer_profile = {
                'full_name': session.get('customer_name', ''),
                'email': session.get('customer_email', ''),
                'phone': '',
                'address': '',
                'dob': '',
                'gender': '',
                'created_at': None
            }

    except Exception as e:
        customer_profile = {
            'full_name': session.get('customer_name', ''),
            'email': session.get('customer_email', ''),
            'phone': '',
            'address': '',
            'dob': '',
            'gender': '',
            'created_at': None
        }
        flash(f'Error loading profile: {str(e)}', 'error')

    return render_template('profile.html', profile=customer_profile)

@main_bp.route('/qr_pay', methods=['GET', 'POST'])
def qr_pay():
    if 'customer_id' not in session:
        flash('Please sign in to access this feature.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']

    if request.method == 'POST':
        # Handle QR code payment processing
        qr_data = request.form.get('qr_data')
        amount = request.form.get('amount')

        if not qr_data:
            flash('QR code data is required!', 'error')
            return redirect(url_for('main.qr_pay'))

        try:
            # Parse QR data (assuming format: account_number|ifsc|name|amount)
            qr_parts = qr_data.split('|')
            if len(qr_parts) < 3:
                flash('Invalid QR code format!', 'error')
                return redirect(url_for('main.qr_pay'))

            receiver_account = qr_parts[0]
            receiver_ifsc = qr_parts[1]
            receiver_name = qr_parts[2]
            qr_amount = qr_parts[3] if len(qr_parts) > 3 else amount

            if qr_amount:
                qr_amount = float(qr_amount)
            elif amount:
                qr_amount = float(amount)
            else:
                flash('Amount is required!', 'error')
                return redirect(url_for('main.qr_pay'))

            if qr_amount <= 0:
                flash('Amount must be greater than 0!', 'error')
                return redirect(url_for('main.qr_pay'))

            # Get user's primary account
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT account_id, balance FROM accounts WHERE customer_id = %s AND is_primary = TRUE AND status = "Active"', (customer_id,))
            account_row = cursor.fetchone()

            if not account_row:
                conn.close()
                flash('No active primary account found!', 'error')
                return redirect(url_for('main.qr_pay'))

            sender_account_id = account_row[0]
            sender_balance = account_row[1]

            if sender_balance < qr_amount:
                conn.close()
                flash('Insufficient balance!', 'error')
                return redirect(url_for('main.qr_pay'))

            # Verify receiver account exists
            cursor.execute('SELECT account_id FROM accounts WHERE account_number = %s AND status = "Active"', (receiver_account,))
            receiver_row = cursor.fetchone()

            if not receiver_row:
                conn.close()
                flash('Invalid receiver account!', 'error')
                return redirect(url_for('main.qr_pay'))

            receiver_account_id = receiver_row[0]

            # Generate reference number
            import uuid
            reference_number = f"QR{uuid.uuid4().hex[:12].upper()}"

            # Process payment with proper transaction handling
            try:
                # Ensure no active transaction before starting a new one
                conn.rollback()
                # Use explicit locking to prevent concurrent transactions
                conn.start_transaction()

                # Lock the sender account for update
                cursor.execute('SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE', (sender_account_id,))
                sender_balance_check = cursor.fetchone()

                if not sender_balance_check or sender_balance_check[0] < qr_amount:
                    conn.rollback()
                    flash('Insufficient balance or account locked!', 'error')
                    return redirect(url_for('main.qr_pay'))

                # Lock the receiver account for update
                cursor.execute('SELECT account_id FROM accounts WHERE account_id = %s FOR UPDATE', (receiver_account_id,))
                if not cursor.fetchone():
                    conn.rollback()
                    flash('Receiver account not available!', 'error')
                    return redirect(url_for('main.qr_pay'))

                # Debit sender
                cursor.execute('UPDATE accounts SET balance = balance - %s WHERE account_id = %s', (qr_amount, sender_account_id))

                # Credit receiver
                cursor.execute('UPDATE accounts SET balance = balance + %s WHERE account_id = %s', (qr_amount, receiver_account_id))

                # Record debit transaction for sender
                cursor.execute('''
                    INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, merchant, category, description, counterparty_account_id, counterparty_account_number, counterparty_bank_name, counterparty_ifsc_code, transfer_type, reference_number, status, initiated_at, completed_at)
                    VALUES (%s, NOW(), 'Debit', %s, 'QR Payment', 'Transfer', %s, %s, %s, %s, %s, 'UPI', %s, 'Completed', NOW(), NOW())
                ''', (sender_account_id, qr_amount, f'QR Payment to {receiver_name}', receiver_account_id, receiver_account, None, receiver_ifsc, reference_number))

                # Record credit transaction for receiver
                cursor.execute('''
                    INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, merchant, category, description, counterparty_account_id, counterparty_account_number, counterparty_bank_name, counterparty_ifsc_code, transfer_type, reference_number, status, initiated_at, completed_at)
                    VALUES (%s, NOW(), 'Credit', %s, 'QR Payment', 'Transfer', %s, %s, %s, %s, %s, 'UPI', %s, 'Completed', NOW(), NOW())
                ''', (receiver_account_id, qr_amount, f'Received QR payment', sender_account_id, None, None, None, reference_number))

                conn.commit()
                flash(f'QR Payment completed successfully! Reference: {reference_number}', 'success')

            except Exception as e:
                conn.rollback()
                flash(f'Payment failed: {str(e)}', 'error')

            finally:
                conn.close()

        except ValueError:
            flash('Invalid amount format!', 'error')
        except Exception as e:
            flash(f'Payment processing failed: {str(e)}', 'error')

        return redirect(url_for('main.qr_pay'))

    # GET request - show QR payment interface
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get user's primary account details
    cursor.execute('''
        SELECT a.account_number, a.account_type, c.full_name
        FROM accounts a
        JOIN customers c ON a.customer_id = c.customer_id
        WHERE a.customer_id = %s AND a.is_primary = TRUE AND a.status = 'Active'
    ''', (customer_id,))

    account_row = cursor.fetchone()
    conn.close()

    if not account_row:
        flash('No active primary account found.', 'error')
        return redirect(url_for('main.index'))

    account_number = account_row[0]
    account_type = account_row[1]
    customer_name = account_row[2]

    # Generate QR code data
    qr_data = f"{account_number}|{account_type}|{customer_name}"

    # Generate QR code image
    import qrcode
    import base64
    import io

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render_template('qr_pay.html',
                         account_number=account_number,
                         account_type=account_type,
                         customer_name=customer_name,
                         qr_code_base64=qr_code_base64)

@main_bp.route('/check_credit_score')
def check_credit_score():
    if 'customer_id' not in session:
        flash('Please sign in to access this feature.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']

    # First check if there's a recent prediction in the database
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT score, decision, confidence, shap_values, created_at
        FROM predictions
        WHERE customer_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    ''', (customer_id,))

    prediction_row = cursor.fetchone()
    conn.close()

    if prediction_row:
        # Use the saved prediction from database
        score, decision, confidence, shap_values_json, created_at = prediction_row
        import json
        shap_values = json.loads(shap_values_json) if shap_values_json else []

        credit_score = {
            'score': float(score),
            'decision': decision,
            'calculated_at': created_at,
            'confidence': float(confidence),
            'shap_values': {item['feature']: item['value'] for item in shap_values}
        }
    else:
        # No saved prediction, try to generate new one
        prediction_result = predict_credit_score(customer_id)

        if prediction_result and prediction_result['data_sufficiency']:
            # Format for template compatibility
            credit_score = {
                'score': prediction_result['predicted_score'],
                'decision': 'Approved' if prediction_result['predicted_score'] >= 650 else 'Review' if prediction_result['predicted_score'] >= 600 else 'Declined',
                'calculated_at': datetime.now(),  # Current timestamp
                'confidence': 0.85,  # Default confidence
                'shap_values': {exp['factor']: 0.1 if exp['impact'] == 'positive' else -0.1
                              for exp in prediction_result['explanations'][:5]},  # Mock SHAP values for display
                'improvement_tips': prediction_result['improvement_tips']  # Add improvement tips
            }
        elif prediction_result and not prediction_result['data_sufficiency']:
            # Insufficient data, use fallback based on customer's stored credit score
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT score FROM credit_scores WHERE customer_id = %s ORDER BY calculated_at DESC LIMIT 1', (customer_id,))
            credit_score_row = cursor.fetchone()
            conn.close()

            if credit_score_row and credit_score_row[0]:
                stored_credit_score = credit_score_row[0]
                if stored_credit_score >= 750:
                    score = 780.5
                    decision = 'Approved'
                    confidence = 0.92
                elif stored_credit_score >= 650:
                    score = 720.5
                    decision = 'Approved'
                    confidence = 0.85
                elif stored_credit_score >= 600:
                    score = 650.0
                    decision = 'Review'
                    confidence = 0.65
                else:
                    score = 580.0
                    decision = 'Declined'
                    confidence = 0.45

                shap_values = [
                    {'feature': 'Income', 'value': 0.15},
                    {'feature': 'Credit History', 'value': 0.12},
                    {'feature': 'Debt-to-Income Ratio', 'value': -0.08},
                    {'feature': 'Employment Length', 'value': 0.06},
                    {'feature': 'Age', 'value': 0.03}
                ]

                credit_score = {
                    'score': score,
                    'decision': decision,
                    'calculated_at': datetime.now(),
                    'confidence': confidence,
                    'shap_values': {item['feature']: item['value'] for item in shap_values}
                }
            else:
                # No stored credit score available, show -1
                credit_score = {
                    'score': -1,
                    'decision': 'Insufficient Data',
                    'calculated_at': datetime.now(),
                    'confidence': 0.0,
                    'shap_values': {}
                }
        else:
            # Prediction failed completely, show -1
            credit_score = {
                'score': -1,
                'decision': 'Insufficient Data',
                'calculated_at': datetime.now(),
                'confidence': 0.0,
                'shap_values': {}
            }

    return render_template('check_credit_score.html', credit_score=credit_score, customer_id=customer_id)

@main_bp.route('/loan_history')
def loan_history():
    if 'customer_id' not in session:
        flash('Please sign in to access this feature.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get user's approved loans (both disbursed and approved applications)
    loan_history_data = []

    # First, get disbursed loans from loans table
    cursor.execute('''
        SELECT l.loan_id, l.loan_type, l.principal_amount, l.interest_rate, l.issue_date,
               l.due_date, l.status, NULL as application_id, NULL as approved_amount,
               NULL as approved_interest_rate, NULL as approved_tenure_months,
               NULL as calculated_emi, NULL as applied_date, 'disbursed' as source
        FROM loans l
        WHERE l.customer_id = %s
        ORDER BY l.issue_date DESC
    ''', (customer_id,))

    disbursed_loans = cursor.fetchall()

    for loan_row in disbursed_loans:
        loan_id = loan_row[0]

        # Get payments for this loan
        cursor.execute('''
            SELECT payment_date, amount_paid, payment_status
            FROM payments
            WHERE loan_id = %s
            ORDER BY payment_date DESC
        ''', (loan_id,))

        payments = cursor.fetchall()

        # Calculate loan details
        principal = float(loan_row[2] or 0)
        interest_rate = float(loan_row[3] or 0)
        tenure_months = 0  # Will be calculated from payments if needed
        emi = 0.0

        # Calculate total paid and remaining
        total_paid = sum(float(p[1]) for p in payments if p[2] == 'On-Time' or p[2] == 'Late')
        remaining_balance = principal - total_paid

        # Calculate next payment date (simplified - monthly from issue date)
        from datetime import datetime, timedelta
        issue_date = loan_row[4]
        if issue_date:
            months_passed = (datetime.now().date() - issue_date).days // 30
            next_payment_date = issue_date + timedelta(days=(months_passed + 1) * 30)
        else:
            next_payment_date = None

        loan_dict = {
            'loan_id': f"L{loan_id}",
            'loan_type': loan_row[1],
            'principal_amount': principal,
            'interest_rate': interest_rate,
            'issue_date': loan_row[4],
            'due_date': loan_row[5],
            'status': loan_row[6],
            'approved_amount': principal,
            'approved_tenure_months': tenure_months,
            'calculated_emi': emi,
            'applied_date': None,
            'payments': [{
                'payment_date': p[0],
                'amount_paid': float(p[1]),
                'payment_status': p[2]
            } for p in payments],
            'total_paid': total_paid,
            'total_interest_paid': 0.0,  # Simplified calculation
            'remaining_balance': max(0, remaining_balance),
            'next_payment_date': next_payment_date,
            'payments_made': len([p for p in payments if p[2] == 'On-Time' or p[2] == 'Late']),
            'total_payments_due': tenure_months,
            'source': 'disbursed'
        }

        loan_history_data.append(loan_dict)

    # Second, get approved loan applications that haven't been disbursed yet
    cursor.execute('''
        SELECT application_id, loan_type, approved_amount, approved_interest_rate,
               approved_tenure_months, calculated_emi, applied_date, reviewed_date
        FROM loan_applications
        WHERE customer_id = %s AND application_status = 'Approved'
        ORDER BY applied_date DESC
    ''', (customer_id,))

    approved_applications = cursor.fetchall()

    for app_row in approved_applications:
        application_id = app_row[0]

        # Check if this application has already been disbursed
        cursor.execute('''
            SELECT loan_id FROM loans
            WHERE customer_id = %s AND loan_type = %s
        ''', (customer_id, app_row[1]))

        if cursor.fetchone():
            continue  # Skip if already disbursed

        # Generate future repayment schedule
        principal = float(app_row[2] or 0)
        interest_rate = float(app_row[3] or 0)
        tenure_months = app_row[4] or 0
        emi = float(app_row[5] or 0)

        # Generate future payments (upcoming EMIs)
        future_payments = []
        from datetime import datetime, timedelta

        applied_date = app_row[6]
        if applied_date:
            current_date = datetime.now().date()
            for month in range(1, tenure_months + 1):
                payment_date = applied_date + timedelta(days=month * 30)
                if payment_date >= current_date:
                    future_payments.append({
                        'payment_date': payment_date,
                        'amount_paid': emi,
                        'payment_status': 'Upcoming'
                    })

        loan_dict = {
            'loan_id': f"APP{application_id}",
            'loan_type': app_row[1],
            'principal_amount': principal,
            'interest_rate': interest_rate,
            'issue_date': None,
            'due_date': None,
            'status': 'Approved',
            'approved_amount': principal,
            'approved_tenure_months': tenure_months,
            'calculated_emi': emi,
            'applied_date': app_row[6],
            'payments': future_payments,
            'total_paid': 0.0,
            'total_interest_paid': 0.0,
            'remaining_balance': principal,
            'next_payment_date': future_payments[0]['payment_date'] if future_payments else None,
            'payments_made': 0,
            'total_payments_due': tenure_months,
            'source': 'application'
        }

        loan_history_data.append(loan_dict)

    # Also include pending/under review applications
    cursor.execute('''
        SELECT application_id, loan_type, requested_amount, NULL as approved_interest_rate,
               tenure_months, calculated_emi, applied_date, reviewed_date, application_status
        FROM loan_applications
        WHERE customer_id = %s AND application_status IN ('Pending', 'Under Review')
        ORDER BY applied_date DESC
    ''', (customer_id,))

    pending_applications = cursor.fetchall()

    for app_row in pending_applications:
        application_id = app_row[0]

        loan_dict = {
            'loan_id': f"PENDING{application_id}",
            'loan_type': app_row[1],
            'principal_amount': float(app_row[2] or 0),
            'interest_rate': 0.0,
            'issue_date': None,
            'due_date': None,
            'status': app_row[8],
            'approved_amount': float(app_row[2] or 0),
            'approved_tenure_months': app_row[4] or 0,
            'calculated_emi': float(app_row[5] or 0),
            'applied_date': app_row[6],
            'payments': [],
            'total_paid': 0.0,
            'total_interest_paid': 0.0,
            'remaining_balance': float(app_row[2] or 0),
            'next_payment_date': None,
            'payments_made': 0,
            'total_payments_due': app_row[4] or 0,
            'source': 'pending'
        }

        loan_history_data.append(loan_dict)

    conn.close()

    # Sort by applied/issued date (most recent first)
    def get_sort_date(x):
        date_val = x.get('applied_date') or x.get('issue_date')
        if date_val:
            if isinstance(date_val, date):
                return datetime.combine(date_val, datetime.min.time())
            else:
                return date_val
        return datetime.min

    loan_history_data.sort(key=get_sort_date, reverse=True)

    # Calculate summary statistics
    total_loans = len([l for l in loan_history_data if l['source'] == 'disbursed'])
    active_loans = len([l for l in loan_history_data if l['status'] == 'Active'])
    approved_applications = len([l for l in loan_history_data if l['source'] == 'application'])
    pending_applications = len([l for l in loan_history_data if l['source'] == 'pending'])

    total_principal = sum(l['principal_amount'] for l in loan_history_data)
    total_paid = sum(l['total_paid'] for l in loan_history_data)
    total_remaining = sum(l['remaining_balance'] for l in loan_history_data)

    summary = {
        'total_loans': total_loans,
        'active_loans': active_loans,
        'approved_applications': approved_applications,
        'pending_applications': pending_applications,
        'total_principal': total_principal,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
        'total_interest_paid': sum(l['total_interest_paid'] for l in loan_history_data)
    }

    return render_template('loan_history.html', loans=loan_history_data, summary=summary)

@main_bp.route('/mobile_transfer', methods=['GET', 'POST'])
def mobile_transfer():
    if 'customer_id' not in session:
        flash('Please sign in to access this feature.', 'error')
        return redirect(url_for('main.signin'))

    customer_id = session['customer_id']

    # Get user's accounts for mobile transfer
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT account_id, account_number, account_type, balance
        FROM accounts
        WHERE customer_id = %s AND status = 'Active'
        ORDER BY account_type
    ''', (customer_id,))

    accounts = cursor.fetchall()
    conn.close()

    # Convert to dicts for template
    accounts_list = []
    for row in accounts:
        accounts_list.append({
            'account_id': row[0],
            'account_number': row[1],
            'account_type': row[2],
            'balance': row[3]
        })

    if request.method == 'POST':
        # Handle mobile transfer
        selected_receiver_id = request.form.get('selectedReceiverId')
        amount = request.form.get('amount')
        sender_account = request.form.get('sender_account')
        password = request.form.get('password')

        if not all([selected_receiver_id, amount, sender_account, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('main.mobile_transfer'))

        try:
            amount = float(amount)
            sender_account_id = int(sender_account)
            receiver_customer_id = int(selected_receiver_id)

            # Verify password
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT password_hash FROM customers WHERE customer_id = %s', (customer_id,))
            user_row = cursor.fetchone()

            if not user_row or not bcrypt.checkpw(password.encode('utf-8'), user_row[0].encode('utf-8')):
                conn.close()
                flash('Invalid password', 'error')
                return redirect(url_for('main.mobile_transfer'))

            # Get sender account details
            cursor.execute('SELECT balance FROM accounts WHERE account_id = %s AND customer_id = %s AND status = "Active"', (sender_account_id, customer_id))
            sender_row = cursor.fetchone()

            if not sender_row:
                conn.close()
                flash('Invalid sender account', 'error')
                return redirect(url_for('main.mobile_transfer'))

            sender_balance = sender_row[0]

            if sender_balance < amount:
                conn.close()
                flash('Insufficient balance', 'error')
                return redirect(url_for('main.mobile_transfer'))

            # Get receiver's primary account
            cursor.execute('SELECT account_id FROM accounts WHERE customer_id = %s AND status = "Active" AND is_primary = TRUE', (receiver_customer_id,))
            receiver_row = cursor.fetchone()

            if not receiver_row:
                conn.close()
                flash('Receiver primary account not found', 'error')
                return redirect(url_for('main.mobile_transfer'))

            receiver_account_id = receiver_row[0]

            # Generate reference number
            import uuid
            reference_number = f"MOBILE{uuid.uuid4().hex[:12].upper()}"

            # Process transfer with proper transaction handling
            try:
                # Ensure no active transaction before starting a new one
                conn.rollback()
                # Use explicit locking to prevent concurrent transactions
                conn.start_transaction()

                # Lock the sender account for update
                cursor.execute('SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE', (sender_account_id,))
                sender_balance_check = cursor.fetchone()

                if not sender_balance_check or sender_balance_check[0] < amount:
                    conn.rollback()
                    flash('Insufficient balance or account locked!', 'error')
                    return redirect(url_for('main.mobile_transfer'))

                # Lock the receiver account for update
                cursor.execute('SELECT account_id FROM accounts WHERE account_id = %s FOR UPDATE', (receiver_account_id,))
                if not cursor.fetchone():
                    conn.rollback()
                    flash('Receiver account not available!', 'error')
                    return redirect(url_for('main.mobile_transfer'))

                # Debit sender
                cursor.execute('UPDATE accounts SET balance = balance - %s WHERE account_id = %s', (amount, sender_account_id))

                # Credit receiver
                cursor.execute('UPDATE accounts SET balance = balance + %s WHERE account_id = %s', (amount, receiver_account_id))

                # Record transfer in transactions table
                cursor.execute('''
                    INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, merchant, category, description, counterparty_account_id, counterparty_account_number, counterparty_bank_name, counterparty_ifsc_code, transfer_type, reference_number, status, initiated_at, completed_at)
                    VALUES (%s, NOW(), 'Debit', %s, 'Mobile Transfer', 'Transfer', %s, %s, NULL, NULL, NULL, 'MOBILE', %s, 'Completed', NOW(), NOW())
                ''', (sender_account_id, amount, f'Mobile transfer to customer {receiver_customer_id}', receiver_account_id, reference_number))

                cursor.execute('''
                    INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, merchant, category, description, counterparty_account_id, counterparty_account_number, counterparty_bank_name, counterparty_ifsc_code, transfer_type, reference_number, status, initiated_at, completed_at)
                    VALUES (%s, NOW(), 'Credit', %s, 'Mobile Transfer', 'Transfer', %s, %s, NULL, NULL, NULL, 'MOBILE', %s, 'Completed', NOW(), NOW())
                ''', (receiver_account_id, amount, f'Received mobile transfer from customer {customer_id}', sender_account_id, reference_number))

                conn.commit()
                flash(f'Transfer completed successfully! Reference: {reference_number}', 'success')

            except Exception as e:
                conn.rollback()
                flash(f'Transfer failed: {str(e)}', 'error')

            finally:
                conn.close()

        except ValueError:
            flash('Invalid amount format', 'error')
        except Exception as e:
            flash(f'Transfer processing failed: {str(e)}', 'error')

        return redirect(url_for('main.mobile_transfer'))

    return render_template('mobile_transfer.html', accounts=accounts_list)
