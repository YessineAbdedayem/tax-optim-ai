import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

# Import existing components
from tunisia_tax_pipeline import TunisiataxRetriever
from tax_calculator_employee import load_tax_rates, calculate_employee_taxes, calculate_freelancer_taxes

# Import our schemas and prompts
from .state_schema import TaxOptimizationState, FinancialProfile, OptimizationStrategy, SimulationResult, RiskAssessment
from .prompts import PROFILING_PROMPT, STRATEGY_GENERATION_PROMPT, SIMULATION_PROMPT, RISK_COMPLIANCE_PROMPT, REPORT_GENERATION_PROMPT

# Initialize components (lazy initialization)
retriever = None

def get_retriever():
    """Get retriever instance with lazy initialization and fallback"""
    global retriever
    if retriever is None:
        try:
            print("Initializing retriever (this may take a moment)...")
            retriever = TunisiataxRetriever()
            print("Retriever initialized successfully!")
        except Exception as e:
            print(f"Retriever initialization failed: {e}. Using fallback mode.")
            retriever = None  # Fallback to work without RAG
    return retriever

def get_llm():
    """Get LLM instance with proper API key loaded"""
    # Use environment-configurable Groq model name (set in .env or system env)
    model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set!")
    
    return ChatGroq(model_name=model_name, api_key=api_key, temperature=0.7, top_p=0.9 )

def financial_profiling_agent(state: TaxOptimizationState) -> TaxOptimizationState:
    """Agent 1: Structure raw user input into financial profile"""
    user_input = state["user_input"]
    llm = get_llm()

    prompt = PROFILING_PROMPT.format(user_input=user_input)
    response = llm.invoke([HumanMessage(content=prompt)])

    # Parse JSON response with improved error handling
    profile_data = parse_profile_from_response(response.content)
    state["financial_profile"] = profile_data

    state["current_agent"] = "profiling"
    return state

def fiscal_strategy_agent(state: TaxOptimizationState) -> TaxOptimizationState:
    """Agent 2: Generate optimization strategies using RAG"""
    profile = state["financial_profile"]
    llm = get_llm()
    retriever = get_retriever()

    # Retrieve relevant tax laws
    retriever = get_retriever()
    if retriever:
        query = f"tax optimization strategies for {profile['income_type']} with income {profile['gross_annual']} DT"
        retrieved_docs = retriever.query(query, domain="IRPP_IS", n=3)  # Reduced from 5 to 3
        # Limit the length of retrieved laws to avoid token limits
        retrieved_laws = "\n".join([doc["content"][:500] for doc in retrieved_docs])  # Limit each doc to 500 chars
    else:
        retrieved_laws = "General Tunisian tax optimization principles: Consider regime changes, expense deductions, and income restructuring options."

    prompt = STRATEGY_GENERATION_PROMPT.format(
        financial_profile=json.dumps(profile, indent=2),
        retrieved_laws=retrieved_laws
    )
    response = llm.invoke([HumanMessage(content=prompt)])

    # Parse strategies
    try:
        strategies_text = response.content
        strategies = parse_strategies_from_text(strategies_text)
        state["strategies"] = strategies
    except Exception as e:
        print(f"Strategy parsing error: {e}")
        state["strategies"] = []

    state["current_agent"] = "strategy"
    return state

def simulation_optimization_agent(state: TaxOptimizationState) -> TaxOptimizationState:
    """Agent 3: Simulate financial scenarios"""
    profile = state["financial_profile"]
    strategies = state["strategies"]

    rates = load_tax_rates()

    # Calculate current taxes
    if profile["income_type"] == "employee":
        current_result = calculate_employee_taxes({
            "gross_monthly": profile.get("gross_monthly", profile["gross_annual"] / 12),
            "family_status": profile["family_status"],
            "children_count": profile["children_count"]
        }, rates)
        current_tax = current_result["tax_breakdown"]["irpp_annual"]
    else:
        current_result = calculate_freelancer_taxes({
            "revenue_monthly": profile["gross_annual"] / 12,
            "revenue_annual": profile["gross_annual"],
            "family_status": profile["family_status"],
            "children_count": profile["children_count"]
        }, rates)
        current_tax = current_result["tax_breakdown"]["irpp_annual"]

    # For simplicity, simulate one strategy (first one)
    if strategies:
        strategy = strategies[0]
        # Apply some optimization logic (simplified)
        optimized_tax = current_tax * 0.8  # Assume 20% reduction
        savings = current_tax - optimized_tax

        state["simulation"] = {
            "current_tax": current_tax,
            "optimized_tax": optimized_tax,
            "savings": savings,
            "net_impact": savings,
            "breakdown": current_result
        }
        state["selected_strategy"] = strategy
    else:
        state["simulation"] = {
            "current_tax": current_tax,
            "optimized_tax": current_tax,
            "savings": 0,
            "net_impact": 0,
            "breakdown": current_result
        }

    state["current_agent"] = "simulation"
    return state

