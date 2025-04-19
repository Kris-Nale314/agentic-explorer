# 🚀 Agentic Explorer

<div align="center">
  <img src="docs/images/agentic_explorer_logo.svg" alt="Agentic Explorer Logo" width="400" height="400">
</div>

### **An Interactive Playground for Multi-Agent Intelligence Systems**

> *"Building a multi-agent system is like organizing a team of highly specialized experts who occasionally hallucinate their credentials."*

## 🧠 What Is This Thing?

Agentic Explorer is an experimental framework for building, testing, and visualizing multi-agent LLM systems focused on extracting meaningful insights from both structured and unstructured data. We're tackling the signal-versus-noise challenge in operational decision making, using public company data as our proving ground.

This framework serves as a sandbox where you can:

- Observe how specialized AI agents collaborate to transform diverse data sources into actionable intelligence
- Measure how different agent configurations affect analysis quality, cost, and accuracy
- Experiment with deliberately imperfect agents to understand system resilience
- Visualize the inner workings of multi-agent systems to demystify how they actually function

Using financial data as our test case (stock prices, earnings transcripts, SEC filings), we're exploring broader questions about how multi-agent systems can help organizations identify early warning signals before they become obvious in traditional metrics.

Built on [CrewAI](https://github.com/crewai/crewai), this project prioritizes transparency and educational value over black-box solutions. By making every agent interaction visible and measurable, we're creating both a practical tool and a learning platform for understanding the true capabilities and limitations of collaborative AI.

## 💡 Why This Matters

Multi-agent LLM systems are increasingly common in enterprise settings, but their inner workings often remain a black box. This can lead to:

- Unpredictable failure modes
- Unclear cost-benefit tradeoffs
- Difficulty diagnosing issues
- Challenges in system optimization

Agentic Explorer provides a transparent view into how these systems work, using financial analysis as a concrete and intuitive example. By making agent interactions visible and measurable, it demystifies the "magic" of collaborative AI.

## 🔍 The "Last Mile" Intelligence Advantage

A key concept we're exploring is how unstructured data can serve as the "last mile" connector that provides early warning signals before they manifest in structured metrics.

Using a wind/leaves analogy:
- We don't directly measure the wind (future business impacts)
- We observe the leaves moving (early indicators in unstructured data)
- We infer wind direction and strength (potential business impacts)
- We compare to historical patterns (calibration and verification)

This approach emphasizes awareness over precision, focusing on identifying emerging patterns rather than making exact predictions.

## 📊 The Signal Intelligence Framework

One of the key concepts we're exploring through Agentic Explorer is a Signal Intelligence Framework that organizes insights into five universal indices that could apply to organizations of all types and sizes:

| Signal Index | Definition | Early Warning For |
|--------------|------------|-------------------|
| **Cost Pressure Index (CPI)** | Forward-looking measure of factors likely to impact cost structure | Margin compression, pricing decisions, operational adjustments |
| **Revenue Vulnerability Index (RVI)** | Predictive assessment of stability and growth potential of revenue streams | Sales forecast adjustments, marketing strategy shifts, product development priorities |
| **Brand Resilience Index (BRI)** | Measure of reputation capital and ability to withstand perception challenges | Communication strategy, stakeholder engagement, value alignment |
| **Risk Exposure Index (REI)** | Assessment of vulnerability to disruption from operational, financial, strategic risks | Contingency planning, risk mitigation initiatives, investment decisions |
| **Market Environment Index (MEI)** | Indicator of favorability of external conditions for an organization's strategy | Strategic recalibration, geographic focus, expansion/contraction decisions |

Through Agentic Explorer, we can test how multi-agent systems might collaboratively construct and maintain these indices.

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

## 📊 Token Economics & Agent Value

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

## 🔬 Core Application Modules

Agentic Explorer offers several application modules that showcase different aspects of multi-agent systems:

### 1. Company Deep Dive Analysis

Select a company and time period for a comprehensive multi-agent analysis. See how different agents contribute unique insights about financial health, news impact, and market positioning. Watch in real-time as agents debate and refine their analysis.

### 2. News Impact Validator

Identify significant news events and validate their actual impact on company performance. Discover which news actually moved markets versus what was just noise. Get a "Reality Score" for each major news event's significance.

### 3. Prediction Challenge Simulator

Split timeline into "before" and "after" periods, with agents making predictions based on early data that are validated against later results. See which agents' predictions were most accurate and why.

### 4. Agent Resilience Tester

Deliberately introduce errors or biases to specific agents to see how the system's overall performance is affected. Learn how robust multi-agent systems handle misinformation and failure.

### 5. Multi-Company Comparative Analysis

Run the same analysis across multiple companies in a sector to identify shared patterns and company-specific insights. Discover hidden connections and divergences across competitors.

## 💻 Technical Challenges & Innovations

Agentic Explorer tackles several advanced technical challenges that are common in modern AI systems:

### 1. Unstructured + Structured Data Integration

Most analysis systems focus primarily on structured data, treating unstructured data as a separate domain. We're exploring how to deliberately integrate these data types using a layered approach where unstructured data signals provide early warnings that are later confirmed by structured metrics.

### 2. Signal-to-Noise Optimization

In any intelligence system, distinguishing meaningful signals from background noise is critical. We're experimenting with:
- Multi-source confirmation requirements
- Temporal pattern detection
- Bayesian probability adjustments based on historical accuracy
- Custom sensitivity thresholds for different contexts

### 3. Agent Orchestration & Communication

Effective multi-agent systems require sophisticated coordination. We're exploring:
- Dynamic task allocation based on agent capabilities
- Information sharing protocols between agents
- Conflict resolution mechanisms
- Meta-cognitive oversight

### 4. Explainable Intelligence

For users to trust and act on insights, they need to understand their origins. We prioritize:
- Transparent agent reasoning
- Clear contribution tracking
- Insight pathway visualization
- Confidence metrics

## 🧪 Development Roadmap

### Phase 1: Foundation (Current)

- Project structure implementation (completed)
- Data collection from financial sources (completed)
- Core data management layer
- Basic agent framework implementation
- CrewAI integration
- Company Deep Dive Analysis module (MVP)

### Phase 2: Core Functionality

- Complete agent ecosystem implementation
- Prediction Challenge Simulator module
- News Impact Validator module
- Enhanced visualization capabilities
- Token economy tracking system
- Interactive UI foundation

### Phase 3: Advanced Features

- Agent Resilience Tester module
- Multi-Company Comparative Analysis module
- Advanced visualization dashboards
- System optimization features
- Comprehensive documentation
- Case studies and examples

## 🚀 Getting Started

### Installation

```bash
# Clone the repo
git clone https://github.com/Kris-Nale314/agentic-explorer.git
cd agentic-explorer

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env to add your API keys
```

### Collecting Financial Data

```bash
# Run the data collector with interactive prompts
python -m utils.run_data_collector

# Or specify companies directly
python -m utils.run_data_collector --tickers DELL,NVDA,TSLA,ACN --years 3
```

### Running the Explorer

```bash
# Launch the Streamlit interface
streamlit run app.py

# Or run specific modules from command line
python -m modules.deep_dive --company NVDA --start 2023-01-01 --end 2023-12-31
```

## 📂 Enhanced Project Structure

Our current enhancement efforts are focusing on a more efficient data organization:

```
agentic-explorer/
├── core/                          # Core system components
│   ├── agents/                    # Agent implementations
│   ├── models/                    # Analysis models
│   └── tools/                     # Shared utilities for agents
├── dataStore/                     # Financial data repository
│   ├── companies/                 # Company-specific data
│   │   └── [TICKER]/              # Data for each company
│   ├── market/                    # Market-wide data
│   ├── events/                    # Event-based data
│   ├── relationships/             # Relationship data
│   └── signals/                   # Generated signal data
├── modules/                       # Application modules
│   ├── deep_dive.py               # Company Deep Dive Analysis
│   ├── news_validator.py          # News Impact Validator
│   ├── prediction_challenge.py    # Prediction Challenge Simulator
│   ├── resilience_tester.py       # Agent Resilience Tester
│   └── comparative_analysis.py    # Multi-Company Comparative Analysis
├── utils/                         # Utility functions
│   ├── data_collector.py          # Financial data collection
│   └── visualization.py           # Visualization helpers
├── pages/                         # Streamlit pages
├── outputs/                       # Analysis outputs and logs
├── app.py                         # Main Streamlit application
└── project_structure.py           # Project structure utilities
```

## 🔮 Future Explorations

As this sandbox project evolves, we're interested in exploring several cutting-edge concepts:

- **Adaptive Agent Specialization**: Agents that automatically specialize based on discovered patterns
- **Cross-Domain Signal Networks**: Mapping relationships between seemingly unrelated signals
- **Temporal Analysis for Lead Time**: Understanding how different signal types predict outcomes with varying lead times
- **Decision Recommendation Engine**: Testing how multi-agent systems can move from insight to action recommendation
- **Multi-Modal Intelligence Integration**: Combining text, numerical, and potentially visual data for comprehensive signal detection

## 📚 Contributing

Contributions welcome! Check out the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Built while convincing LLMs to play nicely together by Kris Naleszkiewicz | [LinkedIn](https://www.linkedin.com/in/kris-nale314/) | [Medium](https://medium.com/@kris_nale314)*

<div align="center">
  <i>"The most unrealistic part of sci-fi AI isn't the intelligence, it's the cooperation."</i>
</div>