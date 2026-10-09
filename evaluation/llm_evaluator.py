"""
LLM Output Evaluator — Tunisian Tax Optimization System
========================================================

Evaluates 4 metrics on every system run:
  1. Factual Accuracy   — do report numbers match calculator output?
  2. Hallucination Rate — does LLM invent inapplicable laws or strategies?
  3. Strategy Relevance — are strategies applicable to the user profile?
  4. Report Coherence   — is the report consistent with simulation results?

Usage:
    python evaluation/llm_evaluator.py
    
Results saved to: evaluation/llm_evaluation_results.json
"""

import sys
import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from tax_calculator_employee import (
    load_tax_rates,
    calculate_employee_taxes,
    calculate_freelancer_taxes,
)

rates = load_tax_rates()

# ── Test cases for LLM evaluation ─────────────────────────────────────────────
# Each case includes profile + expected calculator values
# LLM output is evaluated against these ground truths

EVAL_CASES = [
    {
        "id": "EVAL_001",
        "desc": "Salarié célibataire 30,000 DT — strategies must be expense_deductions only",
        "profile": {
            "income_type": "employee",
            "gross_annual": 30000.0,
            "gross_monthly": 2500.0,
            "family_status": "single",
            "children_count": 0,
            "deductions": {},
            "expenses": {},
        },
        "rules": {
            "forbidden_strategy_types": ["regime_change"],
            "forbidden_keywords": [
                "micro-enterprise", "SUARL", "forfaitaire",
                "micro enterprise", "regime change"
            ],
            "currency_must_be": "DT",
            "forbidden_currencies": ["$", "USD", "DZD", "dollar"],
        },
    },
    {
        "id": "EVAL_002",
        "desc": "Freelancer célibataire 36,000 DT — regime_change allowed",
        "profile": {
            "income_type": "freelancer",
            "gross_annual": 36000.0,
            "gross_monthly": 3000.0,
            "family_status": "single",
            "children_count": 0,
            "deductions": {},
            "expenses": {},
        },
        "rules": {
            "forbidden_strategy_types": [],
            "forbidden_keywords": [],
            "currency_must_be": "DT",
            "forbidden_currencies": ["$", "USD", "DZD", "dollar"],
        },
    },
    {
        "id": "EVAL_003",
        "desc": "Salarié marié 2 enfants 45,000 DT — no regime_change, savings realistic",
        "profile": {
            "income_type": "employee",
            "gross_annual": 45000.0,
            "gross_monthly": 3750.0,
            "family_status": "married_with_children",
            "children_count": 2,
            "deductions": {},
            "expenses": {},
        },
        "rules": {
            "forbidden_strategy_types": ["regime_change"],
            "forbidden_keywords": [
                "micro-enterprise", "SUARL", "forfaitaire"
            ],
            "currency_must_be": "DT",
            "forbidden_currencies": ["$", "USD", "DZD", "dollar"],
        },
    },
    {
        "id": "EVAL_004",
        "desc": "Freelancer marié 2 enfants 60,000 DT — high income, regime_change valid",
        "profile": {
            "income_type": "freelancer",
            "gross_annual": 60000.0,
            "gross_monthly": 5000.0,
            "family_status": "married_with_children",
            "children_count": 2,
            "deductions": {},
            "expenses": {},
        },
        "rules": {
            "forbidden_strategy_types": [],
            "forbidden_keywords": [],
            "currency_must_be": "DT",
            "forbidden_currencies": ["$", "USD", "DZD", "dollar"],
        },
    },
    {
        "id": "EVAL_005",
        "desc": "Salarié célibataire 60,000 DT haut revenu — no regime_change",
        "profile": {
            "income_type": "employee",
            "gross_annual": 60000.0,
            "gross_monthly": 5000.0,
            "family_status": "single",
            "children_count": 0,
            "deductions": {},
            "expenses": {},
        },
        "rules": {
            "forbidden_strategy_types": ["regime_change"],
            "forbidden_keywords": [
                "micro-enterprise", "SUARL", "forfaitaire"
            ],
            "currency_must_be": "DT",
            "forbidden_currencies": ["$", "USD", "DZD", "dollar"],
        },
    },
]


