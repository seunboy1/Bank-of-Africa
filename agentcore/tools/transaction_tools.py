"""
Bank of Africa — Transaction Tools
Strands Agents custom tools for the Transaction Agent.
"""

import uuid
import boto3
from datetime import datetime, timezone
from decimal import Decimal
from strands import tool

dynamodb = boto3.resource("dynamodb")
ACCOUNTS_TABLE = "boa_accounts"
TRANSACTIONS_TABLE = "boa_transactions"


@tool
def get_recent_transactions(account_id: str, limit: int = 20) -> str:
    """
    Get recent transactions for a bank account, ordered newest first.

    Args:
        account_id: The account to get transactions for (e.g., "2002")
        limit: Maximum number of transactions to return (default 20)

    Returns:
        A formatted list of recent transactions with dates, amounts, types, and descriptions.
    """
    table = dynamodb.Table(TRANSACTIONS_TABLE)

    try:
        response = table.query(
            KeyConditionExpression="account_id = :aid",
            ExpressionAttributeValues={":aid": account_id},
            ScanIndexForward=False,
            Limit=limit,
        )
        transactions = response.get("Items", [])

        if not transactions:
            return f"No transactions found for account: {account_id}"

        lines = [f"Recent Transactions for Account {account_id}:\n"]
        for i, txn in enumerate(transactions, 1):
            amount = float(txn.get("amount", 0))
            txn_type = txn.get("txn_type", "N/A")
            sign = "+" if txn_type in ("DEPOSIT", "TRANSFER_IN", "CREDIT") else "-"
            lines.append(
                f"{i}. {txn.get('date', 'N/A')} | {txn_type} | "
                f"{sign}NGN {abs(amount):,.2f} | {txn.get('description', '')}"
            )

        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving transactions: {str(e)}"


@tool
def transfer_funds(source_account_id: str, destination_account_id: str, amount: float) -> str:
    """
    Transfer money from one bank account to another.
    Validates sufficient balance before executing.

    Args:
        source_account_id: Account to transfer FROM (e.g., "2001")
        destination_account_id: Account to transfer TO (e.g., "2002")
        amount: Amount in NGN to transfer (e.g., 100000)

    Returns:
        Success message with new balances and transaction IDs, or error if insufficient funds.
    """
    if amount <= 0:
        return "Error: Amount must be greater than zero."
    if source_account_id == destination_account_id:
        return "Error: Source and destination accounts must be different."

    accounts_table = dynamodb.Table(ACCOUNTS_TABLE)
    txn_table = dynamodb.Table(TRANSACTIONS_TABLE)
    amt = Decimal(str(amount))

    try:
        # 1. Check source balance
        source_resp = accounts_table.get_item(Key={"account_id": source_account_id})
        source = source_resp.get("Item")
        if not source:
            return f"Error: Source account {source_account_id} not found."

        source_balance = Decimal(str(source.get("balance", 0)))
        if source_balance < amt:
            return (
                f"Insufficient funds. Account {source_account_id} has "
                f"NGN {float(source_balance):,.2f} but you need NGN {float(amt):,.2f}."
            )

        # 2. Check destination exists
        dest_resp = accounts_table.get_item(Key={"account_id": destination_account_id})
        dest = dest_resp.get("Item")
        if not dest:
            return f"Error: Destination account {destination_account_id} not found."

        # 3. Execute transfer
        accounts_table.update_item(
            Key={"account_id": source_account_id},
            UpdateExpression="SET balance = balance - :amt",
            ExpressionAttributeValues={":amt": amt},
        )
        accounts_table.update_item(
            Key={"account_id": destination_account_id},
            UpdateExpression="SET balance = balance + :amt",
            ExpressionAttributeValues={":amt": amt},
        )

        # 4. Create transaction logs
        now = datetime.now(timezone.utc).isoformat()
        txn_out_id = f"TXN-{str(uuid.uuid4())[:8]}"
        txn_in_id = f"TXN-{str(uuid.uuid4())[:8]}"

        txn_table.put_item(Item={
            "account_id": source_account_id, "txn_id": txn_out_id,
            "date": now, "amount": amt, "txn_type": "TRANSFER_OUT",
            "description": f"Transfer to account {destination_account_id}",
        })
        txn_table.put_item(Item={
            "account_id": destination_account_id, "txn_id": txn_in_id,
            "date": now, "amount": amt, "txn_type": "TRANSFER_IN",
            "description": f"Transfer from account {source_account_id}",
        })

        new_source = source_balance - amt
        new_dest = Decimal(str(dest.get("balance", 0))) + amt

        return (
            f"Transfer successful!\n"
            f"- Amount: NGN {float(amt):,.2f}\n"
            f"- From: Account {source_account_id} (new balance: NGN {float(new_source):,.2f})\n"
            f"- To: Account {destination_account_id} (new balance: NGN {float(new_dest):,.2f})\n"
            f"- Transaction IDs: {txn_out_id}, {txn_in_id}\n"
            f"- Timestamp: {now}"
        )
    except Exception as e:
        return f"Error processing transfer: {str(e)}"


@tool
def deposit_withdraw(account_id: str, amount: float, direction: str) -> str:
    """
    Deposit money into or withdraw money from a bank account.

    Args:
        account_id: The account ID (e.g., "2002")
        amount: Amount in NGN (e.g., 50000)
        direction: Either "deposit" or "withdraw"

    Returns:
        Success message with new balance and transaction ID, or error message.
    """
    direction = direction.lower()
    if direction not in ("deposit", "withdraw"):
        return "Error: direction must be 'deposit' or 'withdraw'."
    if amount <= 0:
        return "Error: Amount must be greater than zero."

    accounts_table = dynamodb.Table(ACCOUNTS_TABLE)
    txn_table = dynamodb.Table(TRANSACTIONS_TABLE)
    amt = Decimal(str(amount))

    try:
        resp = accounts_table.get_item(Key={"account_id": account_id})
        acct = resp.get("Item")
        if not acct:
            return f"Error: Account {account_id} not found."

        current_balance = Decimal(str(acct.get("balance", 0)))

        if direction == "withdraw" and current_balance < amt:
            return (
                f"Insufficient funds. Account {account_id} has "
                f"NGN {float(current_balance):,.2f} but you need NGN {float(amt):,.2f}."
            )

        if direction == "deposit":
            update_expr = "SET balance = balance + :amt"
            new_balance = current_balance + amt
            txn_type = "DEPOSIT"
        else:
            update_expr = "SET balance = balance - :amt"
            new_balance = current_balance - amt
            txn_type = "WITHDRAWAL"

        accounts_table.update_item(
            Key={"account_id": account_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues={":amt": amt},
        )

        now = datetime.now(timezone.utc).isoformat()
        txn_id = f"TXN-{str(uuid.uuid4())[:8]}"
        txn_table.put_item(Item={
            "account_id": account_id, "txn_id": txn_id,
            "date": now, "amount": amt, "txn_type": txn_type,
            "description": f"Cash {direction}",
        })

        return (
            f"{direction.capitalize()} successful!\n"
            f"- Account: {account_id}\n"
            f"- Amount: NGN {float(amt):,.2f}\n"
            f"- New Balance: NGN {float(new_balance):,.2f}\n"
            f"- Transaction ID: {txn_id}\n"
            f"- Timestamp: {now}"
        )
    except Exception as e:
        return f"Error processing {direction}: {str(e)}"
