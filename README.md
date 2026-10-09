# Tunisian Tax Optimization Multi-Agent System

An AI-powered system for legal tax optimization in Tunisia using multi-agent orchestration with LangGraph.

## Architecture

### Agents
1. **Financial Profiling Agent** - Structures user input into standardized financial profiles
2. **Fiscal Strategy Agent** - Generates optimization strategies using RAG on Tunisian tax laws
3. **Simulation & Optimization Agent** - Runs deterministic simulations of tax scenarios
4. **Risk & Compliance Agent** - Validates legal compliance and assesses risk levels
5. **Explanation & Reporting Agent** - Generates human-readable reports

### Data Pipeline
- **RAG System**: ChromaDB vector store with embedded Tunisian tax documents
- **Tax Calculator**: Deterministic computation engine for IRPP, CNSS, TVA
- **Orchestration**: LangGraph workflow with conditional logic and agent interaction

## Setup :

1. Install dependencies:
```bash
pip install -r requirements.txt
```


2. Set up environment:
```bash
cp .env.example .env
# Add your GROQ_API_KEY to .env
```


3. Run the data pipeline (if not already done):
```bash
python tunisia_tax_pipeline.py
```

4. Run the multi-agent system:
```bash
python run_agents.py
```

## Project Structure


```
├── agents/
│   ├── langgraph_agents.py    # LangGraph workflow definition
│   ├── state_schema.py        # TypedDict state schemas
│   └── prompts.py             # LLM prompts for agents
├── tunisia_tax_data/
│   ├── chroma_index/          # Vector database
│   ├── rates_config/          # Numeric tax rules
│   └── extracted_text/        # Raw document text
├── tunisia_tax_pipeline.py    # Data ingestion pipeline
├── tax_calculator_employee.py # Deterministic tax calculator
├── run_agents.py              # Main entry point
└── requirements.txt           # Dependencies
```

## Features

- **Multi-Agent Orchestration**: Agents collaborate through LangGraph with conditional flows
- **RAG Integration**: Retrieval-augmented generation using official Tunisian tax sources
- **Deterministic Calculations**: Accurate tax computations with progressive brackets
- **Compliance Validation**: Risk assessment against legal requirements
- **Human-Readable Reports**: Clear explanations of strategies and impacts


## Usage



The system takes user financial information and generates optimized tax strategies:

```python
from agents.langgraph_agents import tax_optimization_graph

result = tax_optimization_graph.invoke({
    "user_input": "I earn 60,000 DT annually, married with 2 children...",
    # ... other state fields
})
```


## Next Steps


- Add Streamlit/Gradio UI for user interaction
- Implement more sophisticated strategy simulation
- Add support for corporate tax optimization
- Integrate with Tunisian government APIs for validation
- Add comprehensive testing and validation suite