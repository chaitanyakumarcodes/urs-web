from flask import render_template, request, jsonify, session, redirect, url_for, flash, make_response
from firebase_config import db
from app import app
import pandas as pd
from io import StringIO, BytesIO
import pdfkit
from datetime import datetime, timedelta
import csv
import os
from pathlib import Path
import bcrypt

# # Configure wkhtmltopdf path
# WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
# config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

@app.route('/')
def index():
    if 'vendor_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Query Firestore for vendor
        vendors_ref = db.collection('vendors')
        vendor_docs = vendors_ref.where('email', '==', email).stream()

        # Check if vendor exists
        vendor = None
        for doc in vendor_docs:
            vendor = doc.to_dict()
            vendor['id'] = doc.id  # Add the document ID to the vendor dictionary
            break  # Exit loop after finding the first match

        if not vendor:
            return render_template('login.html', error="Invalid credentials")

        hashed_password = vendor['password']

        # Verify the password using bcrypt
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            session['vendor_id'] = vendor['id']  # Use the document ID
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('vendor_id', None)
    return redirect(url_for('login'))

@app.route('/business-model')
def business_model():
    if 'temp_vendor_id' not in session:
        return redirect(url_for('register'))
    return render_template('business_model.html')

@app.route('/business-model-confirmation')
def business_model_confirmation():
    if 'temp_vendor_id' not in session:
        return redirect(url_for('register'))
    return render_template('business_model_confirmation.html')

@app.route('/confirm-registration', methods=['POST'])
def confirm_registration():
    if 'temp_vendor_id' not in session:
        return redirect(url_for('register'))
    
    choice = request.form.get('choice')
    vendor_id = session.pop('temp_vendor_id')  # Remove temporary session
    
    if choice == 'accept':
        session['vendor_id'] = vendor_id  # Set permanent session
        flash('Welcome to URS! You can now start using the system.', 'success')
        return redirect(url_for('dashboard'))
    else:
        # Delete the vendor if they decline
        db.collection('vendors').document(vendor_id).delete()
        flash('Registration cancelled. Feel free to register again when ready.', 'info')
        return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        vendor_type = request.form.get('vendor_type')
        
        if not all([name, email, password, vendor_type]):
            return render_template('register.html', error="All fields are required")
        
        # Check if vendor already exists
        vendors_ref = db.collection('vendors')
        if vendors_ref.where('email', '==', email).get():
            return render_template('register.html', error="Email already registered")
        
        try:
            # Create new vendor
            vendor_data = {
                'name': name,
                'email': email,
                'password': password,  # Hash passwords in production
                'vendor_type': vendor_type
            }
            vendor_ref = vendors_ref.document()
            vendor_ref.set(vendor_data)
            
            # Create vendor type policy based on business size
            policy_settings = {
                'small': {
                    'threshold': 50,
                    'earn_min': 5,
                    'earn_max': 10,
                    'redeem': 5,
                    'can_redeem': True
                },
                'medium': {
                    'threshold': 100,
                    'earn_min': 10,
                    'earn_max': 15,
                    'redeem': 10,
                    'can_redeem': True
                },
                'large': {
                    'threshold': 200,
                    'earn_min': 15,
                    'earn_max': 20,
                    'redeem': 15,
                    'can_redeem': True
                }
            }
            
            settings = policy_settings[vendor_type]
            vendor_policy = {
                'vendor_id': vendor_ref.id,
                'threshold_amount': settings['threshold'],
                'earn_percentage_min': settings['earn_min'],
                'earn_percentage_max': settings['earn_max'],
                'redeem_percentage': settings['redeem'],
                'can_redeem': settings['can_redeem']
            }
            db.collection('vendor_policies').document().set(vendor_policy)
            
            session['temp_vendor_id'] = vendor_ref.id
            return redirect(url_for('business_model'))
            
        except Exception as e:
            return render_template('register.html', error=f"Registration failed: {str(e)}")
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'vendor_id' not in session:
        return redirect(url_for('login'))

    vendor_ref = db.collection('vendors').document(session['vendor_id'])
    vendor = vendor_ref.get().to_dict()
    if not vendor:
        return redirect(url_for('logout'))

    # Get today's data
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)  # Convert to datetime
    today_end = today_start + timedelta(days=1)

    # Query Firestore for today's transactions
    transactions_ref = db.collection('transactions')
    today_transactions = transactions_ref.where('vendor_id', '==', vendor_ref.id)\
                                         .where('timestamp', '>=', today_start)\
                                         .where('timestamp', '<', today_end)\
                                         .stream()

    # Calculate metrics
    total_sales = sum(t.to_dict()['amount'] for t in today_transactions)
    total_points_issued = sum(t.to_dict()['points_earned'] for t in today_transactions)
    total_points_redeemed = sum(t.to_dict()['points_redeemed'] for t in today_transactions)

    return render_template('dashboard.html',
                         vendor=vendor,
                         total_sales=total_sales,
                         total_points_issued=total_points_issued,
                         total_points_redeemed=total_points_redeemed)


