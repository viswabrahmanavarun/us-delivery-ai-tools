from dotenv import load_dotenv
load_dotenv()
import json
import os
from groq import Groq
from app.models.schemas import Ticket, EvalResult
from app.agents.triage_agent import TicketTriageAgent
from app.agents.tam_summariser import TAMAccountSummariser

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TRIAGE_TEST_CASES = [
    {
        "id": "triage-1",
        "description": "Clear Bug in DataBridge Pro",
        "input": Ticket(subject="Connectors failing", body="DataBridge Pro connectors are failing with ERR_CONNECTION_TIMEOUT after 30s. Affecting production.", company="Acme"),
        "expected_criteria": "Should classify as Bug, P1 or P2 urgency, and identify product area as Connectors."
    },
    {
        "id": "triage-2",
        "description": "Billing inquiry",
        "input": Ticket(subject="Upgrade to Enterprise", body="We want to upgrade our plan from Starter to Enterprise, how much does it cost?", company="BetaCorp"),
        "expected_criteria": "Should classify as Billing/Sales, P3 or P4 urgency, suggest billing team."
    },
    {
        "id": "triage-3",
        "description": "SSO Authentication issue",
        "input": Ticket(subject="Cannot login via Okta", body="Users are getting SAML binding errors when trying to login using Okta SSO.", company="GammaInc"),
        "expected_criteria": "Should classify as Authentication/SSO, identify relevant doc as authentication-sso.md."
    },
    {
        "id": "triage-4",
        "description": "Feature Request",
        "input": Ticket(subject="Dark mode?", body="Can you add dark mode to the dashboard?", company="DeltaCo"),
        "expected_criteria": "Should classify as Feature Request, P4 urgency."
    },
    {
        "id": "triage-5-adv",
        "description": "Adversarial: Ambiguous Ticket",
        "input": Ticket(subject="It doesn't work", body="Fix it now.", company="Chaos Corp"),
        "expected_criteria": "Should handle ambiguity gracefully, likely classifying as P3/P4 pending more info, and drafting a response asking for details."
    }
]

TAM_TEST_CASES = [
    {
        "id": "tam-1",
        "description": "Healthy Account",
        "input": "ACC-1001",
        "expected_criteria": "Should generate a brief without major churn flags."
    },
    {
        "id": "tam-2",
        "description": "At Risk Account",
        "input": "ACC-1002",
        "expected_criteria": "Should flag churn risks and pull quotes from tickets."
    },
    {
        "id": "tam-3",
        "description": "High value enterprise",
        "input": "ACC-1003",
        "expected_criteria": "Should mention Enterprise tier and highlight key metrics."
    },
    {
        "id": "tam-4",
        "description": "Renewal upcoming",
        "input": "ACC-1004",
        "expected_criteria": "Should recommend discussing the upcoming renewal."
    },
    {
        "id": "tam-5-adv",
        "description": "Adversarial: Incomplete/Missing Account Data",
        "input": "ACC-9999",
        "expected_criteria": "Should gracefully fail or raise ValueError."
    }
]

def llm_as_judge(task: str, test_case: str, output: str, criteria: str) -> EvalResult:
    prompt = f"""
    You are an expert evaluator. Evaluate the following output based on the expected criteria.
    
    Task: {task}
    Test Case: {test_case}
    Output to Evaluate:
    {output}
    
    Expected Criteria:
    {criteria}
    
    Determine if the output meets the criteria (Pass/Fail) and provide a quality score from 0.0 to 1.0.
    Respond with a JSON object strictly matching this schema:
    {{"passed": true/false, "quality_score": 0.0-1.0, "reasoning": "string"}}
    """
    
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are a judge. Always return valid JSON."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    
    try:
        result_dict = json.loads(response.choices[0].message.content)
    except:
        result_dict = {}
        
    return EvalResult(
        task=task,
        test_case=test_case,
        passed=result_dict.get("passed", False),
        quality_score=result_dict.get("quality_score", 0.0),
        reasoning=result_dict.get("reasoning", "")
    )

def run_evals():
    results = []
    
    triage_agent = TicketTriageAgent()
    for tc in TRIAGE_TEST_CASES:
        try:
            output = triage_agent.triage_ticket(tc["input"])
            eval_res = llm_as_judge("Triage", tc["description"], output.model_dump_json(indent=2), tc["expected_criteria"])
        except Exception as e:
            eval_res = EvalResult(task="Triage", test_case=tc["description"], passed=False, quality_score=0.0, reasoning=str(e))
        results.append(eval_res)
        
    from app.utils.data_loader import load_accounts
    accs = load_accounts()
    if len(accs) >= 4:
        TAM_TEST_CASES[0]["input"] = accs[0]["account_id"]
        TAM_TEST_CASES[1]["input"] = accs[1]["account_id"]
        TAM_TEST_CASES[2]["input"] = accs[2]["account_id"]
        TAM_TEST_CASES[3]["input"] = accs[3]["account_id"]
        
    tam_summariser = TAMAccountSummariser()
    for tc in TAM_TEST_CASES:
        try:
            output = tam_summariser.generate_brief(tc["input"])
            eval_res = llm_as_judge("TAM Summariser", tc["description"], output.model_dump_json(indent=2), tc["expected_criteria"])
        except Exception as e:
            if "ACC-9999" in tc["input"] and isinstance(e, ValueError):
                eval_res = EvalResult(task="TAM Summariser", test_case=tc["description"], passed=True, quality_score=1.0, reasoning="Successfully rejected missing account data.")
            else:
                eval_res = EvalResult(task="TAM Summariser", test_case=tc["description"], passed=False, quality_score=0.0, reasoning=str(e))
        results.append(eval_res)
        
    with open("eval_report.json", "w") as f:
        json.dump([r.model_dump() for r in results], f, indent=2)
        
    print("Evaluation Complete. Results saved to eval_report.json")
    
if __name__ == "__main__":
    run_evals()
