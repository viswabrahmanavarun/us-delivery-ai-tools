from dotenv import load_dotenv
load_dotenv()
import os
import json
from groq import Groq
from app.models.schemas import TriageOutput, TriageClassification, Ticket
from app.utils.rag import get_rag_system

class TicketTriageAgent:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
    def triage_ticket(self, ticket: Ticket) -> TriageOutput:
        rag = get_rag_system()
        query = f"{ticket.subject}\n\n{ticket.body}"
        relevant_doc = rag.retrieve_relevant_doc(query)
        
        doc_context = ""
        doc_path = None
        if relevant_doc:
            doc_context = f"Relevant Knowledge Base Document ({relevant_doc['filename']}):\n{relevant_doc['content']}\n\n"
            doc_path = relevant_doc['path']
            
        prompt = f"""
You are an intelligent triage agent for a Technical Support team.
Your task is to analyze the following support ticket and provide structured triage output.

Ticket Subject: {ticket.subject}
Ticket Body: {ticket.body}

{doc_context}
Based on the ticket and the provided knowledge base context (if any), please provide:
1. Classification (product area, issue category, urgency P1-P4, and reasoning)
2. Recommended responder team
3. A draft first-response message to the customer.

You MUST respond with a valid JSON object strictly matching this schema:
{{
  "classification": {{
    "product_area": "string",
    "issue_category": "string",
    "urgency_tier": "string",
    "reasoning": "string"
  }},
  "responder_team": "string",
  "draft_response": "string"
}}
"""

        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are an expert technical support triage assistant. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        content = json.loads(response.choices[0].message.content)
        
        triage_result = TriageOutput(
            classification=TriageClassification(**content["classification"]),
            relevant_doc=doc_path,
            responder_team=content.get("responder_team", ""),
            draft_response=content.get("draft_response", "")
        )
            
        return triage_result
