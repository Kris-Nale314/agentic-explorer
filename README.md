# 🚀 Agentic Explorer

**Demystifying aspects of Agentic AI in the context of RAG systems**

## 💡 What is Agentic AI 

Ever wondered why your carefully built RAG system still hallucinates despite your best efforts? You're not alone.

This repo is my lab  - comparing **traditional RAG pipelines** against **multi-agent "Agentic RAG" approaches** in a direct showdown. 

> *"RAG isn't just about retrieving chunks - it's about understanding document architecture and context flow."*

## 🔥 Why This Matters

Here is what I've found - that traditional RAG pipelines consistently fail in predictable ways:

- **Boundary Blindness**: Chunking that ignores natural document boundaries, destroying context
- **Entity Confusion**: Inability to track and disambiguate similar entities across documents
- **Context Fragmentation**: Loss of critical relationships between concepts
- **Reasoning Gaps**: Failure to connect related information that spans multiple chunks

These aren't theoretical problems - they're the reason your RAG system hallucinates dates, mixes up companies, or invents nonexistent relationships.

## 🧠 The Agentic RAG Crew

Instead of one model doing everything, Agentic RAG employs specialist agents:

| Agent | Role | Why It Matters |
|-------|------|----------------|
| **🔍 Boundary Detective** | Identifies natural document boundaries | Preserves critical context across chunks |
| **🔎 Entity Tracker** | Disambiguates and tracks entities | Prevents confusion between similar companies, people, or concepts |
| **🔗 Context Connector** | Finds relationships between segments | Ensures reasoning can span multiple chunks coherently |
| **⚖️ Analysis Judge** | Synthesizes insights from specialists | Creates coherent, accurate summaries from fragmented information |

## 💥 Core Features: The RAG Showdown

This repo lets you run head-to-head comparisons between traditional and agentic approaches:

- **Chunking Strategy Deathmatch**: Fixed-size chunking vs. boundary-aware segmentation
- **Retrieval Method Battle Royale**: Basic vector search vs. entity-aware, context-enhanced retrieval
- **Synthesis Showdown**: Single-prompt LLM vs. multi-agent collaborative analysis
- **Hallucination Hunter**: Identify and track factual inconsistencies between approaches

All with detailed metrics and visualizations so you can see *exactly* why one approach outperforms the other.

## 🧪 Interactive RAG Labs

1. **Chunking Strategy Lab**: Experiment with different chunking strategies on your own documents
2. **Retrieval Arena**: Compare search relevance between traditional and agentic approaches
3. **Agent Collaboration Explorer**: Step through the agent workflow and see how specialists contribute

## 📁 Project Structure

```
agentic-explorer/
├── processors/                 # Modular RAG Components
│   ├── document_processor.py   # Document handling
│   ├── chunking_processor.py   # Traditional & Agentic chunking
│   ├── embedding_processor.py  # Vector embedding generation
│   ├── index_processor.py      # Vector DB management
│   ├── retrieval_processor.py  # Search strategies
│   └── synthesis_processor.py  # Analysis approaches
├── agents/                     # The Agentic Dream Team
│   ├── boundary_detective.py   # Intelligent boundary detection
│   ├── entity_tracker.py       # Entity disambiguation
│   ├── context_connector.py    # Relationship mapping
│   └── analysis_judge.py       # Synthesis orchestration
├── run_demo.py                 # Run the RAG Showdown
└── ... (other standard files)
```

## 🛠️ Tech Stack

- **CrewAI**: For orchestrating multi-agent workflows
- **OpenAI**: GPT-3.5/4 for agent implementation
- **ChromaDB**: Vector storage and search
- **NLTK**: Natural language processing
- **Streamlit**: Interactive UI (coming soon!)

## 🧑‍💻 Quick Start

```bash
# Clone the repo
git clone https://github.com/kris-nale314/agentic-explorer.git
cd agentic-explorer

# Set up environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your API keys in .env
# OPENAI_API_KEY=your_key_here

# Run a basic comparison
python run_demo.py --document data/samples/mixed_earnings.txt --query "Dell revenue growth"
```

## 🔬 Show Me The Science!

Run your own head-to-head comparison:

```python
from run_demo import run_rag_showdown

# Compare traditional vs. agentic RAG
results = run_rag_showdown(
    file_path="your_document.pdf",
    chunking_strategies=["fixed_size", "boundary_aware"],
    search_query="financial performance of Dell"
)

# See why agentic RAG won
print(results["chunking_showdown"]["boundary_preservation_score"])
print(results["search_method_faceoff"]["relevance_comparison"])
print(results["hallucination_metrics"]["factual_consistency_score"])
```

## 🤝 Join The RAG Revolution!

This project is my sandbox for exploring better RAG architectures. Found it useful? Have ideas?

- **Star** this repo if you found it helpful
- **Fork** it to build your own experiments
- **Contribute** new processors, agents, or test datasets
- **Open issues** with your findings or challenges

---

*Built while surviving on coffee by Kris Naleszkiewicz | [LinkedIn](https://www.linkedin.com/in/kris-nale314/) | [Medium](https://medium.com/@kris_nale314)*

<div align="center">
  <i>"The problem isn't that AI hallucinates - it's that we're hallucinating about how AI works."</i>
</div>