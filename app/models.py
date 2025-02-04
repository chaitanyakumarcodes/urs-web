from datetime import datetime

class FirestoreModel:
    def to_dict(self):
        return self.__dict__

class Vendor(FirestoreModel):
    def __init__(self, id, name, email, vendor_type, subscription_status=True):
        self.id = id
        self.name = name
        self.email = email
        self.vendor_type = vendor_type
        self.subscription_status = subscription_status

class Transaction(FirestoreModel):
    def __init__(self, id, vendor_id, customer_id, amount, points_earned, points_redeemed=0):
        self.id = id
        self.vendor_id = vendor_id
        self.customer_id = customer_id
        self.amount = amount
        self.points_earned = points_earned
        self.points_redeemed = points_redeemed
        self.timestamp = datetime.utcnow()

class Customer(FirestoreModel):
    def __init__(self, id, name, email, phone, wallet_balance=0.0):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.wallet_balance = wallet_balance
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class VendorType(FirestoreModel):
    def __init__(self, vendor_id, threshold_amount, earn_percentage_min, 
                 earn_percentage_max, redeem_percentage, can_redeem=False):
        self.vendor_id = vendor_id
        self.threshold_amount = threshold_amount
        self.earn_percentage_min = earn_percentage_min
        self.earn_percentage_max = earn_percentage_max
        self.redeem_percentage = redeem_percentage
        self.can_redeem = can_redeem