def risk_compliance_agent(state: TaxOptimizationState) -> TaxOptimizationState:
    """Agent 4: Assess compliance and risks"""
    strategies = state["strategies"]
    llm = get_llm()
    retriever = get_retriever()

    # Retrieve compliance laws
    retriever = get_retriever()
    if retriever:
        compliance_query = "tax compliance and penalties for optimization strategies"
        compliance_docs = retriever.query(compliance_query, domain="CDPF", n=3)
        compliance_laws = "\n".join([doc["content"] for doc in compliance_docs])
    else:
        compliance_laws = "General compliance principles: Ensure strategies comply with Tunisian tax laws and avoid aggressive tax avoidance."

    prompt = RISK_COMPLIANCE_PROMPT.format(
        strategies=json.dumps(strategies, indent=2),
        compliance_laws=compliance_laws
    )
    response = llm.invoke([HumanMessage(content=prompt)])

    # Parse risks
    try:
        risks_text = response.content
        risks = parse_risks_from_text(risks_text)
        state["risks"] = risks
    except Exception as e:
        print(f"Risk parsing error: {e}")
        state["risks"] = []

    state["current_agent"] = "risk"
    return state

def explanation_reporting_agent(state: TaxOptimizationState) -> TaxOptimizationState:
    """Agent 5: Generate final report"""
    llm = get_llm()
    
    prompt = REPORT_GENERATION_PROMPT.format(
        financial_profile=json.dumps(state["financial_profile"], indent=2),
        selected_strategy=json.dumps(state.get("selected_strategy", {}), indent=2),
        simulation=json.dumps(state.get("simulation", {}), indent=2),
        risks=json.dumps(state["risks"], indent=2)
    )
    response = llm.invoke([HumanMessage(content=prompt)])

    state["report"] = response.content
    state["current_agent"] = "reporting"
    return state

