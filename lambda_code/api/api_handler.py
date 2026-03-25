"""
Bank of Africa — API Handler
Receives chat messages from React frontend via API Gateway.
Uses Amazon Bedrock Converse API with tool use to implement the multi-agent pattern.

This approach works immediately after CloudFormation deploy — no AgentCore setup needed.
For the AgentCore version, see the agent/ directory in the full project.
"""

import json
import os
import uuid
import boto3
from decimal import Decimal

bedrock = boto3.client("bedrock-runtime", region_name=os.environ.get("REGION", "us-east-1"))
dynamodb = boto3.resource("dynamodb")

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
    "Content-Type": "application/json",
}

# Store conversation history per session (in-memory for demo)
sessions = {}

SYSTEM_PROMPT = """You are the Bank of Africa AI Banking Assistant. You help customers manage their bank accounts through natural conversation.

You have tools to:
1. Look up customer profiles (get_user_profile)
2. List all accounts for a customer (list_accounts)
3. Check account balances (get_balance)
4. View recent transactions (get_recent_transactions)
5. Transfer money between accounts (transfer_funds)
6. Deposit or withdraw cash (deposit_withdraw)

RULES:
- When asked for balances with a USER ID: first call list_accounts, then call get_balance for EACH account.
- Before any transfer: check the source balance first. If insufficient, tell the user.
- After any transfer/deposit/withdrawal: show the updated balance automatically.
- Format currency as NGN with commas (e.g., NGN 1,500,000.00).
- Be friendly and conversational.
- If a request is unclear, ask for clarification.
"""

TOOLS = [
    {
        "toolSpec": {
            "name": "get_user_profile",
            "description": "Get a customer's profile by user_id. Returns name, email, phone, address, BVN, KYC tier.",
            "inputSchema": {"json": {"type": "object", "properties": {"user_id": {"type": "string", "description": "Customer ID (e.g., '1', '2', '3')"}}, "required": ["user_id"]}}
        }
    },
    {
        "toolSpec": {
            "name": "list_accounts",
            "description": "List all bank accounts for a customer by user_id. Returns account IDs, types, balances.",
            "inputSchema": {"json": {"type": "object", "properties": {"user_id": {"type": "string", "description": "Customer ID"}}, "required": ["user_id"]}}
        }
    },
    {
        "toolSpec": {
            "name": "get_balance",
            "description": "Get the current balance for a specific account by account_id.",
            "inputSchema": {"json": {"type": "object", "properties": {"account_id": {"type": "string", "description": "Account ID (e.g., '1001', '2002')"}}, "required": ["account_id"]}}
        }
    },
    {
        "toolSpec": {
            "name": "get_recent_transactions",
            "description": "Get recent transactions for an account. Returns dates, amounts, types, descriptions.",
            "inputSchema": {"json": {"type": "object", "properties": {"account_id": {"type": "string", "description": "Account ID"}}, "required": ["account_id"]}}
        }
    },
    {
        "toolSpec": {
            "name": "transfer_funds",
            "description": "Transfer money from one account to another. Validates balance before executing.",
            "inputSchema": {"json": {"type": "object", "properties": {
                "source_account_id": {"type": "string", "description": "Account to transfer FROM"},
                "destination_account_id": {"type": "string", "description": "Account to transfer TO"},
                "amount": {"type": "number", "description": "Amount in NGN"}
            }, "required": ["source_account_id", "destination_account_id", "amount"]}}
        }
    },
    {
        "toolSpec": {
            "name": "deposit_withdraw",
            "description": "Deposit or withdraw cash from an account.",
            "inputSchema": {"json": {"type": "object", "properties": {
                "account_id": {"type": "string", "description": "Account ID"},
                "amount": {"type": "number", "description": "Amount in NGN"},
                "direction": {"type": "string", "description": "'deposit' or 'withdraw'"}
            }, "required": ["account_id", "amount", "direction"]}}
        }
    },
]


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)


def execute_tool(name, params):
    """Execute a banking tool and return the result."""
    try:
        if name == "get_user_profile":
            table = dynamodb.Table("boa_users")
            user = table.get_item(Key={"user_id": params["user_id"]}).get("Item", {})
            if not user:
                return f"No user found with ID: {params['user_id']}"
            return json.dumps(user, cls=DecimalEncoder)

        elif name == "list_accounts":
            table = dynamodb.Table("boa_accounts")
            resp = table.query(IndexName="user_id-index", KeyConditionExpression="user_id = :uid",
                             ExpressionAttributeValues={":uid": params["user_id"]})
            return json.dumps(resp.get("Items", []), cls=DecimalEncoder)

        elif name == "get_balance":
            table = dynamodb.Table("boa_accounts")
            acct = table.get_item(Key={"account_id": params["account_id"]}).get("Item", {})
            if not acct:
                return f"No account found: {params['account_id']}"
            return json.dumps(acct, cls=DecimalEncoder)

        elif name == "get_recent_transactions":
            table = dynamodb.Table("boa_transactions")
            resp = table.query(KeyConditionExpression="account_id = :aid",
                             ExpressionAttributeValues={":aid": params["account_id"]},
                             ScanIndexForward=False, Limit=20)
            return json.dumps(resp.get("Items", []), cls=DecimalEncoder)

        elif name == "transfer_funds":
            return do_transfer(params["source_account_id"], params["destination_account_id"], params["amount"])

        elif name == "deposit_withdraw":
            return do_deposit_withdraw(params["account_id"], params["amount"], params["direction"])

        else:
            return f"Unknown tool: {name}"
    except Exception as e:
        return f"Error: {str(e)}"


