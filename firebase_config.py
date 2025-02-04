import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import atexit

# Global Firestore DB variable
_db = None

def initialize_firebase():
    global _db
    try:
        if not firebase_admin._apps:
            # Fetch Firebase credentials from the firebase-auth.json file
            firebase_credentials_path = "firebase-auth.json"
            
            # Check if the file exists
            if not os.path.exists(firebase_credentials_path):
                raise FileNotFoundError(f"Firebase credentials file not found at {firebase_credentials_path}")
            
            # Load the credentials from the JSON file
            with open(firebase_credentials_path, 'r') as file:
                cred_dict = json.load(file)
            
            # Initialize Firebase with the credentials
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        # Initialize Firestore DB client
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

# Cleanup function to delete Firebase app on exit
def cleanup():
    global _db
    if _db:
        firebase_admin.delete_app(firebase_admin.get_app())
        _db = None

# Register cleanup function to be called on exit
atexit.register(cleanup)

# Initialize Firebase and Firestore DB on module import
db = initialize_firebase()