# ── Calculator ground truth ────────────────────────────────────────────────────

def get_ground_truth(profile: dict) -> dict:
    """Get correct tax values from deterministic calculator."""
    if profile["income_type"] == "employee":
        data = {
            "gross_monthly": profile["gross_monthly"],
            "family_status": profile["family_status"],
            "children_count": profile["children_count"],
        }
        result = calculate_employee_taxes(data, rates)
        return {
            "irpp_annual": round(result["tax_breakdown"]["irpp_annual"], 2),
            "cnss_annual": round(result["deductions"]["cnss_annual"], 2),
            "net_monthly": round(result["net_monthly"], 2),
        }
    else:
        data = {
            "revenue_monthly": profile["gross_monthly"],
            "family_status": profile["family_status"],
            "children_count": profile["children_count"],
        }
        result = calculate_freelancer_taxes(data, rates)
        return {
            "irpp_annual": round(result["tax_breakdown"]["irpp_annual"], 2),
            "cnss_annual": round(result["tax_breakdown"]["cnss_annual"], 2),
            "net_monthly": round(result["net_monthly"], 2),
        }


# ── Metric 1: Factual Accuracy ─────────────────────────────────────────────────

def evaluate_factual_accuracy(
    simulation: dict,
    report: str,
    ground_truth: dict,
    tolerance_pct: float = 0.05,
) -> dict:
    """
    Check if the numbers in simulation and report match calculator ground truth.
    Tolerance: 5% deviation allowed (rounding, minor differences).
    """
    issues = []
    score = 100

    # Check simulation current_tax vs ground truth irpp_annual
    sim_tax = simulation.get("current_tax", 0)
    expected_tax = ground_truth["irpp_annual"]
    if expected_tax > 0:
        diff_pct = abs(sim_tax - expected_tax) / expected_tax
        if diff_pct > tolerance_pct:
            issues.append(
                f"current_tax mismatch: simulation={sim_tax:.2f}, "
                f"calculator={expected_tax:.2f}, diff={diff_pct:.1%}"
            )
            score -= 40

    # Check report mentions correct IRPP order of magnitude
    # Extract all numbers from report that look like tax amounts
    numbers_in_report = re.findall(r'\b(\d[\d,\.]+)\s*(?:DT|TND|dinars?)\b', report, re.I)
    parsed_numbers = []
    for n in numbers_in_report:
        try:
            parsed_numbers.append(float(n.replace(",", "")))
        except ValueError:
            pass

    # The correct IRPP should appear somewhere in the report
    if parsed_numbers and expected_tax > 100:
        closest = min(parsed_numbers, key=lambda x: abs(x - expected_tax))
        diff_pct = abs(closest - expected_tax) / expected_tax
        if diff_pct > 0.10:  # 10% tolerance for report numbers
            issues.append(
                f"Report numbers don't match IRPP: "
                f"closest={closest:.2f}, expected={expected_tax:.2f}"
            )
            score -= 20

    return {
        "score": max(0, score),
        "issues": issues,
        "ground_truth_irpp": expected_tax,
        "simulation_irpp": sim_tax,
    }


# ── Metric 2: Hallucination Rate ──────────────────────────────────────────────

def evaluate_hallucination(
    strategies: list,
    report: str,
    rules: dict,
) -> dict:
    """
    Detect hallucinated content:
    - Forbidden strategy types for this profile
    - Forbidden keywords (wrong regime suggestions)
    - Wrong currency symbols
    - Impossible savings (> 50% of gross income)
    """
    issues = []
    hallucinations_found = 0
    total_checks = 0

    report_lower = report.lower()
    combined_text = report_lower + " ".join(
        s.get("description", "").lower() for s in strategies
    )

    # Check forbidden strategy types
    forbidden_types = rules.get("forbidden_strategy_types", [])
    for strategy in strategies:
        total_checks += 1
        stype = strategy.get("strategy_type", "")
        if stype in forbidden_types:
            issues.append(f"Forbidden strategy type '{stype}' for this profile")
            hallucinations_found += 1

    # Check forbidden keywords
    forbidden_kw = rules.get("forbidden_keywords", [])
    for kw in forbidden_kw:
        total_checks += 1
        if kw.lower() in combined_text:
            issues.append(f"Forbidden keyword found: '{kw}'")
            hallucinations_found += 1

    # Check wrong currencies
    forbidden_currencies = rules.get("forbidden_currencies", [])
    for curr in forbidden_currencies:
        total_checks += 1
        if curr in report:
            issues.append(f"Wrong currency symbol found: '{curr}'")
            hallucinations_found += 1

    # Check impossible savings
    for strategy in strategies:
        total_checks += 1
        savings = strategy.get("expected_savings", 0)
        # Will be cross-checked against gross_annual in full evaluator
        if savings < 0:
            issues.append(f"Negative savings: {savings}")
            hallucinations_found += 1

    hallucination_rate = (
        hallucinations_found / total_checks if total_checks > 0 else 0
    )
    score = max(0, 100 - int(hallucination_rate * 100))

    return {
        "score": score,
        "hallucination_rate": round(hallucination_rate, 3),
        "hallucinations_found": hallucinations_found,
        "total_checks": total_checks,
        "issues": issues,
    }


