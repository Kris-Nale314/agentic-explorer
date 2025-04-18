![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![LangChain](https://img.shields.io/badge/LangChain-3178C6?style=for-the-badge&logo=langchain&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-FF5A5F?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMNCA4djhsOCA2bDgtNlY4bC04LTZ6IiBmaWxsPSIjZmZmIi8+PC9zdmc+)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

# 🚀 Agentic Explorer

<div align="center">
  <img src="docs/images/agentic_explorer_logo.svg" alt="Agentic Explorer Logo" width="400" height="400">
</div>

### **An Interactive Playground for Financial Multi-Agent Systems**

> *"In the world of AI agents, failure is just another data point. Unless it's catastrophic. Then it's a resume builder."*

## 🧠 What Is This Thing?

Agentic Explorer is an experimental framework for building, testing, and visualizing multi-agent LLM systems focused on financial analysis. It's a sandbox where you can:

- Watch specialized AI agents collaborate to analyze financial news and stock data
- See how different agent configurations affect analysis quality and cost
- Experiment with deliberate "broken" agents to observe failure cascades
- Learn practical lessons about multi-agent system design

Built on [CrewAI](https://github.com/crewai/crewai), this repo focuses on transparency and educational value rather than just getting the "right" answer. It's designed to reveal the inner workings of agent collaboration and help you understand the strengths and pitfalls of agentic systems.

## 💡 Why This Matters

Multi-agent LLM systems are increasingly common in enterprise settings, but their inner workings often remain a black box. This can lead to:

- Unpredictable failure modes
- Unclear cost-benefit tradeoffs
- Difficulty diagnosing issues
- Challenges in system optimization

Agentic Explorer provides a transparent view into how these systems work, using financial news analysis as a concrete and intuitive example. By making agent interactions visible and measurable, it demystifies the "magic" of collaborative AI.

## 🤖 The Agent Ecosystem

The system deploys a customizable team of specialized agents:

| Agent | Function | Special Power |
|-------|----------|---------------|
| **strategyAgent** | Designs analysis workflow & coordinates team | Meta-cognition |
| **newsAgent** | Analyzes news sentiment & extracts claims | Language pattern recognition |
| **tickerAgent** | Processes stock price movements & volumes | Numerical correlation detection |
| **secAgent** | Reviews SEC filings & company disclosures | Regulatory interpretation |
| **industryAgent** | Provides sector context & competitive analysis | Comparative reasoning |
| **devilsAdvocateAgent** | Challenges mainstream analysis & assumptions | Contrarian thinking |
| **brokeAgent** | Deliberately introduces errors (for educational purposes) | Controlled failure demonstration |
| **judgeAgent** | Evaluates all inputs & provides final assessment | Synthetic reasoning |

## 🧪 Interactive Experiments

Agentic Explorer supports several analysis types designed to showcase different aspects of multi-agent systems:

### 1. Prediction Challenge

Select a company, a date range, and a "prediction date" in the middle. Agents analyze data before the prediction date to forecast what will happen afterward, then validate against what actually occurred.

```bash
python run_explorer.py --company NVDA --start 2023-01-01 --predict 2023-06-15 --end 2023-12-31
```

### 2. Agent Configuration Comparisons

Compare different agent combinations to see how team composition affects analysis quality and cost:

```bash
python run_explorer.py --company TSLA --start 2023-01-01 --end 2023-06-30 --compare basic,full,minimal
```

### 3. Failure Mode Simulations

Introduce the brokeAgent with different error types to see how the system handles misinformation:

```bash
python run_explorer.py --company AAPL --start 2023-01-01 --end 2023-06-30 --broke-mode hallucination
```

### 4. Devil's Advocate Analysis

Run analysis with and without the devilsAdvocateAgent to see how constructive disagreement affects conclusions:

```bash
python run_explorer.py --company MSFT --start 2023-01-01 --end 2023-06-30 --devils-advocate
```

## 📈 Token Economy Tracking

A core feature is comprehensive token usage tracking and cost-benefit analysis:

```
┌──────────────────────────────────────────────────────────────────┐
│                 Agent Token Economy Dashboard                     │
├────────────────┬───────────┬─────────┬────────────┬──────────────┤
│ Agent          │ Tokens    │ Cost($) │ Insights   │ Value/Token  │
├────────────────┼───────────┼─────────┼────────────┼──────────────┤
│ strategyAgent  │ 14,231    │ $0.28   │ (meta)     │ ⚙️ Orchestr. │
│ newsAgent      │ 28,450    │ $0.57   │ 12         │ ★★★★☆        │
│ tickerAgent    │ 15,230    │ $0.30   │ 8          │ ★★★☆☆        │
│ secAgent       │ 31,520    │ $0.63   │ 15         │ ★★★★★        │
│ industryAgent  │ 22,860    │ $0.46   │ 9          │ ★★☆☆☆        │
│ devilsAdvAgent │ 18,940    │ $0.38   │ 7          │ ★★★★☆        │
│ judgeAgent     │ 35,760    │ $0.72   │ 18         │ ★★★★★        │
├────────────────┼───────────┼─────────┼────────────┼──────────────┤
│ Total          │ 166,991   │ $3.34   │ 69         │ ★★★★☆        │
└────────────────┴───────────┴─────────┴────────────┴──────────────┘
```

This enables you to quantify the contribution of each agent and optimize system cost-effectiveness.

## 🔬 Implementation

### Data Organization

```
dataStore/
├── NVDA/
│   ├── ticker_data.csv             # Daily price and volume data
│   ├── filings/                    # 10-K, 10-Q and other SEC filings
│   │   ├── 10K_2023.txt
│   │   ├── 10Q_2023Q1.txt
│   │   └── ...
│   └── news/                       # News articles organized by date
│       ├── 2023-01-05_article1.txt
│       ├── 2023-01-08_article2.txt
│       └── ...
├── AAPL/
│   └── ...
└── market_data/
    └── index_data.csv              # Market index data for reference
```

### Installation

```bash
# Clone the repo
git clone https://github.com/Kris-Nale314/agentic-explorer.git
cd agentic-explorer

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

### Core Technical Features

- **CrewAI Integration**: Leverages CrewAI for agent orchestration and collaboration
- **Agent Interaction Logging**: Captures all inter-agent communications for review
- **Visualization Dashboard**: Interactive visuals of agent contributions and workflow
- **Configurable Analysis Types**: Multiple experiment templates built-in
- **Failure Mode Simulations**: Controlled introduction of errors for educational purposes

## 🔮 Broader Applications

While Agentic Explorer focuses on financial news analysis, the lessons learned have broader applications for any multi-agent LLM system, such as:

### Real-time Monitoring Systems

The techniques demonstrated here could inform design considerations for "always-on" monitoring systems that continuously process information streams across domains.

### Enterprise Decision Support

Understanding agent collaboration patterns helps build more reliable decision support systems in areas like supply chain management, customer intelligence, and strategic planning.

### Information Validation Frameworks

The approach to error detection and validation provides insights for building more robust information processing pipelines in any domain.

## 🧪 Future Development

Planned enhancements include:

- **Agent Specialization Evolution**: Agents that adapt their focus based on incoming data
- **Interactive Agent Debugging**: Tools to isolate and fix agent reasoning errors
- **Cross-domain Applications**: Extending the framework beyond financial analysis
- **Advanced Visualization**: More detailed views of agent reasoning processes
- **Custom Agent Creation**: Tools for users to design and deploy their own specialized agents

## 📚 Contributing

Contributions welcome! 

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Built while searching for meaning in stochastic parrots by Kris Naleszkiewicz | [LinkedIn](https://www.linkedin.com/in/kris-nale314/) | [Medium](https://medium.com/@kris_nale314)*

<div align="center">
  <i>"If you're not slightly embarrassed by your first multi-agent system, you waited too long to release it."</i>
</div>