def do_transfer(source_id, dest_id, amount):
    table = dynamodb.Table("boa_accounts")
    txn_table = dynamodb.Table("boa_transactions")
    amt = Decimal(str(amount))

    source = table.get_item(Key={"account_id": source_id}).get("Item")
    if not source:
        return f"Source account {source_id} not found"
    bal = Decimal(str(source.get("balance", 0)))
    if bal < amt:
        return f"Insufficient funds. Account {source_id} has NGN {float(bal):,.2f}, need NGN {float(amt):,.2f}"

    dest = table.get_item(Key={"account_id": dest_id}).get("Item")
    if not dest:
        return f"Destination account {dest_id} not found"

    table.update_item(Key={"account_id": source_id}, UpdateExpression="SET balance = balance - :a", ExpressionAttributeValues={":a": amt})
    table.update_item(Key={"account_id": dest_id}, UpdateExpression="SET balance = balance + :a", ExpressionAttributeValues={":a": amt})

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    t1, t2 = str(uuid.uuid4())[:8], str(uuid.uuid4())[:8]
    txn_table.put_item(Item={"account_id": source_id, "txn_id": f"TXN-{t1}", "date": now, "amount": amt, "txn_type": "TRANSFER_OUT", "description": f"Transfer to {dest_id}"})
    txn_table.put_item(Item={"account_id": dest_id, "txn_id": f"TXN-{t2}", "date": now, "amount": amt, "txn_type": "TRANSFER_IN", "description": f"Transfer from {source_id}"})

    new_src = bal - amt
    new_dst = Decimal(str(dest.get("balance", 0))) + amt
    return f"Transfer successful! NGN {float(amt):,.2f} moved. {source_id} new balance: NGN {float(new_src):,.2f}. {dest_id} new balance: NGN {float(new_dst):,.2f}. TXN IDs: {t1}, {t2}"


def do_deposit_withdraw(account_id, amount, direction):
    table = dynamodb.Table("boa_accounts")
    txn_table = dynamodb.Table("boa_transactions")
    amt = Decimal(str(amount))
    acct = table.get_item(Key={"account_id": account_id}).get("Item")
    if not acct:
        return f"Account {account_id} not found"
    bal = Decimal(str(acct.get("balance", 0)))

    if direction == "withdraw" and bal < amt:
        return f"Insufficient funds. Balance: NGN {float(bal):,.2f}, requested: NGN {float(amt):,.2f}"

    expr = "SET balance = balance + :a" if direction == "deposit" else "SET balance = balance - :a"
    table.update_item(Key={"account_id": account_id}, UpdateExpression=expr, ExpressionAttributeValues={":a": amt})

    new_bal = (bal + amt) if direction == "deposit" else (bal - amt)
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    tid = str(uuid.uuid4())[:8]
    txn_table.put_item(Item={"account_id": account_id, "txn_id": f"TXN-{tid}", "date": now, "amount": amt, "txn_type": direction.upper(), "description": f"Cash {direction}"})
    return f"{direction.capitalize()} successful! NGN {float(amt):,.2f}. New balance: NGN {float(new_bal):,.2f}. TXN: {tid}"


def handler(event, context):
    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": HEADERS, "body": ""}

    try:
        body = json.loads(event.get("body", "{}"))
        user_msg = body.get("message", "")
        session_id = body.get("session_id", str(uuid.uuid4()))

        if not user_msg:
            return {"statusCode": 400, "headers": HEADERS, "body": json.dumps({"error": "Message required"})}

        # Get or create conversation history
        if session_id not in sessions:
            sessions[session_id] = []
        messages = sessions[session_id]
        messages.append({"role": "user", "content": [{"text": user_msg}]})

        # Agentic loop — keep calling Bedrock until we get a final text response
        traces = []
        max_iterations = 10

        for i in range(max_iterations):
            response = bedrock.converse(
                modelId=MODEL_ID,
                system=[{"text": SYSTEM_PROMPT}],
                messages=messages,
                toolConfig={"tools": TOOLS},
            )

            output = response["output"]["message"]
            messages.append(output)
            stop_reason = response["stopReason"]

            if stop_reason == "tool_use":
                # Model wants to call a tool
                tool_results = []
                for block in output["content"]:
                    if "toolUse" in block:
                        tool_name = block["toolUse"]["name"]
                        tool_input = block["toolUse"]["input"]
                        tool_id = block["toolUse"]["toolUseId"]

                        traces.append({"type": "action", "agent": tool_name, "input": json.dumps(tool_input)})

                        result = execute_tool(tool_name, tool_input)
                        traces.append({"type": "result", "text": f"{tool_name} completed"})

                        tool_results.append({
                            "toolResult": {
                                "toolUseId": tool_id,
                                "content": [{"text": result}],
                            }
                        })

                # Feed tool results back
                messages.append({"role": "user", "content": tool_results})

            elif stop_reason == "end_turn":
                # Got final response
                final_text = ""
                for block in output["content"]:
                    if "text" in block:
                        final_text += block["text"]

                # Trim session history to prevent context overflow
                if len(messages) > 40:
                    messages[:] = messages[-30:]
                sessions[session_id] = messages

                return {
                    "statusCode": 200,
                    "headers": HEADERS,
                    "body": json.dumps({"response": final_text, "session_id": session_id, "traces": traces}),
                }
            else:
                break

        return {
            "statusCode": 200,
            "headers": HEADERS,
            "body": json.dumps({"response": "I'm still processing. Please try again.", "session_id": session_id, "traces": traces}),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"statusCode": 500, "headers": HEADERS, "body": json.dumps({"error": str(e)})}
