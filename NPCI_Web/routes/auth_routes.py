from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, Vendor

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        vendor = Vendor.query.filter_by(email=email).first()
        if vendor and password == "admin123":  # Replace with hashed password check
            session["vendor_id"] = vendor.id
            return redirect(url_for("vendor.dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.pop("vendor_id", None)
    return redirect(url_for("auth.login"))
