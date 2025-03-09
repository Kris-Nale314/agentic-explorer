# 🚀 Agentic Explorer

**Demystifying multi-agent AI by showing what's happening under the hood**

<div align="center">
  <img  alt="Agentic Explorer Banner" width="80%">
</div>

## 💡 The Big Idea

**Data is messy. AI is not magic. We're showing you how they work together.**

Agentic Explorer is an educational platform that reveals what's *actually* happening when AI agents collaborate to solve real problems with real data. By peeling back the layers of abstraction, we help you understand why:

> *"Your data strategy is as important as your solution architecture."*

We're on a mission to:
1. **Bust AI myths**: No, language models don't "understand" your documents
2. **Show failure modes**: See how easily context gets fragmented or lost
3. **Demonstrate real solutions**: Explore techniques that actually work
4. **Make the invisible visible**: Watch AI agents collaborate in real-time

## 🔥 Why This Matters

Every time an AI system hallucinates, misunderstands context, or gets confused by mixed documents, it's not (just) because "AI is dumb." It's because we're feeding these systems information in ways that break their ability to reason effectively.

Agentic Explorer tackles fundamental challenges that plague AI systems in the real world:

- **Document Boundary Problems**: When did the quarterly report end and the news article begin?
- **Context Fragmentation**: How chunking strategies destroy relationships between concepts
- **Entity Confusion**: Why AI gets confused when multiple companies are discussed
- **Temporal Disorientation**: How time references get mixed up across document boundaries

These aren't abstract academic issues—they're the root causes of most AI system failures in production!

## 🧠 Meet Our Crew of AI Agents

<table>
  <tr>
    <td align="center" width="200"><h3>🔍</h3></td>
    <td><b>Boundary Detective</b><br><i>"This paragraph doesn't belong with the others... I can sense it!"</i><br>Specializes in detecting document boundaries, identifying format shifts, and classifying document types in mixed content.</td>
  </tr>
  <tr>
    <td align="center"><h3>📊</h3></td>
    <td><b>Document Analyzer</b><br><i>"Let me measure this text and break it down for you..."</i><br>Computes metrics, extracts structures, and identifies patterns across documents.</td>
  </tr>
  <tr>
    <td align="center"><h3>📚</h3></td>
    <td><b>Summarization Manager</b><br><i>"I'll try several summarization strategies and show you the differences..."</i><br>Orchestrates multiple summarization approaches and compares their effectiveness.</td>
  </tr>
  <tr>
    <td align="center"><h3>⚖️</h3></td>
    <td><b>Analysis Judge</b><br><i>"After weighing all the evidence..."</i><br>Synthesizes information from all sources to provide balanced, contextual insights.</td>
  </tr>
</table>

## 📋 Core Features

- **Multi-Strategy Document Processing**: Compare traditional chunking vs. intelligent boundary detection
- **Comparative Summarization**: See how full-document, partition-based, and entity-focused approaches differ
- **Boundary Detection Visualization**: Actually see where document boundaries are and the confidence in each detection
- **Agent Communication Tracing**: Follow the flow of information between AI agents

## 🧪 Educational Modules

1. **Document Boundary Lab**: Upload your own mixed documents and see if our system can detect the boundaries
2. **Summarization Strategy Analyzer**: Compare different summarization approaches on the same document
3. **Context Preservation Tester**: Visualize how different chunking strategies preserve or destroy context

## 📁 Project Structure & Design Philosophy

