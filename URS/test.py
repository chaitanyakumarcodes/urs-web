from app import app, db
from app.models import Vendor, Transaction, Customer, VendorType
from datetime import datetime, timedelta

def init_database():
    with app.app_context():
        print("Dropping existing tables...")
        db.drop_all()
        
        print("Creating new tables...")
        db.create_all()

        # Create test vendor
        print("Creating test vendor...")
        vendor = Vendor(
            name='Test Vendor',
            email='test@example.com',
            vendor_type='medium'
        )
        vendor.set_password('test123')
        db.session.add(vendor)
        db.session.commit()

        # Populate VendorType based on Vendor ID
        print("Assigning reward policies to vendors...")
        vendor_type = VendorType(
            vendor_id=vendor.id,
            threshold_amount=100,
            earn_percentage_min=10,
            earn_percentage_max=15,
            redeem_percentage=10,
            can_redeem=True
        )
        db.session.add(vendor_type)
        db.session.commit()

        # Create test customers
        print("Creating test customers...")
        customers = [
            Customer(name="Alice Johnson", email="alice@example.com", phone="9876543210", wallet_balance=500.0),
            Customer(name="Bob Smith", email="bob@example.com", phone="8765432109", wallet_balance=700.0),
            Customer(name="Charlie Brown", email="charlie@example.com", phone="7654321098", wallet_balance=300.0)
        ]
        
        for customer in customers:
            db.session.add(customer)
        db.session.commit()

        # Retrieve customer IDs after commit
        alice = Customer.query.filter_by(email="alice@example.com").first()
        bob = Customer.query.filter_by(email="bob@example.com").first()

        # Create transactions for the past week
        print("Creating test transactions...")
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            transactions = [
                Transaction(
                    vendor_id=vendor.id,
                    customer_id=alice.customer_id,  # Assign to Alice
                    amount=100.0 * (i + 1),
                    points_earned=10 * (i + 1),
                    points_redeemed=5 * i,
                    timestamp=date
                ),
                Transaction(
                    vendor_id=vendor.id,
                    customer_id=bob.customer_id,  # Assign to Bob
                    amount=150.0 * (i + 1),
                    points_earned=15 * (i + 1),
                    points_redeemed=7 * i,
                    timestamp=date
                )
            ]
            for t in transactions:
                db.session.add(t)
        
        db.session.commit()
        
        # Verify data
        verify_data()

def verify_data():
    with app.app_context():
        vendor = Vendor.query.first()
        customers = Customer.query.all()
        transactions = Transaction.query.all()
        vendor_type = VendorType.query.first()
        
        print("\nData Verification:")
        print(f"Vendor created: {vendor.name} (ID: {vendor.id})")
        print(f"Assigned Reward Policy: Threshold ₹{vendor_type.threshold_amount}, Earn {vendor_type.earn_percentage_max}%, Redeem Allowed: {vendor_type.can_redeem}")
        print(f"Total customers created: {len(customers)}")
        for customer in customers:
            print(f"- {customer.name}: Phone {customer.phone}, Wallet Balance ₹{customer.wallet_balance}")
        print(f"Total transactions created: {len(transactions)}")
        print(f"Today's transactions: {len([t for t in transactions if t.timestamp.date() == datetime.utcnow().date()])}")

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("\nDatabase initialization complete!")
