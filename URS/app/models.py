from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    vendor_type = db.Column(db.String(20), nullable=False)  # Keep as string for classification
    subscription_status = db.Column(db.Boolean, default=True)

    transactions = db.relationship('Transaction', backref='vendor', lazy=True)
    vendor_policy = db.relationship('VendorType', back_populates='vendor', uselist=False)  # Updated name

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    customer_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    points_earned = db.Column(db.Integer, nullable=False)
    points_redeemed = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Customer(db.Model):
    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    wallet_balance = db.Column(db.Float, default=0.0)  # Wallet balance in currency
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VendorType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    threshold_amount = db.Column(db.Float, nullable=False)
    earn_percentage_min = db.Column(db.Float, nullable=False)
    earn_percentage_max = db.Column(db.Float, nullable=False)
    redeem_percentage = db.Column(db.Float, nullable=True)
    can_redeem = db.Column(db.Boolean, default=False)

    vendor = db.relationship('Vendor', back_populates='vendor_policy')


