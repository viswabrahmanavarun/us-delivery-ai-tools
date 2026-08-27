# US Delivery Internship — Starter Dataset

This repository contains the mock dataset for the **US Delivery Internship Technical Task Round**.  
Candidates should use this data exclusively for their submissions.

---

## Repository Structure

```
starter-repo/
├── data/
│   ├── tickets.json          # 500 synthetic support tickets
│   └── accounts.json         # 50 synthetic customer account summaries
├── knowledge-base/
│   ├── products/
│   │   ├── databridge-pro.md
│   │   ├── cloudsync.md
│   │   ├── analyticshub.md
│   │   ├── securevault.md
│   │   └── workflowengine.md
│   ├── troubleshooting/
│   │   ├── authentication-sso.md
│   │   └── performance-and-integrations.md
│   ├── billing/
│   │   └── billing-and-plans.md
│   └── onboarding/
│       └── onboarding-guide.md
└── DATA_SCHEMA.md            # Field-level schema documentation
```

---

## Data Description

### `data/tickets.json`

500 synthetic support tickets submitted by fictitious enterprise customers. Each ticket represents a realistic interaction between a customer and the technical support team.

**Key fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ticket_id` | string | Unique ticket identifier (e.g., `TKT-10042`) |
| `account_id` | string | Links to an account in `accounts.json` |
| `company` | string | Customer company name |
| `subject` | string | Ticket subject line |
| `body` | string | Full ticket body text |
| `product` | string | Product the ticket relates to |
| `product_area` | string | Module within the product |
| `category` | string | Issue type: Bug, Feature Request, How-To, Performance, Billing, Integration, Onboarding, Data Loss |
| `urgency` | string | P1 (critical) to P4 (low) |
| `status` | string | Open, In Progress, Pending Customer, Resolved, Closed |
| `plan_tier` | string | Starter, Professional, Business, Enterprise |
| `assigned_agent` | string | Support agent name |
| `created_at` | ISO 8601 | Ticket creation timestamp |
| `updated_at` | ISO 8601 | Last update timestamp |
| `tags` | array | Free-form tags |
| `channel` | string | Submission channel: email, portal, chat, phone |
| `satisfaction_score` | int\|null | CSAT score 1–5, or null if not submitted |

See [DATA_SCHEMA.md](DATA_SCHEMA.md) for full schema with examples.

---

### `data/accounts.json`

50 synthetic customer account summaries, each representing a fictional enterprise customer's relationship with the platform.

**Key fields:**

| Field | Type | Description |
|-------|------|-------------|
| `account_id` | string | Unique account identifier |
| `company` | string | Company name |
| `tam` | string | Assigned Technical Account Manager |
| `plan_tier` | string | Current plan |
| `arr_usd` | int | Annual recurring revenue in USD |
| `seats_licensed` | int | Number of licensed seats |
| `seats_active` | int | Seats with activity in last 30 days |
| `products` | array | Products in use |
| `health_status` | string | Healthy, At Risk, Churning, or New |
| `usage_trend` | string | Increasing, Stable, Declining, or Inactive |
| `open_tickets` | int | Currently open support tickets |
| `p1_tickets_last_30d` | int | P1 tickets in last 30 days |
| `renewal_date` | YYYY-MM-DD | Contract renewal date |
| `last_qbr_date` | YYYY-MM-DD | Date of last Quarterly Business Review |
| `escalation_notes` | array | Free-text escalation observations |
| `nps_score` | int\|null | Net Promoter Score 1–10, or null |
| `primary_contact` | object | `name` and `title` of main contact |
| `integrations_active` | array | Active third-party integrations |
| `region` | string | Geographic region |
| `industry` | string | Customer industry vertical |

---

### `knowledge-base/`

Markdown documentation files representing a product knowledge base. These docs contain:

- Product feature descriptions and configuration references
- Common error codes and their meanings
- Step-by-step troubleshooting guides
- Plan limits and pricing information
- Onboarding checklists and training paths

Candidates should use these docs as the retrieval corpus for knowledge-base lookup features.

---

## Usage Notes

- All data is **entirely synthetic**. Company names, contact details, and ticket content are fictional.
- Ticket `account_id` values do not always match an entry in `accounts.json` — this is intentional. Handle missing account lookups gracefully.
- The `escalation_notes` field in accounts contains plain-text observations. These are designed to test churn-risk signal detection.
- Some tickets are deliberately ambiguous in category or urgency — this tests edge-case handling.

---


## Setup Instructions

1.  **Clone the repository and navigate into it.**
2.  **Set up a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up environment variables:**
    Copy `.env.example` to `.env` and insert your OpenAI API key.
    ```bash
    cp .env.example .env
    # Edit .env with your key
    ```

## Running the Application

### 1. Web UI (Streamlit - Recommended)
Run the Streamlit application for a nice interactive demo (Bonus feature):
```bash
streamlit run ui.py
```

### 2. FastAPI Backend
You can run the API server locally:
```bash
uvicorn app.main:app --reload
```
And access the interactive Swagger docs at `http://127.0.0.1:8000/docs`.

