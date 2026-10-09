#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from agents.langgraph_agents import tax_optimization_graph
from agents.state_schema import TaxOptimizationState

def main():
    load_dotenv()

    if not os.getenv("GROQ_API_KEY"):
        print("Please set GROQ_API_KEY in .env file")
        return

    initial_state: TaxOptimizationState = {
        "user_input": "",
        "financial_profile": None,
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
        "questioning_complete": False,
        "next_question": None
    }

    print("Starting Tax Optimization Workflow...\n")
    state = initial_state

    # Step 1 — Interactive questioning loop
    while True:
        result = tax_optimization_graph.invoke(state)
        if result.get("next_question"):
            print(result["next_question"])
            user_response = input("Your answer: ").strip()
            state = result.copy()
            state["user_input"] = user_response
        else:
            break

    # Step 2 — Run full pipeline once questioning is complete
    if not result.get("questioning_complete"):
        print("Profiling incomplete.")
        return

    final = tax_optimization_graph.invoke(result)

    # Step 3 — Display results once, cleanly
    print("\n" + "="*55)
    print("FINANCIAL PROFILE")
    print("="*55)
    profile = final.get("financial_profile", {})
    print(f"  Type         : {profile.get('income_type', 'N/A')}")
    print(f"  Annual income: {profile.get('gross_annual', 0):,.0f} DT")
    print(f"  Monthly      : {profile.get('gross_monthly', 0):,.0f} DT")
    print(f"  Family status: {profile.get('family_status', 'N/A')}")
    print(f"  Children     : {profile.get('children_count', 0)}")

    print("\n" + "="*55)
    print("STRATEGIES GENERATED")
    print("="*55)
    for i, s in enumerate(final.get("strategies", []), 1):
        print(f"  [{i}] {s.get('strategy_type','').upper()}")
        print(f"      {s.get('description','')[:100]}...")
        print(f"      Expected savings : {s.get('expected_savings', 0):,.0f} DT")
        print(f"      Risk             : {s.get('risk_level','N/A')}")

    print("\n" + "="*55)
    print("SIMULATION RESULTS")
    print("="*55)
    sim = final.get("simulation", {})
    print(f"  Current IRPP     : {sim.get('current_tax', 0):,.2f} DT")
    print(f"  Optimized IRPP   : {sim.get('optimized_tax', 0):,.2f} DT")
    print(f"  Annual savings   : {sim.get('savings', 0):,.2f} DT")
    print(f"  CNSS annual      : {sim.get('current_cnss_annual', 0):,.2f} DT")
    print(f"  Note             : {sim.get('note', 'N/A')}")

    if sim.get("all_scenarios"):
        print("\n  All scenarios:")
        for sc in sim["all_scenarios"]:
            print(f"    Scenario {sc['strategy_index']+1}: "
                  f"{sc['strategy_type']} → "
                  f"savings {sc['savings']:,.2f} DT ({sc['note']})")

    print("\n" + "="*55)
    print("RISK ASSESSMENT")
    print("="*55)
    for r in final.get("risks", []):
        print(f"  Strategy {r.get('strategy_id', '?')} : "
              f"risk={r.get('risk_level','?').upper()}")
        for issue in r.get("issues", []):
            print(f"    Issue : {issue}")
        for rec in r.get("recommendations", []):
            print(f"    Rec   : {rec}")

    print("\n" + "="*55)
    print("FINAL REPORT")
    print("="*55)
    print(final.get("report", "No report generated."))

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Main entry point for the Tunisian Tax Optimization Multi-Agent System
"""

import os
from dotenv import load_dotenv
from agents.langgraph_agents import tax_optimization_graph
from agents.state_schema import TaxOptimizationState

def main():
    # Load environment variables
    load_dotenv()

    # Set OpenAI API key (in production, use environment variables)
    if not os.getenv("GROQ_API_KEY"):
        print("Please set GROQ_API_KEY in .env file")
        print("Example: GROQ_API_KEY=gsk-your-groq-key-here")
        return

    # Initialize state
    initial_state: TaxOptimizationState = {
        "user_input": "",
        "financial_profile": None,
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
        "questioning_complete": False,
        "next_question": None
    }

    # Interactive questioning loop
    print("Starting Tax Optimization Workflow...")
    state = initial_state
    
    while True:
        result = tax_optimization_graph.invoke(state)
        
        if result.get("next_question"):
            print(f"\n{result['next_question']}")
            user_response = input("Your answer: ").strip()
            state = result.copy()
            state["user_input"] = user_response
        else:
            # Profiling complete, continue to rest of workflow
            break
    
    # Continue with the rest of the workflow if needed
    if result.get("questioning_complete"):
        # Run the remaining agents
        final_result = tax_optimization_graph.invoke(result)
        
        # Print results
        print("\n=== FINANCIAL PROFILE ===")
        print(final_result["financial_profile"])

        print("\n=== GENERATED STRATEGIES ===")
        for strategy in final_result["strategies"]:
            print(f"- {strategy}")
        
        print("\n=== SIMULATION RESULTS ===")
        sim = final_result.get("simulation", {})
        print(f"Current Tax: {sim.get('current_tax', 0):.2f} DT")
        print(f"Optimized Tax: {sim.get('optimized_tax', 0):.2f} DT")
        print(f"Savings: {sim.get('savings', 0):.2f} DT")
        
        print("\n=== FINAL REPORT ===")
        print(final_result["report"])

    print("\n=== SIMULATION RESULTS ===")
    if result["simulation"]:
        sim = result["simulation"]
        print(f"Current Tax: {sim['current_tax']:.2f} DT")
        print(f"Optimized Tax: {sim['optimized_tax']:.2f} DT")
        print(f"Savings: {sim['savings']:.2f} DT")

    print("\n=== RISK ASSESSMENT ===")
    for risk in result["risks"]:
        print(f"- {risk}")

    print("\n=== FINAL REPORT ===")
    print(result["report"])

if __name__ == "__main__":
    main()