from typing import TypedDict, List, Dict, Any, Optional

class FinancialProfile(TypedDict):
    income_type: str  # "employee" or "freelancer"
    gross_annual: float
    gross_monthly: Optional[float]
    family_status: str  # "single", "married", "married_with_children"
    children_count: int
    deductions: Dict[str, float]
    expenses: Dict[str, float]

class OptimizationStrategy(TypedDict):
    strategy_type: str  # "regime_change", "expense_deductions", "income_restructuring"
    description: str
    expected_savings: float
    risk_level: str
    compliance_notes: str

class SimulationResult(TypedDict):
    current_tax: float
    optimized_tax: float
    savings: float
    net_impact: float
    breakdown: Dict[str, Any]

class RiskAssessment(TypedDict):
    strategy_id: str
    risk_level: str  # "low", "medium", "high"
    issues: List[str]
    recommendations: List[str]

class TaxOptimizationState(TypedDict):
    user_input: str
    financial_profile: Optional[FinancialProfile]
    strategies: List[OptimizationStrategy]
    selected_strategy: Optional[OptimizationStrategy]
    simulation: Optional[SimulationResult]
    risks: List[RiskAssessment]
    report: str
    current_agent: str
    messages: List[Dict[str, Any]]  # For LangGraph messages
    current_question_index: int
    questions: List[str]
    answers: Dict[str, Any]
    questioning_complete: bool
    next_question: Optional[str]