from flask import Blueprint

# Initialize Blueprints for modular routing
auth_bp = Blueprint("auth", __name__)
vendor_bp = Blueprint("vendor", __name__)
