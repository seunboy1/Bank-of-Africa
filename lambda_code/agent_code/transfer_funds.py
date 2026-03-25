"""
Bank of Africa — Transfer Funds
Transfers money between accounts with balance validation.
Creates transaction log entries for both sides.
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
    source_id = params.get("source_account_id", "")
    dest_id = params.get("destination_account_id", "")
    amount_str = params.get("amount", "0")

    if not source_id or not dest_id:
        return agent_response(event, "Error: source_account_id and destination_account_id are required.")

    try:
        amount = Decimal(str(amount_str))
    except Exception:
        return agent_response(event, f"Error: Invalid amount: {amount_str}")

    if amount <= 0:
        return agent_response(event, "Error: Amount must be greater than zero.")

    if source_id == dest_id:
        return agent_response(event, "Error: Source and destination accounts must be different.")

    accounts_table = dynamodb.Table(ACCOUNTS_TABLE)
    txn_table = dynamodb.Table(TRANSACTIONS_TABLE)

    try:
        # 1. Get source account and check balance
        source_resp = accounts_table.get_item(Key={"account_id": source_id})
        source = source_resp.get("Item")
        if not source:
            return agent_response(event, f"Error: Source account {source_id} not found.")

        source_balance = Decimal(str(source.get("balance", 0)))
        if source_balance < amount:
            return agent_response(
                event,
                f"Insufficient funds. Account {source_id} has NGN {float(source_balance):,.2f} "
                f"but you are trying to transfer NGN {float(amount):,.2f}."
            )

        # 2. Get destination account
        dest_resp = accounts_table.get_item(Key={"account_id": dest_id})
        dest = dest_resp.get("Item")
        if not dest:
            return agent_response(event, f"Error: Destination account {dest_id} not found.")

        # 3. Debit source
        accounts_table.update_item(
            Key={"account_id": source_id},
            UpdateExpression="SET balance = balance - :amt",
            ExpressionAttributeValues={":amt": amount},
        )

        # 4. Credit destination
        accounts_table.update_item(
            Key={"account_id": dest_id},
            UpdateExpression="SET balance = balance + :amt",
            ExpressionAttributeValues={":amt": amount},
        )

        # 5. Create transaction logs
        now = datetime.now(timezone.utc).isoformat()
        txn_id_out = str(uuid.uuid4())[:8]
        txn_id_in = str(uuid.uuid4())[:8]

        txn_table.put_item(
            Item={
                "account_id": source_id,
                "txn_id": txn_id_out,
                "date": now,
                "amount": amount,
                "txn_type": "TRANSFER_OUT",
                "description": f"Transfer to account {dest_id}",
                "counterparty_account": dest_id,
            }
        )

        txn_table.put_item(
            Item={
                "account_id": dest_id,
                "txn_id": txn_id_in,
                "date": now,
                "amount": amount,
                "txn_type": "TRANSFER_IN",
                "description": f"Transfer from account {source_id}",
                "counterparty_account": source_id,
            }
        )

        new_source_balance = source_balance - amount
        new_dest_balance = Decimal(str(dest.get("balance", 0))) + amount

        result = (
            f"Transfer successful!\n"
            f"- Amount: NGN {float(amount):,.2f}\n"
            f"- From: Account {source_id} (new balance: NGN {float(new_source_balance):,.2f})\n"
            f"- To: Account {dest_id} (new balance: NGN {float(new_dest_balance):,.2f})\n"
            f"- Transaction IDs: {txn_id_out} (debit), {txn_id_in} (credit)\n"
            f"- Timestamp: {now}"
        )

        return agent_response(event, result)

    except Exception as e:
        return agent_response(event, f"Error processing transfer: {str(e)}")


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
