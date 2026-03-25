# 🏦 Bank of Africa Workshop — Participant Guide

## Your 1-Hour Schedule

| Time | What You're Doing |
|------|-------------------|
| 0:00-0:10 | **Deploy** — Paste one command, wait for it to finish |
| 0:10-0:15 | **Explore** — Open the chat app, try your first query |
| 0:15-0:35 | **Guided Lab** — Work through 6 challenges with the AI banking assistant |
| 0:35-0:45 | **Experiment** — Try your own queries, break things, test edge cases |
| 0:45-0:55 | **Under the Hood** — Facilitator shows how the agent reasons + eKYC demo |
| 0:55-1:00 | **Q&A + Wrap-up** |

---

## Step 1: Deploy (0:00-0:10)

### Open AWS CloudShell
1. Log into your AWS Workshop Studio account
2. Click the **CloudShell** icon (terminal icon) at the top of the AWS Console
3. Wait for CloudShell to initialize

### Run the deploy command
Paste this and press Enter:

```bash
curl -s https://BOA-WORKSHOP-URL/deploy.sh | bash
```

> ⏱️ **This takes ~8-10 minutes.** You'll see progress messages as each component deploys.

### When it finishes, you'll see:
```
🏦 ===========================================
   BANK OF AFRICA IS LIVE!
===========================================

🌐 Chat App:    http://boa-frontend-XXXXX.s3-website-us-east-1.amazonaws.com
🔌 API:         https://XXXXX.execute-api.us-east-1.amazonaws.com/prod
```

**Click the Chat App URL** to open the Bank of Africa in a new browser tab.

---

## Step 2: Your First Query (0:10-0:15)

The chat app looks like a banking assistant. Type your first message:

```
Show me the profile for user 2
```

You should see **Chukwuemeka Nwosu's** profile — name, email, phone, address, BVN, and KYC tier.

🎯 **What just happened:** Your message went to API Gateway → Lambda → Amazon Bedrock (Claude). The model decided to call the `get_user_profile` tool, which read from DynamoDB and returned the result. The model then formatted it into a friendly response.

---

## Step 3: Guided Challenges (0:15-0:35)

Work through these 6 challenges in order. Each one demonstrates a different capability.

### Challenge 1: Multi-Account Balance Check
```
What are all the account balances for user 2?
```

🎯 **What to notice:** The AI calls `list_accounts` first to get all 3 account IDs, then calls `get_balance` for each one. It loops through multiple tool calls autonomously — you never told it how many accounts to check.

**Expected:** 3 accounts — Savings (NGN 37,500,000), Current (NGN 488,000), Credit Line (NGN 400,000).

---

### Challenge 2: Transaction History
```
Show me the recent transactions for account 2002
```

🎯 **What to notice:** The AI retrieves transactions from DynamoDB sorted by newest first. Look at the Nigerian transaction descriptions — POS purchases at Shoprite, salary credits from Dangote, DSTV subscriptions.

---

### Challenge 3: Transfer with Insufficient Funds
```
Transfer NGN 1,000,000 from account 2002 to account 2001
```

🎯 **What to notice:** Account 2002 (Current) only has NGN 488,000. The AI checks the balance BEFORE attempting the transfer and tells you it can't proceed. It doesn't just fail — it explains why.

---

### Challenge 4: Successful Transfer
```
Transfer NGN 100,000 from account 2001 to account 2002
```

🎯 **What to notice:** This time it works. Account 2001 (Savings, NGN 37,500,000) has plenty. Watch for:
- Transaction IDs for both sides (debit and credit)
- Updated balances shown automatically
- Timestamp of the transaction

**Verify it worked:**
```
Show me the balance for account 2002
```

The balance should be NGN 588,000 (was 488,000 + 100,000 transferred).

---

### Challenge 5: Knowledge Base Query (RAG)
```
What are the fees for international transfers?
```

