import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import atexit

_db = None

def initialize_firebase():
    global _db
    try:
        if not firebase_admin._apps:
            # Check for environment variable first (production)
            # If not found, fall back to local file (development)
            cred_json = os.environ.get("FIREBASE_CREDENTIALS")
            
            if cred_json:
                # Production: load from environment variable
                cred_dict = json.loads(cred_json)
            else:
                # Local development: load from file
                firebase_credentials_path = "firebase-auth.json"
                if not os.path.exists(firebase_credentials_path):
                    raise FileNotFoundError(f"Firebase credentials file not found at {firebase_credentials_path}")
                with open(firebase_credentials_path, 'r') as file:
                    cred_dict = json.load(file)
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        _db = firestore.client()
        return _db

    except Exception as e:
        print(f"Firebase initialization error: {e}")
        raise

def get_db():
    global _db
    if _db is None:
        _db = initialize_firebase()
    return _db

def cleanup():
    global _db
    if _db:
        firebase_admin.delete_app(firebase_admin.get_app())
        _db = None

atexit.register(cleanup)
db = initialize_firebase()
