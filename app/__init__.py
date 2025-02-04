from flask import Flask
import os
from firebase_config import get_db

SECRET_KEY = os.urandom(24)
app = Flask(__name__)
app.secret_key = SECRET_KEY

# Get database instance
db = get_db()

# Import routes after app initialization
from app import routes