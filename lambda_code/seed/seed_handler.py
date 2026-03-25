"""
Bank of Africa — Seed Data Handler
CloudFormation Custom Resource Lambda that populates DynamoDB on stack creation.
Automatically runs once when the stack deploys — participants don't touch this.
"""

import json
import uuid
import random
import boto3
import cfnresponse
from decimal import Decimal
from datetime import datetime, timedelta, timezone

dynamodb = boto3.resource("dynamodb")


def handler(event, context):
    """CloudFormation Custom Resource handler."""
    try:
        if event["RequestType"] in ("Create", "Update"):
            seed_all()
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Status": "Seeded"})
        elif event["RequestType"] == "Delete":
            # Don't delete data on stack deletion — tables get deleted anyway
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Status": "Skipped"})
    except Exception as e:
        print(f"Error: {e}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Error": str(e)})


USERS = [
    {"user_id": "1", "full_name": "Adaeze Okonkwo", "email": "adaeze.okonkwo@bankofafrica.ng", "phone": "+234 803 456 7890", "address": "15 Admiralty Way, Lekki Phase 1, Lagos", "bvn": "22345678901", "nin": "12345678901", "date_joined": "2023-03-15", "kyc_tier": "Tier 3"},
    {"user_id": "2", "full_name": "Chukwuemeka Nwosu", "email": "chukwuemeka.nwosu@bankofafrica.ng", "phone": "+234 806 789 0123", "address": "42 Adeola Hopewell St, Victoria Island, Lagos", "bvn": "33456789012", "nin": "23456789012", "date_joined": "2022-11-08", "kyc_tier": "Tier 3"},
    {"user_id": "3", "full_name": "Fatima Abdullahi", "email": "fatima.abdullahi@bankofafrica.ng", "phone": "+234 809 012 3456", "address": "8 Maitama Sule Street, Abuja", "bvn": "44567890123", "nin": "34567890123", "date_joined": "2024-01-20", "kyc_tier": "Tier 2"},
    {"user_id": "4", "full_name": "Oluwaseun Adeyemi", "email": "seun.adeyemi@bankofafrica.ng", "phone": "+234 812 345 6789", "address": "23 Ring Road, Ibadan, Oyo State", "bvn": "55678901234", "nin": "45678901234", "date_joined": "2024-06-10", "kyc_tier": "Tier 2"},
    {"user_id": "5", "full_name": "Ngozi Eze", "email": "ngozi.eze@bankofafrica.ng", "phone": "+234 815 678 9012", "address": "7 New Haven, Enugu", "bvn": "66789012345", "nin": "56789012345", "date_joined": "2023-09-05", "kyc_tier": "Tier 3"},
]

ACCOUNTS = [
    {"account_id": "1001", "user_id": "1", "account_type": "Savings", "balance": Decimal("2750000"), "currency": "NGN", "status": "active"},
    {"account_id": "1002", "user_id": "1", "account_type": "Current", "balance": Decimal("850000"), "currency": "NGN", "status": "active"},
    {"account_id": "1003", "user_id": "1", "account_type": "Fixed Deposit", "balance": Decimal("5000000"), "currency": "NGN", "status": "active"},
    {"account_id": "2001", "user_id": "2", "account_type": "Savings", "balance": Decimal("37500000"), "currency": "NGN", "status": "active"},
    {"account_id": "2002", "user_id": "2", "account_type": "Current", "balance": Decimal("488000"), "currency": "NGN", "status": "active"},
    {"account_id": "2003", "user_id": "2", "account_type": "Credit Line", "balance": Decimal("400000"), "currency": "NGN", "status": "active"},
    {"account_id": "3001", "user_id": "3", "account_type": "Savings", "balance": Decimal("1200000"), "currency": "NGN", "status": "active"},
    {"account_id": "3002", "user_id": "3", "account_type": "Current", "balance": Decimal("320000"), "currency": "NGN", "status": "active"},
    {"account_id": "4001", "user_id": "4", "account_type": "Savings", "balance": Decimal("650000"), "currency": "NGN", "status": "active"},
    {"account_id": "4002", "user_id": "4", "account_type": "Current", "balance": Decimal("180000"), "currency": "NGN", "status": "active"},
    {"account_id": "5001", "user_id": "5", "account_type": "Savings", "balance": Decimal("4200000"), "currency": "NGN", "status": "active"},
    {"account_id": "5002", "user_id": "5", "account_type": "Current", "balance": Decimal("1100000"), "currency": "NGN", "status": "active"},
    {"account_id": "5003", "user_id": "5", "account_type": "Fixed Deposit", "balance": Decimal("10000000"), "currency": "NGN", "status": "active"},
]

DESCRIPTIONS = {
    "DEPOSIT": ["Salary credit from Dangote Industries", "Salary credit from MTN Nigeria", "Cash deposit at Lekki branch", "Cash deposit via POS agent", "Freelance payment received"],
    "WITHDRAWAL": ["ATM withdrawal - Shoprite Ikeja", "ATM withdrawal - Palms Mall", "Cash withdrawal at branch", "POS withdrawal - Agent banking"],
    "TRANSFER_OUT": ["Rent payment", "School fees - University of Lagos", "Electricity bill - Ikeja Electric", "Internet - Spectranet", "Transfer to family", "DSTV subscription", "Car loan repayment"],
    "TRANSFER_IN": ["Refund from vendor", "Payment received - freelance", "Transfer from spouse", "Business income"],
    "POS_PURCHASE": ["POS - Shoprite Ikeja", "POS - Chicken Republic", "POS - Total Filling Station", "POS - Hubmart", "POS - Jumia delivery"],
}


def generate_transactions(account_id, count=100):
    txns = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        days_ago = random.randint(1, 365)
        txn_date = now - timedelta(days=days_ago)
        txn_type = random.choice(list(DESCRIPTIONS.keys()))
        amounts = {"DEPOSIT": [150000, 250000, 450000, 750000], "WITHDRAWAL": [10000, 20000, 50000, 100000],
                    "TRANSFER_OUT": [25000, 75000, 150000, 500000], "TRANSFER_IN": [25000, 50000, 100000],
                    "POS_PURCHASE": [2500, 5000, 12000, 25000, 50000]}
        amount = Decimal(str(random.choice(amounts.get(txn_type, [10000]))))
        desc = random.choice(DESCRIPTIONS.get(txn_type, ["Transaction"]))
        txns.append({
            "account_id": account_id,
            "txn_id": f"TXN-{txn_date.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6]}",
            "date": txn_date.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount, "txn_type": txn_type, "description": desc,
        })
    return txns


def seed_all():
    print("Seeding Bank of Africa database...")

    users_table = dynamodb.Table("boa_users")
    for u in USERS:
        users_table.put_item(Item=u)
    print(f"  Seeded {len(USERS)} users")

    accounts_table = dynamodb.Table("boa_accounts")
    for a in ACCOUNTS:
        accounts_table.put_item(Item=a)
    print(f"  Seeded {len(ACCOUNTS)} accounts")

    txn_table = dynamodb.Table("boa_transactions")
    total = 0
    for a in ACCOUNTS:
        if a["account_type"] != "Fixed Deposit":
            txns = generate_transactions(a["account_id"])
            for t in txns:
                txn_table.put_item(Item=t)
            total += len(txns)
    print(f"  Seeded {total} transactions")
    print("Done!")
