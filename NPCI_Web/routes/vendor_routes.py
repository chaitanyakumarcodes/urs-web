from flask import Blueprint, render_template, session, redirect, url_for
from models import db, Vendor, Transaction, Analytics

vendor_bp = Blueprint("vendor", __name__)

@vendor_bp.route("/dashboard")
def dashboard():
    if "vendor_id" not in session:
        return redirect(url_for("auth.login"))

    vendor = Vendor.query.get(session["vendor_id"])
    transactions = Transaction.query.filter_by(vendor_id=vendor.id).all()
    analytics = Analytics.query.filter_by(vendor_id=vendor.id).first()

    return render_template("dashboard.html", vendor=vendor, transactions=transactions, analytics=analytics)

@vendor_bp.route("/transactions")
def transactions():
    if "vendor_id" not in session:
        return redirect(url_for("auth.login"))

    vendor = Vendor.query.get(session["vendor_id"])
    transactions = Transaction.query.filter_by(vendor_id=vendor.id).all()

    return render_template("transactions.html", vendor=vendor, transactions=transactions)

@vendor_bp.route("/analytics")
def analytics():
    if "vendor_id" not in session:
        return redirect(url_for("auth.login"))

    vendor = Vendor.query.get(session["vendor_id"])
    analytics = Analytics.query.filter_by(vendor_id=vendor.id).first()

    return render_template("analytics.html", vendor=vendor, analytics=analytics)
