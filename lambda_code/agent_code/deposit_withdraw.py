"""
Bank of Africa — Deposit / Withdraw
Handles deposits and withdrawals for a single account.
"""
import json
import uuid
import boto3
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
ACCOUNTS_TABLE = "boa_accounts"
TRANSACTIONS_TABLE = "boa_transactions"


def handler(event, context):
    params = extract_params(event)
    account_id = params.get("account_id", "")
    amount_str = params.get("amount", "0")
    direction = params.get("direction", "").lower()  # "deposit" or "withdraw"

    if not account_id:
        return agent_response(event, "Error: account_id is required.")
    if direction not in ("deposit", "withdraw"):
        return agent_response(event, "Error: direction must be 'deposit' or 'withdraw'.")

    try:
        amount = Decimal(str(amount_str))
    except Exception:
        return agent_response(event, f"Error: Invalid amount: {amount_str}")

    if amount <= 0:
        return agent_response(event, "Error: Amount must be greater than zero.")

    accounts_table = dynamodb.Table(ACCOUNTS_TABLE)
    txn_table = dynamodb.Table(TRANSACTIONS_TABLE)

    try:
        # Get current account
        resp = accounts_table.get_item(Key={"account_id": account_id})
        acct = resp.get("Item")
        if not acct:
            return agent_response(event, f"Error: Account {account_id} not found.")

        current_balance = Decimal(str(acct.get("balance", 0)))

        # Withdrawal: check sufficient funds
        if direction == "withdraw":
            if current_balance < amount:
                return agent_response(
                    event,
                    f"Insufficient funds. Account {account_id} has NGN {float(current_balance):,.2f} "
                    f"but you are trying to withdraw NGN {float(amount):,.2f}."
                )
            update_expr = "SET balance = balance - :amt"
            new_balance = current_balance - amount
            txn_type = "WITHDRAWAL"
            desc = f"Cash withdrawal"
        else:
            update_expr = "SET balance = balance + :amt"
            new_balance = current_balance + amount
            txn_type = "DEPOSIT"
            desc = f"Cash deposit"

        # Update balance
        accounts_table.update_item(
            Key={"account_id": account_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues={":amt": amount},
        )

        # Create transaction log
        now = datetime.now(timezone.utc).isoformat()
        txn_id = str(uuid.uuid4())[:8]
        txn_table.put_item(
            Item={
                "account_id": account_id,
                "txn_id": txn_id,
                "date": now,
                "amount": amount,
                "txn_type": txn_type,
                "description": desc,
            }
        )

        result = (
            f"{direction.capitalize()} successful!\n"
            f"- Account: {account_id}\n"
            f"- Amount: NGN {float(amount):,.2f}\n"
            f"- New Balance: NGN {float(new_balance):,.2f}\n"
            f"- Transaction ID: {txn_id}\n"
            f"- Timestamp: {now}"
        )

        return agent_response(event, result)

    except Exception as e:
        return agent_response(event, f"Error processing {direction}: {str(e)}")


def extract_params(event):
    params = {}
    if "parameters" in event:
        for param in event["parameters"]:
            params[param["name"]] = param["value"]
    elif "requestBody" in event:
        content = event["requestBody"].get("content", {})
        props = content.get("application/json", {}).get("properties", [])
        for prop in props:
            params[prop["name"]] = prop["value"]
    else:
        params = event
    return params


def agent_response(event, body):
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": body}},
        },
    }
