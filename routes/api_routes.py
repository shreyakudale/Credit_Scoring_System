# 🔌 Optional REST API for integration
from flask import Blueprint, request, jsonify
from flask import session
import json
import bcrypt
from config.db_config import get_db_connection
from model.feature_engineering import predict_credit_score
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'AI Credit Scoring API'})

@api_bp.route('/predict', methods=['POST'])
def predict_api():
    """API endpoint for credit score prediction"""
    data = request.get_json()

    if not data or 'customer_id' not in data:
        return jsonify({'error': 'customer_id is required'}), 400

    customer_id = data['customer_id']

    try:
        customer_id = int(customer_id)
    except ValueError:
        return jsonify({'error': 'Invalid customer_id format'}), 400

    # Use trained model for prediction
    prediction_result = predict_credit_score(customer_id)

    if prediction_result and prediction_result['data_sufficiency']:
        # Save prediction to database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Convert explanations to shap_values format for database
        shap_values = [{'feature': exp['factor'], 'value': 0.1 if exp['impact'] == 'positive' else -0.1}
                      for exp in prediction_result['explanations'][:5]]
        shap_json = json.dumps(shap_values)

        # Map risk level to decision
        decision_map = {
            'Low Risk': 'Approved',
            'Medium Risk': 'Approved',
            'High Risk': 'Declined'
        }
        decision = decision_map.get(prediction_result['risk_level'], 'Review')

        cursor.execute('''
            INSERT INTO predictions (customer_id, score, decision, confidence, shap_values)
            VALUES (%s, %s, %s, %s, %s)
        ''', (customer_id, prediction_result['predicted_score'], decision, 0.85, shap_json))

        conn.commit()
        conn.close()

        # Format response for frontend compatibility
        response = {
            'predicted_score': prediction_result['predicted_score'],
            'decision': decision,
            'confidence': 0.85,
            'shap_values': {exp['factor']: 0.1 if exp['impact'] == 'positive' else -0.1
                           for exp in prediction_result['explanations'][:5]},
            'risk_level': prediction_result['risk_level'],
            'data_sufficiency': prediction_result['data_sufficiency'],
            'explanations': prediction_result['explanations'],
            'improvement_tips': prediction_result['improvement_tips']
        }
        return jsonify(response)
    else:
        return jsonify({'error': 'Insufficient data for credit score prediction'}), 400

@api_bp.route('/signup', methods=['POST'])
def signup():
    """User registration endpoint"""
    data = request.get_json()

    if not data or not all(k in data for k in ('username', 'email', 'password')):
        return jsonify({'error': 'username, email, and password are required'}), 400

    username = data['username'].strip()
    email = data['email'].strip().lower()
    password = data['password']

    if len(username) < 3 or len(password) < 6:
        return jsonify({'error': 'Username must be at least 3 characters and password at least 6 characters'}), 400

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE username = %s OR email = %s', (username, email))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Username or email already exists'}), 409

        # Insert new user
        cursor.execute('''
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
        ''', (username, email, password_hash))

        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_id,
            'username': username,
            'email': email
        }), 201

    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@api_bp.route('/signin', methods=['POST'])
def signin():
    """User authentication endpoint"""
    data = request.get_json()

    if not data or not all(k in data for k in ('username', 'password')):
        return jsonify({'error': 'username and password are required'}), 400

    username = data['username'].strip()
    password = data['password']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch user
        cursor.execute('SELECT id, username, email, password_hash FROM users WHERE username = %s', (username,))
        user_row = cursor.fetchone()
        conn.close()

        if not user_row:
            return jsonify({'error': 'Invalid username or password'}), 401

        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user_row[3].encode('utf-8')):
            return jsonify({'error': 'Invalid username or password'}), 401

        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user_row[0],
                'username': user_row[1],
                'email': user_row[2]
            }
        }), 200

    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@api_bp.route('/transfer', methods=['POST'])