```
agentic-explorer/
├── data/
│   ├── samples/                # Example documents for testing
│   ├── data_generation.py      # Creates test datasets
│   └── dev_eval_files.json     # Test documents
├── agents/
│   ├── base_agent.py           # Common agent functionality
│   ├── boundary_detective.py   # Document boundary detection
│   ├── document_analyzer.py    # Document metrics and structure
│   ├── summarization_manager.py # Multi-strategy summarization
│   └── analysis_judge.py       # Evaluation and synthesis
├── processors/
│   ├── document_processor.py   # Core document handling
│   ├── partitioning.py         # Document segmentation strategies
│   ├── summarization.py        # Summarization algorithms
│   └── text_utils.py           # Text preprocessing utilities
├── tools/
│   ├── fmp_tool.py             # Financial data API
│   ├── visualization_tool.py   # For rendering visualizations
│   └── document_tools.py       # Document manipulation tools
├── tests/
│   ├── test_agents.py
│   ├── test_processors.py
│   └── test_integration.py
├── config.py                   # Configuration management
├── analysis.py                 # CrewAI orchestration and task definitions
├── orchestration.py            # High-level system orchestration
├── main.py                     # Main Streamlit app (focused on functionality first)
├── requirements.txt            # Project dependencies
├── .env                        # Environment variables (gitignored)
├── .gitignore                  # Git ignore file
└── __init__.py                 # Package initialization
```

### Why This Architecture Matters

Each component in our architecture addresses specific challenges in building safe, reliable AI systems:

1. **Separation of Processors from Agents**
   - Processors focus on document transformation and analysis
   - Agents focus on reasoning and synthesis
   - This separation makes the system more maintainable and easier to reason about

2. **Multi-Strategy Approach**
   - No single approach works for all document types
   - By comparing multiple strategies, we show why adaptability matters
   - This reveals the importance of "AI strategy" over blind application

3. **Explicit Boundary Detection**
   - Most RAG systems ignore document boundaries, causing hallucinations
   - Our explicit boundary detection shows why this matters for accuracy
   - By making boundaries visible, we make better systems

4. **Educational Transparency**
   - Systems show their reasoning, not just their outputs
   - Confidence levels are explicit, not hidden
   - Comparison between approaches reveals trade-offs

## 🛠️ Technology Stack

This project is built with:

- **[OpenAI](https://openai.com/)**: GPT-3.5 Turbo for cost-effective agent implementation
- **[NLTK](https://www.nltk.org/)**: For natural language processing
- **[Streamlit](https://streamlit.io/)**: For the interactive web interface (coming soon)
- **[Financial Modeling Prep API](https://site.financialmodelingprep.com/developer)**: For clean financial data

## 🧑‍💻 Development Notes

### Getting Started

```bash
# Clone the repository
git clone https://github.com/kris-nale314/agentic-explorer.git
cd agentic-explorer

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (.env file)
OPENAI_API_KEY=your_openai_api_key
FMP_API_KEY=your_fmp_api_key

# Run tests
python -m tests.test_document_analysis

# Process a sample document
python -m orchestration
```

### Running the Analysis Pipeline

```python
from orchestration import run_analysis

# Analyze a document with all available strategies
results = run_analysis(
    file_path="data/dev_eval_files.json", 
    analysis_type="comprehensive"
)

# View recommended summarization approach
recommendation = results["multi_strategy_summary"]["recommended_approach"]
print(f"Recommended approach: {recommendation['recommended_approach']}")
print(f"Explanation: {recommendation['explanation']}")
```

## 🔮 The Road Ahead

We're actively developing additional modules:

- **Agent Visualization**: See the agent communication network in real-time
- **Error Analysis**: Understand common AI reasoning failures
- **Custom Agent Builder**: Design your own specialized agents
- **Streamlit Interface**: Interactive exploration of all concepts

## 🤝 Contribute

Fascinated by this project? We'd love your help! Areas where we're looking for contributions:

- Additional document processing strategies
- Improved boundary detection algorithms
- Educational visualizations
- Documentation and tutorials

## 🧠 Why We Built This

Every day, AI systems are deployed with fundamental flaws in how they process and understand documents. By making these invisible problems visible, we hope to inspire better approaches to AI system design.

Because when AI systems fail, it's rarely about the models—it's almost always about how we're feeding them information.

---

*Made with ❤️ by Kris Naleszkiewicz | [LinkedIn](https://www.linkedin.com/in/kris-nale314/) | [Medium](https://medium.com/@kris_nale314)*

<div align="center">
  <i>"If I had asked people what they wanted, they would have said faster horses."</i><br>
  — Henry Ford (but about AI, probably)
</div>