### 3. Run Evaluations
Run the evaluation harness:
```bash
python -m evals.eval_harness
```
This will produce `eval_report.json` with the LLM-as-judge scoring.

---

## Design Note

### Failure modes
1.  **Hallucination in Triage/Draft Responses:** The model might recommend an action or product feature that doesn't exist. *Detection:* LLM-as-a-judge evals on random production samples, and user thumbs-up/down feedback on drafted responses. *Mitigation:* Ground the generation heavily in the RAG context with strict system prompts ("Do not invent features").
2.  **API Rate Limiting / Downtime:** External LLM providers can go down or limit usage. *Detection:* Monitor HTTP 429 and 50X errors on the API layer. *Mitigation:* Implement exponential backoff, retry logic, and fallback models (e.g., routing to a cheaper model or returning a fallback structured error so the pipeline doesn't crash).
3.  **Context Window Overflow:** If a TAM queries an account that has a massive volume of extremely long tickets, it may exceed the LLM's context window. *Detection:* Track token usage and catch `ContextWindowExceeded` exceptions. *Mitigation:* We dynamically filter by the last 90 days. If the token count is still too high, we can recursively summarize older tickets before passing them to the final context.

### Latency vs quality
I opted to use `gpt-4o-mini` instead of `gpt-4o`. This provides significantly faster response times (latency) at a much lower cost, which is crucial for triage systems where hundreds of tickets arrive quickly. The trade-off is a slight drop in the depth of reasoning. If latency were a *hard* constraint (e.g., sub-200ms), I would swap the LLM out entirely for a fine-tuned smaller local model (like a distilled BERT/RoBERTa for classification) and skip the draft response generation until the agent explicitly clicks "Draft Reply".

### Data sensitivity
Support tickets and account metadata often contain PII (Names, Emails, Phone Numbers). To prevent leaking this to external APIs:
*   In a real-world scenario, we would run a local PII scrubbing pipeline (e.g., using Presidio or regexes) to mask entities before sending the payload to OpenAI.
*   We can leverage self-hosted open-weights models (like Llama-3) or private VPC deployments (like Azure OpenAI) ensuring zero data retention policies. Currently, the design avoids sending the entire `accounts.json` dataset to the LLM; it only sends the specific fields for the requested account.

### Scaling
With 10x the ticket volume, the current bottleneck will be the **RAG embedding step** and **API Rate Limits**. Currently, embeddings are generated on-the-fly and cosine similarity is computed sequentially in-memory. 
*   **What breaks first:** The naive loop over tickets to filter and compute embeddings will become too slow, and concurrent requests will hit OpenAI's rate limits. 
*   **Solution:** We would migrate the embeddings to a dedicated Vector DB (like Pinecone or Milvus) and ingest tickets asynchronously via a message queue (Kafka/RabbitMQ) rather than processing them synchronously in the FastAPI request loop.

## Sample Runs

### Task 1: Ticket Triage Agent
**Input Ticket:**
```json
{
  "subject": "Unable to connect DataBridge Pro to Connectors",
  "body": "Hi team, We're experiencing a critical issue with DataBridge Pro. Our Connectors pipeline has been failing since approximately yesterday morning. Error message: 'ERR_CONNECTION_TIMEOUT after 30s'."
}
```
**Output (Triage & Draft):**
```json
{
  "classification": {
    "product_area": "DataBridge Pro",
    "issue_category": "Connectivity / Timeout",
    "urgency_tier": "P1",
    "reasoning": "Critical impact affecting 47 users in production."
  },
  "relevant_doc": "knowledge-base/troubleshooting/performance-and-integrations.md",
  "responder_team": "DataBridge Pro Support",
  "draft_response": "Hi there, I'm sorry to hear that the DataBridge Pro connectors are timing out. I've escalated this to our support team (P1 priority) and we're looking into it right now."
}
```

### Task 2: TAM Account Summariser
**Input Account ID:** `ACC-3336`

**Output Brief:**
- **Executive Summary:** Omni Consumer Products is a Business tier customer with $500k ARR. However, the account is marked "At Risk" with a renewal due in 10 days and inactive usage trends.
- **Open Risks:** High seat count vs active seats indicates under-utilization. Escalation notes show decision-maker is evaluating competitors.
- **Churn Flags:** 
  - 🚩 *"3 consecutive P1 tickets in the last 30 days"* - Indicates recent critical incidents eroding confidence.