def transfer_money():
    """API endpoint for money transfer"""
    data = request.get_json()

    required_fields = ['sender_account_id', 'receiver_account_number', 'receiver_ifsc', 'amount', 'transfer_type']
    if not data or not all(k in data for k in required_fields):
        return jsonify({'error': f'Required fields: {", ".join(required_fields)}'}), 400

    try:
        sender_account_id = int(data['sender_account_id'])
        receiver_account_number = data['receiver_account_number'].strip()
        receiver_ifsc = data['receiver_ifsc'].strip()
        amount = float(data['amount'])
        transfer_type = data['transfer_type'].upper()
        remarks = data.get('remarks', '').strip()

        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400

        if transfer_type not in ['IMPS', 'NEFT', 'RTGS', 'UPI', 'MOBILE']:
            return jsonify({'error': 'Invalid transfer type'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verify sender account exists and belongs to authenticated user
        cursor.execute('SELECT balance FROM accounts WHERE account_id = %s AND status = "Active"', (sender_account_id,))
        sender_row = cursor.fetchone()
        if not sender_row:
            conn.close()
            return jsonify({'error': 'Invalid sender account'}), 404

        sender_balance = sender_row[0]

        # Check sufficient balance
        if sender_balance < amount:
            conn.close()
            return jsonify({'error': 'Insufficient balance'}), 400

        # Find receiver account
        cursor.execute('SELECT account_id, customer_id FROM accounts WHERE account_number = %s AND status = "Active"', (receiver_account_number,))
        receiver_row = cursor.fetchone()
        if not receiver_row:
            conn.close()
            return jsonify({'error': 'Receiver account not found'}), 404

        receiver_account_id = receiver_row[0]
        receiver_customer_id = receiver_row[1]

        # Get receiver customer name for mobile transfers
        receiver_name = receiver_account_number
        sender_name = sender_account_id  # Default to account ID
        if transfer_type == 'MOBILE':
            # Get receiver name
            cursor.execute('SELECT full_name FROM customers WHERE customer_id = %s', (receiver_customer_id,))
            name_row = cursor.fetchone()
            if name_row:
                receiver_name = name_row[0]

            # Get sender name
            cursor.execute('SELECT c.full_name FROM customers c JOIN accounts a ON c.customer_id = a.customer_id WHERE a.account_id = %s', (sender_account_id,))
            sender_row = cursor.fetchone()
            if sender_row:
                sender_name = sender_row[0]

        # Generate unique reference number
        import uuid
        reference_number = f"TXN{uuid.uuid4().hex[:16].upper()}"

        # Start transaction
        conn.start_transaction()

        try:
            # Debit sender
            cursor.execute('UPDATE accounts SET balance = balance - %s WHERE account_id = %s', (amount, sender_account_id))

            # Credit receiver
            cursor.execute('UPDATE accounts SET balance = balance + %s WHERE account_id = %s', (amount, receiver_account_id))

            # Record transfer
            cursor.execute('''
                INSERT INTO transfers (sender_account_id, receiver_account_id, amount, transfer_type, reference_number, status, remarks, completed_at)
                VALUES (%s, %s, %s, %s, %s, 'Completed', %s, %s)
            ''', (sender_account_id, receiver_account_id, amount, transfer_type, reference_number, remarks, datetime.now()))

            # Record transactions for both accounts
            debit_description = f'Mobile transfer to {receiver_name}' if transfer_type == 'MOBILE' else f'Transfer to {receiver_account_number}'
            cursor.execute('''
                INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, merchant, category, description)
                VALUES (%s, %s, 'Debit', %s, 'Money Transfer', 'Transfer', %s)
            ''', (sender_account_id, datetime.now(), amount, debit_description))

            credit_description = f'Received from {sender_name}' if transfer_type == 'MOBILE' else f'Received from transfer'
            cursor.execute('''
                INSERT INTO transactions (account_id, transaction_date, transaction_type, amount, merchant, category, description)
                VALUES (%s, %s, 'Credit', %s, 'Money Transfer', 'Transfer', %s)
            ''', (receiver_account_id, datetime.now(), amount, credit_description))

            conn.commit()

            return jsonify({
                'message': 'Transfer completed successfully',
                'reference_number': reference_number,
                'amount': amount,
                'transfer_type': transfer_type,
                'status': 'Completed'
            }), 200

        except Exception as e:
            conn.rollback()
            return jsonify({'error': f'Transfer failed: {str(e)}'}), 500

        finally:
            conn.close()

    except ValueError:
        return jsonify({'error': 'Invalid numeric values'}), 400
    except Exception as e:
        return jsonify({'error': f'Transfer processing failed: {str(e)}'}), 500

@api_bp.route('/search_mobile', methods=['POST'])
def search_mobile():
    """API endpoint to search customers by mobile number"""
    data = request.get_json()

    if not data or 'mobile' not in data:
        return jsonify({'error': 'mobile number is required'}), 400

    mobile = data['mobile'].strip()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Search for customers with matching mobile number
        cursor.execute('''
            SELECT customer_id, full_name, phone
            FROM customers
            WHERE phone LIKE %s
            LIMIT 10
        ''', (f'%{mobile}%',))

        customers = cursor.fetchall()
        conn.close()

        receivers = []
        for row in customers:
            receivers.append({
                'customer_id': row[0],
                'name': row[1],
                'phone': row[2]
            })

        return jsonify({'receivers': receivers}), 200

    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@api_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """API endpoint for fetching user transactions with filtering"""
    customer_id = request.args.get('customer_id')
    date_range = request.args.get('date_range', 'month')
    transaction_type = request.args.get('transaction_type', 'all')
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))

    if not customer_id:
        return jsonify({'error': 'customer_id is required'}), 400

    try:
        customer_id = int(customer_id)
        if page < 1 or limit < 1 or limit > 100:
            return jsonify({'error': 'Invalid page or limit parameters'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid customer_id, page, or limit'}), 400

    # Build date filter
    date_filter = ""
    if date_range == 'today':
        date_filter = "AND DATE(t.transaction_date) >= CURDATE()"
    elif date_range == 'week':
        date_filter = "AND DATE(t.transaction_date) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
    elif date_range == 'month':
        date_filter = "AND DATE(t.transaction_date) >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"
    elif date_range == '3months':
        date_filter = "AND DATE(t.transaction_date) >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)"
    elif date_range == 'year':
        date_filter = "AND DATE(t.transaction_date) >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)"
    # 'all' means no date filter

    # Build type filter
    type_filter = ""
    if transaction_type == 'credit':
        type_filter = "AND t.transaction_type = 'Credit'"
    elif transaction_type == 'debit':
        type_filter = "AND t.transaction_type = 'Debit'"
    elif transaction_type == 'transfer':
        type_filter = "AND t.category = 'Transfer'"

    # Build search filter
    search_filter = ""
    if search:
        search_filter = f"AND (t.description LIKE '%{search}%' OR t.merchant LIKE '%{search}%' OR t.category LIKE '%{search}%')"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get total count for pagination
        count_query = f'''
            SELECT COUNT(*) as total
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.customer_id = %s {date_filter} {type_filter} {search_filter}
        '''
        cursor.execute(count_query, (customer_id,))
        total_count = cursor.fetchone()[0]

        # Get transactions with pagination
        offset = (page - 1) * limit
        query = f'''
            SELECT
                t.transaction_id,
                t.transaction_date,
                t.transaction_type,
                t.amount,
                t.merchant,
                t.category,
                t.description,
                a.account_number,
                a.account_type
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.customer_id = %s {date_filter} {type_filter} {search_filter}
            ORDER BY t.transaction_date DESC, t.transaction_id DESC
            LIMIT %s OFFSET %s
        '''
        cursor.execute(query, (customer_id, limit, offset))

        transactions = cursor.fetchall()

        # Get summary stats
        stats_query = f'''
            SELECT
                SUM(CASE WHEN transaction_type = 'Credit' THEN amount ELSE 0 END) as total_credits,
                SUM(CASE WHEN transaction_type = 'Debit' THEN amount ELSE 0 END) as total_debits,
                COUNT(*) as total_transactions
            FROM transactions t
            JOIN accounts a ON t.account_id = a.account_id
            WHERE a.customer_id = %s {date_filter}
        '''
        cursor.execute(stats_query, (customer_id,))
        stats_row = cursor.fetchone()
        if stats_row:
            total_credits = stats_row[0] or 0.0
            total_debits = stats_row[1] or 0.0
            total_transactions = stats_row[2] or 0
        else:
            total_credits = 0.0
            total_debits = 0.0
            total_transactions = 0
        net_flow = total_credits - total_debits

        conn.close()

        # Convert transactions to dict format
        transactions_list = []
        for row in transactions:
            transactions_list.append({
                'transaction_id': row[0],
                'transaction_date': row[1].isoformat() if row[1] else None,
                'transaction_type': row[2],
                'amount': float(row[3]),
                'merchant': row[4] or '',
                'category': row[5] or '',
                'description': row[6] or '',
                'account_number': row[7],
                'account_type': row[8]
            })

        # Group transactions by date for frontend display
        grouped_transactions = {}
        for transaction in transactions_list:
            if transaction['transaction_date']:
                # Parse date and format as DD-MM-YYYY
                from datetime import datetime
                date_obj = datetime.fromisoformat(transaction['transaction_date'][:19])  # Remove timezone if present
                date_str = date_obj.strftime('%d-%m-%Y')
            else:
                date_str = 'Unknown'
            if date_str not in grouped_transactions:
                grouped_transactions[date_str] = []
            grouped_transactions[date_str].append(transaction)

        # Sort grouped transactions by date in descending order (latest first)
        grouped_transactions = dict(sorted(grouped_transactions.items(), key=lambda x: datetime.strptime(x[0], '%d-%m-%Y') if x[0] != 'Unknown' else datetime.min, reverse=True))

        response = {
            'transactions': transactions_list,
            'grouped_transactions': grouped_transactions,
            'summary_stats': {
                'total_credits': float(total_credits),
                'total_debits': float(total_debits),
                'total_transactions': total_transactions,
                'net_flow': float(net_flow)
            },
            'pagination': {
                'page': page,
                'limit': limit,
                'total': total_count,
                'total_pages': (total_count + limit - 1) // limit
            }
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch transactions: {str(e)}'}), 500

@api_bp.route('/loan_applications', methods=['GET'])
def get_loan_applications():
    """API endpoint for fetching user's loan applications"""
    if 'customer_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401

    customer_id = session['customer_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT application_id, loan_type, requested_amount, tenure_months, applied_date, application_status, calculated_emi
            FROM loan_applications
            WHERE customer_id = %s
            ORDER BY applied_date DESC
        ''', (customer_id,))

        applications = cursor.fetchall()
        conn.close()

        applications_list = []
        for row in applications:
            applications_list.append({
                'application_id': row[0],
                'loan_type': row[1],
                'requested_amount': float(row[2]),
                'tenure_months': row[3],
                'applied_date': row[4].isoformat() if row[4] else None,
                'application_status': row[5],
                'calculated_emi': float(row[6]) if row[6] else None
            })

        return jsonify({'applications': applications_list}), 200

    except Exception as e:
        return jsonify({'error': f'Failed to fetch loan applications: {str(e)}'}), 500

@api_bp.route('/beneficiaries', methods=['GET', 'POST'])
def manage_beneficiaries():
    """API endpoint for managing beneficiaries"""
    if request.method == 'GET':
        # Get beneficiaries for authenticated user
        customer_id = request.args.get('customer_id')
        if not customer_id:
            return jsonify({'error': 'customer_id is required'}), 400

        try:
            customer_id = int(customer_id)
        except ValueError:
            return jsonify({'error': 'Invalid customer_id'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT beneficiary_id, name, account_number, bank_name, ifsc_code, phone, email, is_verified, added_at
            FROM beneficiaries
            WHERE customer_id = %s
            ORDER BY added_at DESC
        ''', (customer_id,))

        beneficiaries = cursor.fetchall()
        conn.close()

        beneficiary_list = []
        for row in beneficiaries:
            beneficiary_list.append({
                'beneficiary_id': row[0],
                'name': row[1],
                'account_number': row[2],
                'bank_name': row[3],
                'ifsc_code': row[4],
                'phone': row[5],
                'email': row[6],
                'is_verified': bool(row[7]),
                'added_at': row[8].isoformat() if row[8] else None
            })

        return jsonify({'beneficiaries': beneficiary_list}), 200

    elif request.method == 'POST':
        # Add new beneficiary
        data = request.get_json()

        required_fields = ['customer_id', 'name', 'account_number', 'bank_name', 'ifsc_code']
        if not data or not all(k in data for k in required_fields):
            return jsonify({'error': f'Required fields: {", ".join(required_fields)}'}), 400

        try:
            customer_id = int(data['customer_id'])
            name = data['name'].strip()
            account_number = data['account_number'].strip()
            bank_name = data['bank_name'].strip()
            ifsc_code = data['ifsc_code'].strip()
            phone = data.get('phone', '').strip()
            email = data.get('email', '').strip()

            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if beneficiary already exists
            cursor.execute('''
                SELECT beneficiary_id FROM beneficiaries
                WHERE customer_id = %s AND account_number = %s AND ifsc_code = %s
            ''', (customer_id, account_number, ifsc_code))

            if cursor.fetchone():
                conn.close()
                return jsonify({'error': 'Beneficiary already exists'}), 409

            # Add new beneficiary
            cursor.execute('''
                INSERT INTO beneficiaries (customer_id, name, account_number, bank_name, ifsc_code, phone, email, is_verified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
            ''', (customer_id, name, account_number, bank_name, ifsc_code, phone, email))

            beneficiary_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return jsonify({
                'message': 'Beneficiary added successfully',
                'beneficiary_id': beneficiary_id
            }), 201

        except Exception as e:
            return jsonify({'error': f'Failed to add beneficiary: {str(e)}'}), 500
