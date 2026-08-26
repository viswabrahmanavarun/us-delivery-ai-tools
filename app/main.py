from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv

from app.models.schemas import Ticket, TriageOutput, AccountSummaryBrief
from app.agents.triage_agent import TicketTriageAgent
from app.agents.tam_summariser import TAMAccountSummariser

load_dotenv()

app = FastAPI(title="US Delivery Internship - AI Tools")

@app.post("/triage", response_model=TriageOutput)
def triage_ticket(ticket: Ticket):
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured.")
        
    agent = TicketTriageAgent()
    try:
        result = agent.triage_ticket(ticket)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AccountRequest(BaseModel):
    account_id: str

@app.post("/tam-brief", response_model=AccountSummaryBrief)
def generate_tam_brief(request: AccountRequest):
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured.")
        
    summariser = TAMAccountSummariser()
    try:
        result = summariser.generate_brief(request.account_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