# ── Metric 3: Strategy Relevance ──────────────────────────────────────────────

def evaluate_strategy_relevance(
    strategies: list,
    profile: dict,
) -> dict:
    """
    Check if strategies are relevant to the profile:
    - At least 1 strategy generated
    - Strategies have non-empty descriptions
    - Savings are > 0
    - Strategy types match profile type
    """
    issues = []
    score = 100

    if not strategies:
        return {
            "score": 0,
            "issues": ["No strategies generated"],
            "strategy_count": 0,
        }

    income_type = profile["income_type"]
    gross_annual = profile["gross_annual"]

    for i, s in enumerate(strategies):
        desc = s.get("description", "").strip()
        savings = s.get("expected_savings", 0)
        stype = s.get("strategy_type", "")

        if not desc or len(desc) < 20:
            issues.append(f"Strategy {i+1}: description too short or empty")
            score -= 15

        if savings <= 0:
            issues.append(f"Strategy {i+1}: savings = {savings} (not positive)")
            score -= 10

        if savings > gross_annual * 0.5:
            issues.append(
                f"Strategy {i+1}: savings {savings} > 50% of gross income "
                f"({gross_annual * 0.5}) — likely hallucinated"
            )
            score -= 20

        # For employees: only expense_deductions should appear
        if income_type == "employee" and stype == "regime_change":
            issues.append(
                f"Strategy {i+1}: regime_change invalid for employee"
            )
            score -= 25

    return {
        "score": max(0, score),
        "strategy_count": len(strategies),
        "issues": issues,
    }


# ── Metric 4: Report Coherence ────────────────────────────────────────────────

def evaluate_report_coherence(
    report: str,
    simulation: dict,
    profile: dict,
) -> dict:
    """
    Check if the report is coherent with simulation results:
    - Report mentions the correct income type
    - Savings in report match simulation savings
    - Report is in correct language (French preferred)
    - Report has minimum length (not truncated)
    """
    issues = []
    score = 100

    if not report or len(report) < 200:
        return {
            "score": 0,
            "issues": ["Report too short or empty"],
            "report_length": len(report) if report else 0,
        }

    report_lower = report.lower()
    income_type = profile["income_type"]
    sim_savings = simulation.get("savings", 0)

    # Check income type mentioned
    if income_type == "employee":
        if "employee" not in report_lower and "salarié" not in report_lower and "employé" not in report_lower:
            issues.append("Report doesn't mention employee status")
            score -= 15
    else:
        if "freelance" not in report_lower and "indépendant" not in report_lower:
            issues.append("Report doesn't mention freelancer status")
            score -= 15

    # Check simulation savings reflected in report
    if sim_savings > 0:
        savings_str_variants = [
            str(int(sim_savings)),
            f"{sim_savings:.0f}",
            f"{sim_savings:.2f}",
        ]
        savings_found = any(v in report for v in savings_str_variants)
        if not savings_found:
            issues.append(
                f"Simulation savings {sim_savings:.2f} DT not found in report"
            )
            score -= 20

    # Check minimum report quality — must have sections
    required_sections = ["stratégie", "strategy", "risque", "risk", "recommand"]
    sections_found = sum(1 for s in required_sections if s in report_lower)
    if sections_found < 2:
        issues.append(f"Report missing key sections (found {sections_found}/5)")
        score -= 20

    # Check report not just disclaimers
    disclaimer_only = all(
        phrase in report_lower
        for phrase in ["consult", "professional", "not professional advice"]
    ) and len(report) < 500
    if disclaimer_only:
        issues.append("Report contains only disclaimers, no real content")
        score -= 30

    return {
        "score": max(0, score),
        "report_length": len(report),
        "issues": issues,
    }


