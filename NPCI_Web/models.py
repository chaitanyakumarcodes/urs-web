from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    rewards_balance = db.Column(db.Float, default=0.0)

    transactions = db.relationship('Transaction', backref='customer', lazy=True)

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Small, Medium, Large
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=True)
    subscription_type = db.Column(db.String(50), nullable=False)  # Fixed or commission-based

    transactions = db.relationship('Transaction', backref='vendor', lazy=True)
    reward_policies = db.relationship('RewardPolicy', backref='vendor', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    reward_points_earned = db.Column(db.Float, default=0.0)

class RewardPolicy(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    min_spend_threshold = db.Column(db.Float, nullable=False)
    reward_rate = db.Column(db.Float, nullable=False)  # Points per dollar spent
    max_redeemable_points = db.Column(db.Float, nullable=False)

class RewardRedemption(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    points_used = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    total_transactions = db.Column(db.Integer, default=0)
    total_sales = db.Column(db.Float, default=0.0)
    total_rewards_issued = db.Column(db.Float, default=0.0)
    total_rewards_redeemed = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