@app.route('/api/transactions')
def get_transactions():
    if 'vendor_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    transactions_ref = db.collection('transactions')
    transactions = transactions_ref.where('vendor_id', '==', session['vendor_id']).where('timestamp', '>=', start_date).stream()
    
    return jsonify([{
        'id': t.id,
        'amount': t.to_dict()['amount'],
        'points_earned': t.to_dict()['points_earned'],
        'points_redeemed': t.to_dict()['points_redeemed'],
        'timestamp': t.to_dict()['timestamp'].isoformat()
    } for t in transactions])

@app.route('/api/analytics')
def get_analytics():
    if 'vendor_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    days = request.args.get('days', 7, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    transactions_ref = db.collection('transactions')
    transactions = list(transactions_ref.where('vendor_id', '==', session['vendor_id']).where('timestamp', '>=', start_date).where('timestamp', '<=', end_date).stream())
    
    # Existing analytics processing
    daily_sales = {}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        daily_sales[date_str] = 0
        current_date += timedelta(days=1)
    
    # New analytics data
    unique_customers = set()
    customer_activity = {}
    hourly_distribution = {str(i).zfill(2):0 for i in range(24)}
    total_earned = 0
    total_redeemed = 0
    total_amount = 0
    
    for t in transactions:
        t_dict = t.to_dict()

        # Ensure timestamp is a datetime object
        if not isinstance(t_dict['timestamp'], datetime):
            t_dict['timestamp'] = t_dict['timestamp'].replace(tzinfo=None)

        total_amount += t_dict['amount']

        # Daily sales
        date_str = t_dict['timestamp'].strftime('%Y-%m-%d')
        daily_sales[date_str] = daily_sales.get(date_str, 0) + t_dict['amount']
        
        # Points metrics
        total_earned += t_dict.get('points_earned', 0)
        total_redeemed += t_dict.get('points_redeemed', 0)
        
        # Unique customers
        unique_customers.add(t_dict['customer_id'])
        
        # Customer activity by date
        customer_activity[date_str] = customer_activity.get(date_str, 0) + 1
        
        # Hourly distribution
        hour = t_dict['timestamp'].strftime('%H')
        hourly_distribution[hour] += 1

    # Calculate average transaction
    avg_transaction = total_amount / len(unique_customers) if unique_customers else 0
    
    return jsonify({
        'daily_sales': daily_sales,
        'points_metrics': {
            'total_earned': round(total_earned, 2),
            'total_redeemed': round(total_redeemed, 2)
        },
        'unique_customers': len(unique_customers),
        'customer_activity': customer_activity,
        'hourly_distribution': hourly_distribution,
        'avg_transaction': round(avg_transaction,2)
    })