🎯 **What to notice:** This answer comes from the **Bank Handbook** stored in S3 and indexed in a Bedrock Knowledge Base — NOT from the model's training data. The AI searches the handbook and returns the actual bank policy (1% + NGN 2,500 processing fee).

Try another:
```
What are the KYC tier requirements and transaction limits?
```

---

### Challenge 6: Complex Multi-Step Request
```
Check if user 2's savings account has enough for a NGN 500,000 transfer 
to their current account. If yes, do the transfer and show me the 
updated balances for all of user 2's accounts.
```

🎯 **What to notice:** This is ONE message that triggers MULTIPLE tool calls:
1. `list_accounts` → finds all accounts for user 2
2. `get_balance` → checks savings balance
3. `transfer_funds` → executes the transfer
4. `get_balance` × 3 → shows all updated balances

The AI orchestrates all of this from a single natural language instruction. **This is the power of agentic AI.**

---

## Step 4: Free Experimentation (0:35-0:45)

Now try your own queries. Some ideas:

**Test edge cases:**
- "Transfer NGN 100 from account 9999 to account 2001" (non-existent account)
- "Deposit NGN 500,000 into account 3002" (try a deposit)
- "What's the interest rate on fixed deposits?" (knowledge base)

**Test different users:**
- User 1: Adaeze Okonkwo (3 accounts including Fixed Deposit)
- User 3: Fatima Abdullahi (Tier 2 — different from Tier 3 users)
- User 5: Ngozi Eze (3 accounts)

**Test ambiguous requests:**
- "I need money" (should ask for clarification)
- "Move money around" (should ask which accounts)

**Test conversational memory:**
- Ask about user 2, then follow up with "What's their email?" (should remember context)

---

## Step 5: Under the Hood (0:45-0:55)

The facilitator will now show:

### How the AI Agent Reasons
- The Bedrock Converse API with tool use — how the model decides which tool to call
- The agentic loop — model calls a tool, gets results, decides if it needs more tools
- How prompt engineering controls the business logic (balance checking before transfers)

### eKYC Demo (Facilitator's Laptop)
- Amazon Rekognition Face Liveness in action
- Printed photo fails liveness check
- Live face passes
- How this would be the "front door" before a customer gets a bank account

### AgentCore Runtime (Production Path)
- How the same agent code deploys to AgentCore with MicroVM isolation
- Strands SDK Swarm pattern — one line of code to orchestrate multiple agents
- Enterprise features: 8-hour sessions, OpenTelemetry, 100MB payloads

---

## Step 6: Clean Up (After Workshop)

When the workshop is over, run this in CloudShell:

```bash
curl -s https://BOA-WORKSHOP-URL/cleanup.sh | bash
```

This deletes all AWS resources created during the workshop.

---

## Key Takeaways

1. **AI agents can orchestrate complex multi-step banking operations** from a single natural language instruction — no hardcoded workflows.

2. **The business logic lives in prompts, not code.** The Lambda functions are minimal database operations. The agent's prompt controls routing, validation, and formatting.

3. **RAG (Retrieval-Augmented Generation)** grounds the AI in your actual bank policies — it doesn't hallucinate fees or rates.

4. **Amazon Bedrock + DynamoDB + Lambda** is a serverless, pay-per-use stack that scales from a workshop demo to production without changing architecture.

5. **The path from this demo to production** is: add authentication (Cognito), deploy to AgentCore (MicroVM isolation), add observability (OpenTelemetry), and connect real banking APIs.

---

## Want to Keep Building?

Take the code home! Everything is in the CloudFormation stack:
- **Lambda code:** Check the Lambda console for all 7 functions
- **DynamoDB data:** Browse tables in the DynamoDB console
- **Agent prompts:** In the API handler Lambda code (system prompt)
- **React frontend:** In the S3 frontend bucket

The full source code with the AgentCore + Strands SDK version is available from your facilitator.
