import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import bcrypt

# Initialize Firebase
cred = credentials.Certificate('firebase-auth.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def hash_password(password):
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def init_database():
    # Clear existing collections (optional, use with caution)
    collections_to_clear = ['vendors', 'vendor_policies', 'customers', 'transactions']
    for collection in collections_to_clear:
        batch = db.batch()
        docs = db.collection(collection).stream()
        for doc in docs:
            batch.delete(doc.reference)
        batch.commit()

    # Create test vendor
    vendors_ref = db.collection('vendors')
    vendor_data = {
        'name': 'Test Vendor',
        'email': 'test@example.com',
        'vendor_type': 'medium',
        'password': hash_password('test123')
    }
    vendor_ref = vendors_ref.add(vendor_data)
    vendor_id = vendor_ref[1].id

    # Create vendor policy
    vendor_policy_data = {
        'vendor_id': vendor_id,
        'threshold_amount': 100,
        'earn_percentage_min': 10,
        'earn_percentage_max': 15,
        'redeem_percentage': 10,
        'can_redeem': True
    }
    db.collection('vendor_policies').document(vendor_id).set(vendor_policy_data)

    # Create test customers
    customers_ref = db.collection('customers')
    customers_data = [
        {
            'name': "Alice Johnson",
            'email': "alice@example.com",
            'phone': "9876543210",
            'wallet_balance': 500.0
        },
        {
            'name': "Bob Smith",
            'email': "bob@example.com",
            'phone': "8765432109",
            'wallet_balance': 700.0
        },
        {
            'name': "Charlie Brown",
            'email': "charlie@example.com",
            'phone': "7654321098",
            'wallet_balance': 300.0
        }
    ]

    customer_refs = []
    for customer_data in customers_data:
        customer_ref = customers_ref.add(customer_data)
        customer_refs.append(customer_ref)

    # Create transactions for the past week
    transactions_ref = db.collection('transactions')
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        
        # Transactions for Alice
        transactions_data = [
            {
                'vendor_id': vendor_id,
                'customer_id': customer_refs[0][1].id,
                'amount': 100.0 * (i + 1),
                'points_earned': 10 * (i + 1),
                'points_redeemed': 5 * i,
                'timestamp': date
            },
            {
                'vendor_id': vendor_id,
                'customer_id': customer_refs[1][1].id,
                'amount': 150.0 * (i + 1),
                'points_earned': 15 * (i + 1),
                'points_redeemed': 7 * i,
                'timestamp': date
            }
        ]
        
        for transaction_data in transactions_data:
            transactions_ref.add(transaction_data)

    # Verify data
    verify_data()

def verify_data():
    # Retrieve and print verification data
    vendors = list(db.collection('vendors').stream())
    customers = list(db.collection('customers').stream())
    transactions = list(db.collection('transactions').stream())
    vendor_policies = list(db.collection('vendor_policies').stream())

    print("\nData Verification:")
    print(f"Vendors created: {len(vendors)}")
    for vendor in vendors:
        vendor_data = vendor.to_dict()
        print(f"- {vendor_data['name']} (ID: {vendor.id})")

    print(f"\nTotal customers created: {len(customers)}")
    for customer in customers:
        customer_data = customer.to_dict()
        print(f"- {customer_data['name']}: Phone {customer_data['phone']}, Wallet Balance ₹{customer_data['wallet_balance']}")

    print(f"\nTotal transactions created: {len(transactions)}")

    # Additional detailed verification can be added as needed

if __name__ == "__main__":
    print("Initializing Firestore database...")
    init_database()
    print("\nDatabase initialization complete!")