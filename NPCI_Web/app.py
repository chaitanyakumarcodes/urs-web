from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:ChaitanyA%4023@localhost/urs_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # "vendor" or "admin"

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            if user.role == 'vendor':
                return redirect(url_for('vendor_dashboard'))
            else:
                flash("Admin login not implemented", 'warning')
                return redirect(url_for('login'))
        else:
            flash('Invalid login credentials', 'danger')
    return render_template('login.html')

@app.route('/auth/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/vendor/dashboard')
def vendor_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user.role != 'vendor':
        flash("Access Denied", 'danger')
        return redirect(url_for('login'))
    
    transactions = Transaction.query.filter_by(vendor_id=user.id).all()
    return render_template('vendor_dashboard.html', transactions=transactions)

@app.route('/vendor/transactions')
def vendor_transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user.role != 'vendor':
        flash("Access Denied", 'danger')
        return redirect(url_for('login'))
    
    transactions = Transaction.query.filter_by(vendor_id=user.id).all()
    return render_template('transactions.html', transactions=transactions)

@app.route('/vendor/analytics')
def vendor_analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user.role != 'vendor':
        flash("Access Denied", 'danger')
        return redirect(url_for('login'))
    
    # Add analytics logic (e.g., graphs, stats, etc.)
    return render_template('analytics.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if user.role != 'admin':
        flash("Access Denied", 'danger')
        return redirect(url_for('login'))
    
    # Admin dashboard logic (e.g., user management, stats)
    return render_template('admin_dashboard.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # 'vendor' or 'admin'
        
        hashed_password = generate_password_hash(password)
        new_user = User(email=email, password=hashed_password, role=role)
        
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully!", 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

if __name__ == "__main__":
    app.run(debug=True)
