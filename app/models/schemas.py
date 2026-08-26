from pydantic import BaseModel, Field
from typing import Optional, List

class Ticket(BaseModel):
    ticket_id: Optional[str] = None
    account_id: Optional[str] = None
    company: Optional[str] = None
    subject: str
    body: str
    
class TriageClassification(BaseModel):
    product_area: str = Field(description="The product area or module the ticket relates to.")
    issue_category: str = Field(description="The category of the issue, e.g., Bug, Feature Request, How-To, Performance, Billing, Integration, Onboarding, Data Loss.")
    urgency_tier: str = Field(description="Urgency tier from P1 (critical) to P4 (low).")
    reasoning: str = Field(description="Reasoning for the classification and urgency.")

class TriageOutput(BaseModel):
    classification: TriageClassification
    relevant_doc: Optional[str] = Field(description="Path or name of the relevant knowledge base document.")
    responder_team: str = Field(description="Recommended responder team for the ticket.")
    draft_response: str = Field(description="Draft first-response message for the support agent.")

class AccountSummaryBrief(BaseModel):
    executive_summary: str = Field(description="3-5 sentence executive summary of the account.")
    open_risks_and_issues: str = Field(description="Open risks and flagged issues for the account.")
    recommended_talking_points: str = Field(description="Recommended talking points for the TAM.")
    churn_escalation_flags: List[str] = Field(description="Flags indicating churn risk or escalation signals. Must include direct quotes from tickets.")

class EvalResult(BaseModel):
    task: str
    test_case: str
    passed: bool
    quality_score: float
    reasoning: str