# ── Full evaluator ────────────────────────────────────────────────────────────

def evaluate_run(
    case_id: str,
    profile: dict,
    strategies: list,
    simulation: dict,
    risks: list,
    report: str,
    rules: dict,
) -> dict:
    """Run all 4 metrics on a single system output."""

    ground_truth = get_ground_truth(profile)

    # Guard against None simulation (system failed silently)
    if simulation is None:
        simulation = {"current_tax": 0, "optimized_tax": 0, "savings": 0}
    if not report:
        report = ""
    if not strategies:
        strategies = []

    m1 = evaluate_factual_accuracy(simulation, report, ground_truth)
    m2 = evaluate_hallucination(strategies, report, rules)
    m3 = evaluate_strategy_relevance(strategies, profile)
    m4 = evaluate_report_coherence(report, simulation, profile)

    overall = round(
        (m1["score"] + m2["score"] + m3["score"] + m4["score"]) / 4, 1
    )

    return {
        "case_id": case_id,
        "overall_score": overall,
        "metrics": {
            "factual_accuracy": m1,
            "hallucination": m2,
            "strategy_relevance": m3,
            "report_coherence": m4,
        },
        "ground_truth": ground_truth,
    }


# ── Runner — calls the actual system ─────────────────────────────────────────

def run_system_on_case(case: dict) -> dict | None:
    """
    Run the full tax optimization system on a case.
    Returns the final state dict or None if failed.
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()

    try:
        from agents.langgraph_agents import (
            fiscal_strategy_agent,
            simulation_optimization_agent,
            risk_compliance_agent,
            explanation_reporting_agent,
        )
        from agents.state_schema import TaxOptimizationState

        # Build state with pre-filled profile — bypass LangGraph routing
        # and call agents directly in sequence
        state: TaxOptimizationState = {
            "user_input": "",
            "financial_profile": case["profile"],
            "strategies": [],
            "selected_strategy": None,
            "simulation": None,
            "risks": [],
            "report": "",
            "current_agent": "",
            "messages": [],
            "current_question_index": 0,
            "questions": [],
            "answers": {},
            "questioning_complete": True,
            "next_question": None,
        }

        # Call each agent directly — no graph routing needed
        print("    → strategy...", end=" ", flush=True)
        state = fiscal_strategy_agent(state)
        print("OK", end=" ", flush=True)

        print("→ simulation...", end=" ", flush=True)
        state = simulation_optimization_agent(state)
        print("OK", end=" ", flush=True)

        print("→ risk...", end=" ", flush=True)
        state = risk_compliance_agent(state)
        print("OK", end=" ", flush=True)

        print("→ report...", end=" ", flush=True)
        state = explanation_reporting_agent(state)
        print("OK")

        return {
            "strategies":        state.get("strategies", []),
            "simulation":        state.get("simulation", None),
            "risks":             state.get("risks", []),
            "report":            state.get("report", ""),
            "financial_profile": state.get("financial_profile", case["profile"]),
        }

    except Exception as e:
        print(f"  System error on {case['id']}: {e}")
        return None


# ── Main evaluation loop ──────────────────────────────────────────────────────

def run_evaluation(
    delay_between_cases: int = 30,
    save_path: str = "evaluation/llm_evaluation_results.json",
):
    """
    Run evaluation on all cases with delay between each to avoid rate limits.

    Args:
        delay_between_cases: seconds to wait between API calls
        save_path: where to save results
    """
    print("=" * 65)
    print("  LLM EVALUATION — Tunisian Tax Optimization System")
    print(f"  {len(EVAL_CASES)} cases | 4 metrics each")
    print(f"  Delay between cases: {delay_between_cases}s (rate limit protection)")
    print("=" * 65)

    all_results = []
    total_score = 0
    failed_cases = 0

    for i, case in enumerate(EVAL_CASES):
        print(f"\n[{i+1}/{len(EVAL_CASES)}] {case['id']} — {case['desc'][:50]}...")

        # Run system
        print("  Running system...", end=" ", flush=True)
        system_output = run_system_on_case(case)

        if system_output is None:
            print("FAILED")
            failed_cases += 1
            all_results.append({
                "case_id": case["id"],
                "status": "FAILED",
                "overall_score": 0,
            })
            continue

        print("OK")
    
        # Evaluate output
        result = evaluate_run(
            case_id=case["id"],
            profile=case["profile"],
            strategies=system_output.get("strategies", []),
            simulation=system_output.get("simulation", {}),
            risks=system_output.get("risks", []),
            report=system_output.get("report", ""),
            rules=case["rules"],
        )
        result["status"] = "OK"
        all_results.append(result)
        total_score += result["overall_score"]

        # Print summary
        m = result["metrics"]
        print(f"  Overall: {result['overall_score']:.1f}/100")
        print(f"  Factual accuracy  : {m['factual_accuracy']['score']}/100  "
              f"(IRPP: calc={result['ground_truth']['irpp_annual']:.0f} "
              f"sim={m['factual_accuracy']['simulation_irpp']:.0f})")
        print(f"  Hallucination     : {m['hallucination']['score']}/100  "
              f"(rate={m['hallucination']['hallucination_rate']:.1%})")
        print(f"  Strategy relevance: {m['strategy_relevance']['score']}/100  "
              f"({m['strategy_relevance']['strategy_count']} strategies)")
        print(f"  Report coherence  : {m['report_coherence']['score']}/100  "
              f"({m['report_coherence']['report_length']} chars)")

        # Print issues if any
        all_issues = (
            m["factual_accuracy"]["issues"]
            + m["hallucination"]["issues"]
            + m["strategy_relevance"]["issues"]
            + m["report_coherence"]["issues"]
        )
        if all_issues:
            print("  Issues:")
            for issue in all_issues[:5]:  # max 5 issues shown
                print(f"    ⚠  {issue}")

        # Wait between cases to avoid rate limits
        if i < len(EVAL_CASES) - 1:
            print(f"  Waiting {delay_between_cases}s before next case...", end=" ")
            time.sleep(delay_between_cases)
            print("done")

    # Final summary
    successful = len(EVAL_CASES) - failed_cases
    avg_score = total_score / successful if successful > 0 else 0

    print("\n" + "=" * 65)
    print("  EVALUATION SUMMARY")
    print("=" * 65)
    print(f"  Cases run     : {successful}/{len(EVAL_CASES)}")
    print(f"  Failed        : {failed_cases}")
    print(f"  Average score : {avg_score:.1f}/100")
    print()

    # Per-metric averages
    metric_names = ["factual_accuracy", "hallucination", "strategy_relevance", "report_coherence"]
    for mn in metric_names:
        scores = [
            r["metrics"][mn]["score"]
            for r in all_results
            if r.get("status") == "OK"
        ]
        avg = sum(scores) / len(scores) if scores else 0
        print(f"  {mn:<25s}: {avg:.1f}/100")

    # Save full results
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "system": "Tunisian Tax Optimization Multi-Agent",
        "total_cases": len(EVAL_CASES),
        "successful": successful,
        "failed": failed_cases,
        "average_score": round(avg_score, 1),
        "metric_averages": {
            mn: round(
                sum(
                    r["metrics"][mn]["score"]
                    for r in all_results
                    if r.get("status") == "OK"
                ) / max(successful, 1),
                1,
            )
            for mn in metric_names
        },
        "cases": all_results,
    }

    out = Path(save_path)
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    print(f"\n  Full results saved: {save_path}")
    print(f"\n  This is your LLM evaluation baseline.")
    print(f"  Cite this in your research report as Section 4 — Evaluation.")
    return report_data


if __name__ == "__main__":
    # Default: 30s delay between cases to stay within Groq free tier limits
    # If you have a paid API key, reduce to 5s
    run_evaluation(delay_between_cases=30)