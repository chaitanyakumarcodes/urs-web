from app import app, db
from app.models import Vendor, Transaction, Customer, VendorType
from flask import render_template, request, jsonify, session, redirect, url_for,flash, make_response
import pandas as pd
from io import StringIO, BytesIO
import pdfkit
from datetime import datetime, timedelta
import csv
import os

# Configure wkhtmltopdf path
WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)

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
        
        vendor = Vendor.query.filter_by(email=email).first()
        if vendor and vendor.check_password(password):
            session['vendor_id'] = vendor.id
            return redirect(url_for('dashboard'))
        
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
        vendor = Vendor.query.get(vendor_id)
        if vendor:
            db.session.delete(vendor)
            db.session.commit()
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
        if Vendor.query.filter_by(email=email).first():
            return render_template('register.html', error="Email already registered")
        
        try:
            # Create new vendor
            vendor = Vendor(
                name=name,
                email=email,
                vendor_type=vendor_type
            )
            vendor.set_password(password)
            db.session.add(vendor)
            db.session.commit()
            
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
            vendor_policy = VendorType(
                vendor_id=vendor.id,
                threshold_amount=settings['threshold'],
                earn_percentage_min=settings['earn_min'],
                earn_percentage_max=settings['earn_max'],
                redeem_percentage=settings['redeem'],
                can_redeem=settings['can_redeem']
            )
            db.session.add(vendor_policy)
            db.session.commit()
            session['temp_vendor_id'] = vendor.id
            flash('Registration successful! Please review our business model.', 'success')
            return redirect(url_for('business_model'))
            
        except Exception as e:
            db.session.rollback()
            return render_template('register.html', error=f"Registration failed: {str(e)}")
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'vendor_id' not in session:
        return redirect(url_for('login'))
    
    vendor = Vendor.query.get(session['vendor_id'])
    if not vendor:
        return redirect(url_for('logout'))
    
    # Get today's transactions
    today = datetime.utcnow().date()
    today_transactions = Transaction.query.filter(
        Transaction.vendor_id == vendor.id,
        db.func.date(Transaction.timestamp) == today
    ).all()
    
    # Calculate metrics
    total_sales = sum(t.amount for t in today_transactions)
    total_points_issued = sum(t.points_earned for t in today_transactions)
    total_points_redeemed = sum(t.points_redeemed for t in today_transactions)
    
    print(f"Debug: Found {len(today_transactions)} transactions") # Debug line
    
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
    
    transactions = Transaction.query.filter(
        Transaction.vendor_id == session['vendor_id'],
        Transaction.timestamp >= start_date
    ).all()
    
    return jsonify([{
        'id': t.id,
        'amount': t.amount,
        'points_earned': t.points_earned,
        'points_redeemed': t.points_redeemed,
        'timestamp': t.timestamp.isoformat()
    } for t in transactions])

@app.route('/api/analytics')
def get_analytics():
    if 'vendor_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get last 7 days by default
    days = request.args.get('days', 7, type=int)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    transactions = Transaction.query.filter(
        Transaction.vendor_id == session['vendor_id'],
        Transaction.timestamp >= start_date,
        Transaction.timestamp <= end_date
    ).all()
    
    # Process data day by day
    daily_sales = {}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        daily_sales[date_str] = 0
        current_date += timedelta(days=1)
    
    total_earned = 0
    total_redeemed = 0
    
    # Calculate actual values
    for t in transactions:
        date_str = t.timestamp.strftime('%Y-%m-%d')
        daily_sales[date_str] = daily_sales.get(date_str, 0) + t.amount
        total_earned += t.points_earned
        total_redeemed += t.points_redeemed
    
    return jsonify({
        'daily_sales': daily_sales,
        'points_metrics': {
            'total_earned': total_earned,
            'total_redeemed': total_redeemed
        }
    })

@app.route('/api/export')
def export_transactions():
    if 'vendor_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        format = request.args.get('format', 'csv')
        vendor = Vendor.query.get(session['vendor_id'])
        
        if not vendor:
            return jsonify({'error': 'Vendor not found'}), 404
            
        transactions = Transaction.query.filter_by(vendor_id=vendor.id).all()
        
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
            writer.writerow([
                t.id,
                f"{t.amount:.2f}",
                t.points_earned,
                t.points_redeemed,
                t.timestamp.strftime('%Y-%m-%d %H:%M:%S')
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

    vendor = Vendor.query.get(session['vendor_id'])
    if not vendor:
        flash('Invalid vendor.', 'error')
        return redirect(url_for('logout'))

    customer_info = None
    if request.method == 'POST':
        phone = request.form['phone']
        customer = Customer.query.filter_by(phone=phone).first()

        if customer:
            customer_info = {
                'name': customer.name,
                'phone': customer.phone,
                'wallet_balance': customer.wallet_balance
            }
        else:
            flash("Customer not found.", 'warning')

    return render_template('check_customer.html', customer=customer_info)


@app.route('/apply_discount', methods=['POST'])
def apply_discount():
    if 'vendor_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))

    vendor = Vendor.query.get(session['vendor_id'])
    if not vendor:
        return redirect(url_for('logout'))

    try:
        phone = request.form.get('phone')
        bill_amount = request.form.get('bill_amount')

        if not phone or not bill_amount:
            flash("Missing phone number or bill amount.", 'danger')
            return redirect(url_for('check_customer'))

        try:
            bill_amount = float(bill_amount)
        except ValueError:
            flash("Invalid bill amount. Please enter a valid number.", 'danger')
            return redirect(url_for('check_customer'))

        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            flash("Customer not found.", 'danger')
            return redirect(url_for('check_customer'))

        vendor_type = vendor.vendor_policy
        if not vendor_type:
            flash("Vendor policy not found. Please contact support.", 'danger')
            return redirect(url_for('check_customer'))

        if bill_amount < vendor_type.threshold_amount:
            flash(f"Bill must be at least ₹{vendor_type.threshold_amount} to earn points.", 'warning')
            return redirect(url_for('check_customer'))

        # Debug logs
        print(f"Customer Wallet Balance: {customer.wallet_balance}")
        print(f"Can Redeem: {vendor_type.can_redeem}")

        # Calculate discount
        discount = min(customer.wallet_balance, bill_amount) if vendor_type.can_redeem else 0
        final_bill = bill_amount - discount
        points_earned = (final_bill * vendor_type.earn_percentage_max) / 100
        points_redeemed = discount

        # Debug logs
        print(f"Discount Calculated: {discount}")
        print(f"Points Earned: {points_earned}")
        print(f"Points Redeemed: {points_redeemed}")

        # Update customer wallet balance
        print(f"Wallet Balance Before: {customer.wallet_balance}")
        customer.wallet_balance -= discount
        customer.wallet_balance += points_earned
        print(f"Wallet Balance After: {customer.wallet_balance}")

        # Save transaction
        new_transaction = Transaction(
            vendor_id=vendor.id,
            customer_id=customer.customer_id,
            amount=bill_amount,
            points_earned=points_earned,
            points_redeemed=points_redeemed,
            timestamp=datetime.utcnow()
        )

        db.session.add(new_transaction)
        db.session.commit()

        flash(f"Transaction successful! ₹{discount:.2f} used. Final bill: ₹{final_bill:.2f}. Earned {points_earned} points.", 'success')
        return redirect(url_for('check_customer'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error processing transaction: {str(e)}", 'danger')
        return redirect(url_for('check_customer'))
