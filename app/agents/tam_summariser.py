from dotenv import load_dotenv
load_dotenv()
import os
import json
from datetime import datetime, timedelta
from typing import List
from groq import Groq
from app.models.schemas import AccountSummaryBrief
from app.utils.data_loader import load_accounts, load_tickets

class TAMAccountSummariser:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.accounts = {acc['account_id']: acc for acc in load_accounts()}
        self.tickets = load_tickets()
        
    def _get_account_data(self, account_id: str):
        return self.accounts.get(account_id)
        
    def _get_recent_tickets(self, account_id: str, days: int = 90):
        account_tickets = [t for t in self.tickets if t.get('account_id') == account_id]
        if not account_tickets:
            return []
            
        parsed_tickets = []
        for t in account_tickets:
            try:
                dt = datetime.strptime(t['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                parsed_tickets.append((dt, t))
            except ValueError:
                continue
                
        if not parsed_tickets:
            return []
            
        max_date = max(pt[0] for pt in parsed_tickets)
        cutoff_date = max_date - timedelta(days=days)
        
        recent_tickets = [pt[1] for pt in parsed_tickets if pt[0] >= cutoff_date]
        return recent_tickets
        
    def generate_brief(self, account_id: str) -> AccountSummaryBrief:
        account_data = self._get_account_data(account_id)
        if not account_data:
            raise ValueError(f"Account ID {account_id} not found in dataset.")
            
        recent_tickets = self._get_recent_tickets(account_id, 90)
        
        ticket_context = json.dumps([{
            "id": t["ticket_id"],
            "subject": t["subject"],
            "body": t["body"],
            "urgency": t["urgency"],
            "status": t["status"]
        } for t in recent_tickets], indent=2)
        
        extraction_prompt = f"""
        Analyze the following recent support tickets for account {account_data.get('company')}.
        Identify any signals of churn risk, extreme frustration, or escalation.
        Return ONLY a JSON object containing an array of strings under the key "quotes", where each string is a direct quote from the ticket body that demonstrates the risk. 
        If there are no risks, return {{"quotes": []}}.
        
        Tickets:
        {ticket_context}
        """
        
        extraction_response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Always return valid JSON."},
                {"role": "user", "content": extraction_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            seed=42
        )
        
        try:
            content = extraction_response.choices[0].message.content
            quotes_data = json.loads(content)
            quotes = quotes_data.get("quotes", [])
        except Exception:
            quotes = []
            
        account_context = json.dumps(account_data, indent=2)
        
        brief_prompt = f"""
        You are an AI assistant helping a Technical Account Manager (TAM) prepare for a QBR.
        Generate a concise, actionable account brief.
        
        Account Data:
        {account_context}
        
        Ticket History (Summary of last 90 days):
        There were {len(recent_tickets)} tickets filed in the last 90 days.
        Identified Escalation/Churn Quotes from Tickets: {json.dumps(quotes)}
        
        Provide the response as a JSON object matching this schema:
        {{
            "executive_summary": "string (3-5 sentences)",
            "open_risks_and_issues": "string",
            "recommended_talking_points": "string",
            "churn_escalation_flags": ["list of strings (quotes and justification)"]
        }}
        """
        
        final_response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are a strategic Technical Account Manager assistant. Always return valid JSON."},
                {"role": "user", "content": brief_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            seed=42
        )
        
        final_content = json.loads(final_response.choices[0].message.content)
        return AccountSummaryBrief(**final_content)
