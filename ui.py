import streamlit as st
import os
import requests
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="US Delivery Tools", layout="wide")
st.title("AI Tooling for Support & TAM Teams")

tab1, tab2 = st.tabs(["Intelligent Triage", "TAM Account Summariser"])

with tab1:
    st.header("Ticket Triage Agent")
    st.write("Submit a raw ticket to get an automated structured triage output.")
    
    subject = st.text_input("Ticket Subject")
    body = st.text_area("Ticket Body")
    
    if st.button("Triage Ticket"):
        if not subject or not body:
            st.warning("Please provide both subject and body.")
        else:
            with st.spinner("Triaging..."):
                try:
                    from app.models.schemas import Ticket
                    from app.agents.triage_agent import TicketTriageAgent
                    
                    ticket = Ticket(subject=subject, body=body)
                    agent = TicketTriageAgent()
                    result = agent.triage_ticket(ticket)
                    
                    st.success("Triage Complete!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Classification")
                        st.write(f"**Product Area:** {result.classification.product_area}")
                        st.write(f"**Category:** {result.classification.issue_category}")
                        st.write(f"**Urgency:** {result.classification.urgency_tier}")
                        st.write(f"**Reasoning:** {result.classification.reasoning}")
                        
                        st.subheader("Routing")
                        st.write(f"**Responder Team:** {result.responder_team}")
                        
                    with col2:
                        st.subheader("Knowledge Base Retrieval")
                        if result.relevant_doc:
                            st.info(f"Relevant Doc Found: {result.relevant_doc}")
                        else:
                            st.write("No relevant document found in KB.")
                            
                        st.subheader("Draft Response")
                        st.text_area("Suggested First Response", result.draft_response, height=150)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tab2:
    st.header("TAM Account Health Summariser")
    st.write("Enter an Account ID to generate a strategic prep brief.")
    
    account_id = st.text_input("Account ID (e.g. ACC-3847)")
    
    if st.button("Generate Brief"):
        if not account_id:
            st.warning("Please provide an Account ID.")
        else:
            with st.spinner("Generating brief..."):
                try:
                    from app.agents.tam_summariser import TAMAccountSummariser
                    
                    summariser = TAMAccountSummariser()
                    result = summariser.generate_brief(account_id)
                    
                    st.success("Brief Generated!")
                    
                    st.subheader("Executive Summary")
                    st.write(result.executive_summary)
                    
                    st.subheader("Open Risks & Issues")
                    st.write(result.open_risks_and_issues)
                    
                    st.subheader("Recommended Talking Points")
                    st.write(result.recommended_talking_points)
                    
                    st.subheader("Churn / Escalation Flags")
                    if result.churn_escalation_flags:
                        for flag in result.churn_escalation_flags:
                            st.warning(f"🚩 {flag}")
                    else:
                        st.info("No major churn risks identified in recent tickets.")
                except ValueError as ve:
                    st.error(str(ve))
                except Exception as e:
                    st.error(f"Error: {str(e)}")
