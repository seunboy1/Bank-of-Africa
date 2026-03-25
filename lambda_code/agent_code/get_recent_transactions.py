"""
Bank of Africa — Get Recent Transactions
Returns the most recent transactions for an account.
"""
import json
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = "boa_transactions"


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def handler(event, context):
    params = extract_params(event)
    account_id = params.get("account_id", "")
    limit = int(params.get("limit", "20"))

    if not account_id:
        return agent_response(event, "Error: account_id is required.")

    table = dynamodb.Table(TABLE_NAME)

    try:
        response = table.query(
            KeyConditionExpression="account_id = :aid",
            ExpressionAttributeValues={":aid": account_id},
            ScanIndexForward=False,  # newest first
            Limit=limit,
        )
        transactions = response.get("Items", [])

        if not transactions:
            return agent_response(
                event, f"No transactions found for account: {account_id}"
            )

        lines = [f"Recent Transactions for Account {account_id}:\n"]
        for i, txn in enumerate(transactions, 1):
            amount = float(txn.get("amount", 0))
            txn_type = txn.get("txn_type", "N/A")
            sign = "+" if txn_type in ("DEPOSIT", "TRANSFER_IN", "CREDIT") else "-"
            lines.append(
                f"{i}. {txn.get('date', 'N/A')} | {txn_type} | "
                f"{sign}NGN {abs(amount):,.2f} | {txn.get('description', '')}"
            )

        return agent_response(event, "\n".join(lines))

    except Exception as e:
        return agent_response(event, f"Error retrieving transactions: {str(e)}")


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
            "httpMethod": event.get("httpMethod", "GET"),
            "httpStatusCode": 200,
            "responseBody": {"application/json": {"body": body}},
        },
    }
