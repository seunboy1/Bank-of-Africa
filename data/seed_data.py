"""
Bank of Africa — DynamoDB Seed Data
Populates the database with realistic Nigerian banking mock data.
Run: python seed_data.py
"""
import boto3
import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import random

dynamodb = boto3.resource("dynamodb", region_name="af-south-1")

# ============================================================
# TABLE CREATION (if not using CloudFormation)
# ============================================================

def create_tables():
    """Create DynamoDB tables if they don't exist."""
    client = boto3.client("dynamodb", region_name="af-south-1")
    existing = client.list_tables()["TableNames"]

    if "boa_users" not in existing:
        client.create_table(
            TableName="boa_users",
            KeySchema=[{"AttributeName": "user_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "user_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Created boa_users table")

    if "boa_accounts" not in existing:
        client.create_table(
            TableName="boa_accounts",
            KeySchema=[{"AttributeName": "account_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "account_id", "AttributeType": "S"},
                {"AttributeName": "user_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "user_id-index",
                    "KeySchema": [{"AttributeName": "user_id", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Created boa_accounts table")

    if "boa_transactions" not in existing:
        client.create_table(
            TableName="boa_transactions",
            KeySchema=[
                {"AttributeName": "account_id", "KeyType": "HASH"},
                {"AttributeName": "txn_id", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "account_id", "AttributeType": "S"},
                {"AttributeName": "txn_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print("Created boa_transactions table")

    # Wait for tables to be active
    import time
    for tbl in ["boa_users", "boa_accounts", "boa_transactions"]:
        if tbl not in existing:
            waiter = client.get_waiter("table_exists")
            waiter.wait(TableName=tbl)
            print(f"  {tbl} is active")


# ============================================================
# SEED DATA
# ============================================================

USERS = [
    {
        "user_id": "1",
        "full_name": "Adaeze Okonkwo",
        "email": "adaeze.okonkwo@bankofafrica.ng",
        "phone": "+234 803 456 7890",
        "address": "15 Admiralty Way, Lekki Phase 1, Lagos",
        "bvn": "22345678901",
        "nin": "12345678901",
        "date_joined": "2023-03-15",
        "kyc_tier": "Tier 3",
    },
    {
        "user_id": "2",
        "full_name": "Chukwuemeka Nwosu",
        "email": "chukwuemeka.nwosu@bankofafrica.ng",
        "phone": "+234 806 789 0123",
        "address": "42 Adeola Hopewell St, Victoria Island, Lagos",
        "bvn": "33456789012",
        "nin": "23456789012",
        "date_joined": "2022-11-08",
        "kyc_tier": "Tier 3",
    },
    {
        "user_id": "3",
        "full_name": "Fatima Abdullahi",
        "email": "fatima.abdullahi@bankofafrica.ng",
        "phone": "+234 809 012 3456",
        "address": "8 Maitama Sule Street, Abuja",
        "bvn": "44567890123",
        "nin": "34567890123",
        "date_joined": "2024-01-20",
        "kyc_tier": "Tier 2",
    },
    {
        "user_id": "4",
        "full_name": "Oluwaseun Adeyemi",
        "email": "seun.adeyemi@bankofafrica.ng",
        "phone": "+234 812 345 6789",
        "address": "23 Ring Road, Ibadan, Oyo State",
        "bvn": "55678901234",
        "nin": "45678901234",
        "date_joined": "2024-06-10",
        "kyc_tier": "Tier 2",
    },
    {
        "user_id": "5",
        "full_name": "Ngozi Eze",
        "email": "ngozi.eze@bankofafrica.ng",
        "phone": "+234 815 678 9012",
        "address": "7 New Haven, Enugu",
        "bvn": "66789012345",
        "nin": "56789012345",
        "date_joined": "2023-09-05",
        "kyc_tier": "Tier 3",
    },
]

ACCOUNTS = [
    # User 1: Adaeze
    {"account_id": "1001", "user_id": "1", "account_type": "Savings", "balance": Decimal("2750000.00"), "currency": "NGN", "status": "active"},
    {"account_id": "1002", "user_id": "1", "account_type": "Current", "balance": Decimal("850000.00"), "currency": "NGN", "status": "active"},
    {"account_id": "1003", "user_id": "1", "account_type": "Fixed Deposit", "balance": Decimal("5000000.00"), "currency": "NGN", "status": "active"},
    # User 2: Chukwuemeka
    {"account_id": "2001", "user_id": "2", "account_type": "Savings", "balance": Decimal("37500000.00"), "currency": "NGN", "status": "active"},
    {"account_id": "2002", "user_id": "2", "account_type": "Current", "balance": Decimal("488000.00"), "currency": "NGN", "status": "active"},
    {"account_id": "2003", "user_id": "2", "account_type": "Credit Line", "balance": Decimal("400000.00"), "currency": "NGN", "status": "active"},
    # User 3: Fatima
    {"account_id": "3001", "user_id": "3", "account_type": "Savings", "balance": Decimal("1200000.00"), "currency": "NGN", "status": "active"},
    {"account_id": "3002", "user_id": "3", "account_type": "Current", "balance": Decimal("320000.00"), "currency": "NGN", "status": "active"},
    # User 4: Oluwaseun
    {"account_id": "4001", "user_id": "4", "account_type": "Savings", "balance": Decimal("650000.00"), "currency": "NGN", "status": "active"},
    {"account_id": "4002", "user_id": "4", "account_type": "Current", "balance": Decimal("180000.00"), "currency": "NGN", "status": "active"},
    # User 5: Ngozi
    {"account_id": "5001", "user_id": "5", "account_type": "Savings", "balance": Decimal("4200000.00"), "currency": "NGN", "status": "active"},
    {"account_id": "5002", "user_id": "5", "account_type": "Current", "balance": Decimal("1100000.00"), "currency": "NGN", "status": "active"},
    {"account_id": "5003", "user_id": "5", "account_type": "Fixed Deposit", "balance": Decimal("10000000.00"), "currency": "NGN", "status": "active"},
]

# Realistic Nigerian transaction descriptions
TXN_DESCRIPTIONS = {
    "DEPOSIT": [
        "Salary credit from Dangote Industries",
        "Salary credit from MTN Nigeria",
        "Salary credit from Access Bank",
        "Cash deposit at Lekki branch",
        "Cash deposit via POS agent",
        "Freelance payment received",
        "Transfer from GTBank",
        "Dividend payment - BUA Cement",
    ],
    "WITHDRAWAL": [
        "ATM withdrawal - Shoprite Ikeja",
        "ATM withdrawal - Palms Mall",
        "Cash withdrawal at branch",
        "POS withdrawal - Agent banking",
    ],
    "TRANSFER_OUT": [
        "Rent payment - Landlord",
        "School fees - University of Lagos",
        "Electricity bill - Ikeja Electric",
        "Internet subscription - Spectranet",
        "Transfer to family",
        "Business payment - supplier",
        "DSTV subscription",
        "Car loan repayment",
        "Mortgage payment",
    ],
    "TRANSFER_IN": [
        "Refund from vendor",
        "Payment received - freelance work",
        "Transfer from spouse",
        "Business income",
    ],
    "POS_PURCHASE": [
        "POS purchase - Shoprite Ikeja",
        "POS purchase - Chicken Republic",
        "POS purchase - Total Filling Station",
        "POS purchase - Hubmart Superstore",
        "POS purchase - Mr Biggs",
        "POS purchase - Jumia delivery",
        "POS purchase - Konga order",
    ],
}


def generate_transactions(account_id, count=100):
    """Generate realistic transaction history for an account."""
    transactions = []
    now = datetime.now(timezone.utc)

    for i in range(count):
        days_ago = random.randint(1, 365)
        txn_date = now - timedelta(days=days_ago)
        txn_type = random.choice(["DEPOSIT", "WITHDRAWAL", "TRANSFER_OUT", "TRANSFER_IN", "POS_PURCHASE"])
        
        if txn_type == "DEPOSIT":
            amount = Decimal(str(random.choice([150000, 250000, 350000, 450000, 500000, 750000, 1000000])))
        elif txn_type == "WITHDRAWAL":
            amount = Decimal(str(random.choice([10000, 20000, 50000, 100000])))
        elif txn_type == "POS_PURCHASE":
            amount = Decimal(str(random.choice([2500, 5000, 8500, 12000, 15000, 25000, 35000, 50000])))
        else:
            amount = Decimal(str(random.choice([25000, 50000, 75000, 100000, 150000, 200000, 500000])))

        desc = random.choice(TXN_DESCRIPTIONS.get(txn_type, TXN_DESCRIPTIONS["TRANSFER_OUT"]))

        transactions.append({
            "account_id": account_id,
            "txn_id": f"TXN-{txn_date.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6]}",
            "date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "txn_type": txn_type,
            "description": desc,
        })

    return transactions


def seed_all():
    """Populate all tables."""
    print("Seeding Bank of Africa database...\n")

    # Users
    users_table = dynamodb.Table("boa_users")
    for user in USERS:
        users_table.put_item(Item=user)
        print(f"  Added user: {user['full_name']} (ID: {user['user_id']})")

    print()

    # Accounts
    accounts_table = dynamodb.Table("boa_accounts")
    for acct in ACCOUNTS:
        accounts_table.put_item(Item=acct)
        print(f"  Added account: {acct['account_id']} ({acct['account_type']}) for user {acct['user_id']} - NGN {float(acct['balance']):,.2f}")

    print()

    # Transactions
    txn_table = dynamodb.Table("boa_transactions")
    total_txns = 0
    for acct in ACCOUNTS:
        if acct["account_type"] != "Fixed Deposit":  # No transactions on FD
            txns = generate_transactions(acct["account_id"], count=random.randint(90, 110))
            for txn in txns:
                txn_table.put_item(Item=txn)
            total_txns += len(txns)
            print(f"  Added {len(txns)} transactions for account {acct['account_id']}")

    print(f"\nDone! Seeded {len(USERS)} users, {len(ACCOUNTS)} accounts, {total_txns} transactions.")


if __name__ == "__main__":
    print("Creating tables (if needed)...")
    create_tables()
    print()
    seed_all()