@app.route('/api/export')
def export_transactions():
    if 'vendor_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        format = request.args.get('format', 'csv')
        vendor_ref = db.collection('vendors').document(session['vendor_id'])
        vendor = vendor_ref.get().to_dict()
        
        if not vendor:
            return jsonify({'error': 'Vendor not found'}), 404
            
        transactions_ref = db.collection('transactions')
        transactions = transactions_ref.where('vendor_id', '==', session['vendor_id']).stream()
        
        if format == 'csv':
            return export_csv(transactions)
        elif format == 'pdf':
            return export_pdf(vendor, transactions)
        else:
            return jsonify({'error': 'Invalid format'}), 400
            
    except Exception as e:
        app.logger.error(f"Export error: {str(e)}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

def export_csv(transactions):
    try:
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Transaction ID', 'Amount (INR)', 'Points Earned', 'Points Redeemed', 'Timestamp'])
        
        for t in transactions:
            t_dict = t.to_dict()
            writer.writerow([
                t.id,
                f"{t_dict['amount']:.2f}",
                t_dict['points_earned'],
                t_dict['points_redeemed'],
                t_dict['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        output = si.getvalue()
        si.close()
        
        response = make_response(output)
        response.headers["Content-Disposition"] = f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        return response
        
    except Exception as e:
        raise Exception(f"CSV generation failed: {str(e)}")

def export_pdf(vendor, transactions):
    try:
        if not os.path.exists(WKHTMLTOPDF_PATH):
            raise Exception("wkhtmltopdf not found. Please install it first.")
            
        html_content = render_template(
            'export_pdf.html',
            vendor=vendor,
            transactions=transactions,
            datetime=datetime
        )
        
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None
        }
        
        pdf = pdfkit.from_string(
            html_content, 
            False, 
            options=options,
            configuration=config
        )
        
        response = make_response(pdf)
        response.headers["Content-Disposition"] = f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.pdf"
        response.headers["Content-Type"] = "application/pdf"
        return response
        
    except Exception as e:
        raise Exception(f"PDF generation failed: {str(e)}")
    
@app.route('/check_customer', methods=['GET', 'POST'])
def check_customer():
    if 'vendor_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    vendor_ref = db.collection('vendors').document(session['vendor_id'])
    vendor = vendor_ref.get().to_dict()
    if not vendor:
        flash('Invalid vendor.', 'error')
        return redirect(url_for('logout'))

    customer_info = None
    if request.method == 'POST':
        phone = request.form['phone']
        customers_ref = db.collection('customers')
        customer = customers_ref.where('phone', '==', phone).get()
        
        if customer:
            customer = customer[0].to_dict()
            customer_info = {
                'name': customer['name'],
                'phone': customer['phone'],
                'wallet_balance': customer['wallet_balance']
            }
        else:
            flash("Customer not found.", 'warning')

    return render_template('check_customer.html', customer=customer_info)


@app.route('/apply_discount', methods=['POST'])
def apply_discount():
    if 'vendor_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    try:
        vendor_ref = db.collection('vendors').document(session['vendor_id'])
        phone = request.form.get('phone')
        bill_amount = float(request.form.get('bill_amount', 0))

        # Get customer document
        customers_ref = db.collection('customers')
        customer_docs = customers_ref.where('phone', '==', phone).limit(1).get()
        
        if not customer_docs:
            flash('Customer not found', 'error')
            return redirect(url_for('check_customer'))

        # Get first customer doc and its ID
        customer_doc = customer_docs[0]
        customer_data = customer_doc.to_dict()
        customer_id = customer_doc.id  # Get the document ID to use as customer_id

        # Get vendor policy
        policies_ref = db.collection('vendor_policies')
        policy_docs = policies_ref.where('vendor_id', '==', vendor_ref.id).limit(1).get()
        
        if not policy_docs:
            flash('Vendor policy not found', 'error')
            return redirect(url_for('check_customer'))

        policy = policy_docs[0].to_dict()

        # Calculate points and discounts
        wallet_balance = float(customer_data.get('wallet_balance', 0))
        discount = min(wallet_balance, bill_amount) if policy['can_redeem'] else 0
        final_bill = bill_amount - discount
        points_earned = (final_bill * policy['earn_percentage_max']) / 100

        # Create transaction
        transaction_data = {
            'vendor_id': vendor_ref.id,
            'customer_id': customer_id,  # Use the document ID as customer_id
            'amount': bill_amount,
            'points_earned': points_earned,
            'points_redeemed': discount,
            'timestamp': datetime.utcnow()
        }

        # Update customer wallet balance
        new_balance = wallet_balance - discount + points_earned
        customer_doc.reference.update({'wallet_balance': new_balance})

        # Save transaction
        db.collection('transactions').add(transaction_data)

        flash(f"""Transaction successful!
        Amount: ₹{bill_amount:.2f}
        Discount Applied: ₹{discount:.2f}
        Final Bill: ₹{final_bill:.2f}
        Points Earned: {points_earned:.0f}""", 'success')

        return redirect(url_for('check_customer'))

    except Exception as e:
        print(f"Error details: {str(e)}")  # Debug log
        flash(f"Error processing transaction. Please try again.", 'error')
        return redirect(url_for('check_customer'))