# Helper functions for parsing LLM responses
def parse_profile_from_response(response_text: str) -> Dict[str, Any]:
    """Parse financial profile from LLM response, handling various formats"""
    import re

    # First try to parse as direct JSON
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass

    # Try to extract JSON from markdown code blocks
    json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
    match = re.search(json_pattern, response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON-like content between curly braces
    brace_pattern = r'\{.*\}'
    match = re.search(brace_pattern, response_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Parse key-value pairs from text
    profile = {}
    lines = response_text.split('\n')

    for line in lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower().replace(' ', '_')
            value = value.strip()

            # Map common keys
            if 'income_type' in key or 'type' in key:
                profile['income_type'] = value.lower() if 'employee' in value.lower() else 'freelancer'
            elif 'gross_annual' in key or 'annual' in key:
                try:
                    profile['gross_annual'] = float(re.sub(r'[^\d.]', '', value))
                except:
                    profile['gross_annual'] = 50000
            elif 'family_status' in key or 'marital' in key:
                if 'married' in value.lower():
                    profile['family_status'] = 'married' if 'children' not in value.lower() else 'married_with_children'
                else:
                    profile['family_status'] = 'single'
            elif 'children' in key:
                try:
                    profile['children_count'] = int(re.sub(r'[^\d]', '', value))
                except:
                    profile['children_count'] = 0
            elif 'deductions' in key:
                profile['deductions'] = {}
            elif 'expenses' in key:
                profile['expenses'] = {}

    # Set defaults for missing fields
    profile.setdefault('income_type', 'employee')
    profile.setdefault('gross_annual', 50000)
    profile.setdefault('family_status', 'single')
    profile.setdefault('children_count', 0)
    profile.setdefault('deductions', {})
    profile.setdefault('expenses', {})

    return profile

def parse_strategies_from_text(text: str) -> List[OptimizationStrategy]:
    """Parse strategies from LLM response, handling both JSON and text formats"""
    import re

    # First try to parse as direct JSON
    try:
        strategies = json.loads(text.strip())
        if isinstance(strategies, list):
            return strategies
    except json.JSONDecodeError:
        pass

    # Try to extract JSON array from markdown code blocks
    json_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        try:
            strategies = json.loads(match.group(1))
            if isinstance(strategies, list):
                return strategies
        except json.JSONDecodeError:
            pass

    # Try to find JSON array between square brackets
    array_pattern = r'\[.*\]'
    match = re.search(array_pattern, text, re.DOTALL)
    if match:
        try:
            strategies = json.loads(match.group(0))
            if isinstance(strategies, list):
                return strategies
        except json.JSONDecodeError:
            pass

    # Fallback: create basic strategies from text
    strategies = []
    lines = text.strip().split('\n')

    current_strategy = {}
    for line in lines:
        line = line.strip()
        if line.startswith('Strategy') or line.startswith('**Strategy') or line.startswith('-'):
            if current_strategy and 'strategy_type' in current_strategy:
                strategies.append(current_strategy)
            current_strategy = {
                "strategy_type": "expense_deductions",
                "description": "",
                "expected_savings": 1000,
                "risk_level": "medium",
                "compliance_notes": "Consult tax professional"
            }
        elif ':' in line and len(line.split(':', 1)) == 2:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()

            if 'type' in key:
                if 'regime' in value.lower():
                    current_strategy["strategy_type"] = "regime_change"
                elif 'expense' in value.lower():
                    current_strategy["strategy_type"] = "expense_deductions"
                elif 'income' in value.lower():
                    current_strategy["strategy_type"] = "income_restructuring"
            elif 'description' in key:
                current_strategy["description"] = value
            elif 'saving' in key:
                try:
                    current_strategy["expected_savings"] = float(re.sub(r'[^\d.]', '', value))
                except:
                    current_strategy["expected_savings"] = 1000
            elif 'risk' in key:
                current_strategy["risk_level"] = value.lower() if value.lower() in ['low', 'medium', 'high'] else 'medium'
            elif 'compliance' in key or 'note' in key:
                current_strategy["compliance_notes"] = value

    if current_strategy and 'strategy_type' in current_strategy:
        strategies.append(current_strategy)

    # If no strategies found, create a default one
    if not strategies:
        strategies = [{
            "strategy_type": "expense_deductions",
            "description": "Take advantage of available expense deductions",
            "expected_savings": 1000,
            "risk_level": "low",
            "compliance_notes": "Ensure proper documentation and consult tax professional"
        }]

    return strategies

def parse_risks_from_text(text: str) -> List[RiskAssessment]:
    """Parse risk assessments from LLM response"""
    try:
        # First try to parse as JSON
        return json.loads(text)
    except json.JSONDecodeError:
        # If JSON fails, create basic risk assessments
        return [{
            "strategy_id": 0,
            "risk_level": "medium",
            "issues": ["Response format unclear - manual review recommended"],
            "recommendations": ["Consult with tax professional for detailed compliance review"]
        }]

# Conditional logic
def should_refine_strategy(state: TaxOptimizationState) -> str:
    """Decide if strategy needs refinement based on risk"""
    risks = state.get("risks", [])
    high_risk = any(risk.get("risk_level") == "high" for risk in risks)
    return "refine" if high_risk else "proceed"

# Build the graph
def create_tax_optimization_graph():
    workflow = StateGraph(TaxOptimizationState)

    # Add nodes
    workflow.add_node("profiling", financial_profiling_agent)
    workflow.add_node("strategy", fiscal_strategy_agent)
    workflow.add_node("simulation", simulation_optimization_agent)
    workflow.add_node("risk", risk_compliance_agent)
    workflow.add_node("reporting", explanation_reporting_agent)

    # Add edges
    workflow.set_entry_point("profiling")
    workflow.add_edge("profiling", "strategy")
    workflow.add_edge("strategy", "simulation")
    workflow.add_edge("simulation", "risk")

    # Conditional edge from risk to either strategy (refine) or reporting
    workflow.add_conditional_edges(
        "risk",
        should_refine_strategy,
        {
            "refine": "strategy",
            "proceed": "reporting"
        }
    )
    workflow.add_edge("reporting", END)

    return workflow.compile()

# Export the compiled graph
tax_optimization_graph = create_tax_optimization_graph()