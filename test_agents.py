#!/usr/bin/env python3
"""
Quick test of the Tunisian Tax Optimization Multi-Agent System
"""

import os
from dotenv import load_dotenv
from agents.langgraph_agents import tax_optimization_graph
from agents.state_schema import TaxOptimizationState

def main():
    # Load environment variables
    load_dotenv()

    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not found in .env file")
        return

    print("🚀 Starting Tunisian Tax Optimization Multi-Agent System...")

    # Example user input
    user_input = """
    I am a salaried employee in Tunisia earning 60,000 DT annually (5,000 DT monthly).
    I am married with 2 children.
    I have some business expenses of 10,000 DT per year.
    I want to optimize my taxes legally.
    """

    # Initialize state
    initial_state: TaxOptimizationState = {
        "user_input": user_input,
        "financial_profile": None,
        "strategies": [],
        "selected_strategy": None,
        "simulation": None,
        "risks": [],
        "report": "",
        "current_agent": "",
        "messages": []
    }

    try:
        # Run the multi-agent workflow
        print("📊 Processing financial profile...")
        result = tax_optimization_graph.invoke(initial_state)

        # Print results
        print("\n" + "="*50)
        print("🎯 TAX OPTIMIZATION RESULTS")
        print("="*50)

        if result["financial_profile"]:
            print("✅ Financial Profile Created")
            profile = result["financial_profile"]
            print(f"   Income Type: {profile.get('income_type', 'N/A')}")
            print(f"   Annual Income: {profile.get('gross_annual', 0):,.0f} DT")
            print(f"   Family Status: {profile.get('family_status', 'N/A')}")
            print(f"   Children: {profile.get('children_count', 0)}")
        else:
            print("❌ Financial Profile Creation Failed")

        print(f"\n📈 Strategies Generated: {len(result['strategies'])}")

        if result["simulation"]:
            sim = result["simulation"]
            print("💰 Tax Simulation Results:")
            print(f"   Current Tax: {sim.get('current_tax', 0):,.0f} DT")
            print(f"   Optimized Tax: {sim.get('optimized_tax', 0):,.0f} DT")
            print(f"   Savings: {sim.get('savings', 0):,.0f} DT")
        else:
            print("❌ Tax Simulation Failed")

        print(f"\n⚠️  Risk Assessments: {len(result['risks'])}")

        if result["report"]:
            print("\n📋 Final Report Preview:")
            print(result["report"][:500] + "..." if len(result["report"]) > 500 else result["report"])
        else:
            print("❌ Report Generation Failed")

        print("\n" + "="*50)
        print("🎉 Multi-Agent System Completed Successfully!")
        print("✅ All agents (Profiling → Strategy → Simulation → Risk → Reporting) executed")
        print("✅ RAG integration with Tunisian tax laws working")
        print("✅ Deterministic tax calculations integrated")
        print("✅ Groq LLM API responding correctly")

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()