<p align="center">
  <img src="assets/TauricResearch.png" style="width: 60%; height: auto;">
</p>

<div align="center" style="line-height: 1;">
  <a href="https://arxiv.org/abs/2412.20138" target="_blank"><img alt="arXiv" src="https://img.shields.io/badge/arXiv-2412.20138-B31B1B?logo=arxiv"/></a>
  <a href="https://discord.com/invite/hk9PGKShPK" target="_blank"><img alt="Discord" src="https://img.shields.io/badge/Discord-TradingResearch-7289da?logo=discord&logoColor=white&color=7289da"/></a>
  <a href="./assets/wechat.png" target="_blank"><img alt="WeChat" src="https://img.shields.io/badge/WeChat-TauricResearch-brightgreen?logo=wechat&logoColor=white"/></a>
  <a href="https://x.com/TauricResearch" target="_blank"><img alt="X Follow" src="https://img.shields.io/badge/X-TauricResearch-white?logo=x&logoColor=white"/></a>
  <br>
  <a href="https://github.com/TauricResearch/" target="_blank"><img alt="Community" src="https://img.shields.io/badge/Join_GitHub_Community-TauricResearch-14C290?logo=discourse"/></a>
</div>

<div align="center">
  <!-- Keep these links. Translations will automatically update with the README. -->
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=de">Deutsch</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=es">Español</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=fr">français</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=ja">日本語</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=ko">한국어</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=pt">Português</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=ru">Русский</a> | 
  <a href="https://www.readme-i18n.com/TauricResearch/TradingAgents?lang=zh">中文</a>
</div>

---

# TradingAgents: Multi-Agents LLM Financial Trading Framework 

> 🎉 **TradingAgents** officially released! We have received numerous inquiries about the work, and we would like to express our thanks for the enthusiasm in our community.
>
> So we decided to fully open-source the framework. Looking forward to building impactful projects with you!

<div align="center">
<a href="https://www.star-history.com/#TauricResearch/TradingAgents&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=TauricResearch/TradingAgents&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=TauricResearch/TradingAgents&type=Date" />
   <img alt="TradingAgents Star History" src="https://api.star-history.com/svg?repos=TauricResearch/TradingAgents&type=Date" style="width: 80%; height: auto;" />
 </picture>
</a>
</div>

<div align="center">

🚀 [TradingAgents](#tradingagents-framework) | ⚡ [Installation & CLI](#installation-and-cli) | 🎬 [Demo](https://www.youtube.com/watch?v=90gr5lwjIho) | 📦 [Package Usage](#tradingagents-package) | 🤝 [Contributing](#contributing) | 📄 [Citation](#citation)

</div>

## TradingAgents Framework

TradingAgents is a multi-agent trading framework that mirrors the dynamics of real-world trading firms. By deploying specialized LLM-powered agents: from fundamental analysts, sentiment experts, and technical analysts, to trader, risk management team, the platform collaboratively evaluates market conditions and informs trading decisions. Moreover, these agents engage in dynamic discussions to pinpoint the optimal strategy.

<p align="center">
  <img src="assets/schema.png" style="width: 100%; height: auto;">
</p>

> TradingAgents framework is designed for research purposes. Trading performance may vary based on many factors, including the chosen backbone language models, model temperature, trading periods, the quality of data, and other non-deterministic factors. [It is not intended as financial, investment, or trading advice.](https://tauric.ai/disclaimer/)

Our framework decomposes complex trading tasks into specialized roles. This ensures the system achieves a robust, scalable approach to market analysis and decision-making.

### Analyst Team
- Fundamentals Analyst: Evaluates company financials and performance metrics, identifying intrinsic values and potential red flags.
- Sentiment Analyst: Analyzes social media and public sentiment using sentiment scoring algorithms to gauge short-term market mood.
- News Analyst: Monitors global news and macroeconomic indicators, interpreting the impact of events on market conditions.
- Technical Analyst: Utilizes technical indicators (like MACD and RSI) to detect trading patterns and forecast price movements.

<p align="center">
  <img src="assets/analyst.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

### Researcher Team
- Comprises both bullish and bearish researchers who critically assess the insights provided by the Analyst Team. Through structured debates, they balance potential gains against inherent risks.

<p align="center">
  <img src="assets/researcher.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Trader Agent
- Composes reports from the analysts and researchers to make informed trading decisions. It determines the timing and magnitude of trades based on comprehensive market insights.

<p align="center">
  <img src="assets/trader.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

### Risk Management and Portfolio Manager
- Continuously evaluates portfolio risk by assessing market volatility, liquidity, and other risk factors. The risk management team evaluates and adjusts trading strategies, providing assessment reports to the Portfolio Manager for final decision.
- The Portfolio Manager approves/rejects the transaction proposal. If approved, the order will be sent to the simulated exchange and executed.

<p align="center">
  <img src="assets/risk.png" width="70%" style="display: inline-block; margin: 0 2%;">
</p>

## Installation and CLI

### Installation

Clone TradingAgents:
```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents
```

Create a virtual environment in any of your favorite environment managers:
```bash
conda create -n tradingagents python=3.13
conda activate tradingagents
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Required APIs

You will also need the [Alpha Vantage API](https://www.alphavantage.co/support/#api-key) for financial data. The free tier supports 25 API calls per day.
```bash
export ALPHA_VANTAGE_API_KEY=$YOUR_ALPHA_VANTAGE_API_KEY
```

You will need the OpenAI API for all the agents.
```bash
export OPENAI_API_KEY=$YOUR_OPENAI_API_KEY
```

Alternatively, you can create a `.env` file in the project root with your API keys (see `.env.example` for reference):
```bash
cp .env.example .env
# Edit .env with your actual API keys
```

### CLI Usage

You can also try out the CLI directly by running:
```bash
python -m cli.main
```
You will see a screen where you can select your desired tickers, date, LLMs, research depth, etc.

<p align="center">
  <img src="assets/cli/cli_init.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

An interface will appear showing results as they load, letting you track the agent's progress as it runs.

<p align="center">
  <img src="assets/cli/cli_news.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

<p align="center">
  <img src="assets/cli/cli_transaction.png" width="100%" style="display: inline-block; margin: 0 2%;">
</p>

## TradingAgents Package

### Implementation Details

We built TradingAgents with LangGraph to ensure flexibility and modularity. We utilize `o1-preview` and `gpt-4o` as our deep thinking and fast thinking LLMs for our experiments. However, for testing purposes, we recommend you use `o4-mini` and `gpt-4.1-mini` to save on costs as our framework makes **lots of** API calls.

### Python Usage

To use TradingAgents inside your code, you can import the `tradingagents` module and initialize a `TradingAgentsGraph()` object. The `.propagate()` function will return a decision. You can run `main.py`, here's also a quick example:

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

ta = TradingAgentsGraph(debug=True, config=DEFAULT_CONFIG.copy())

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
print(decision)
```

You can also adjust the default configuration to set your own choice of LLMs, debate rounds, etc.

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Create a custom config
config = DEFAULT_CONFIG.copy()
config["deep_think_llm"] = "gpt-4.1-nano"  # Use a different model
config["quick_think_llm"] = "gpt-4.1-nano"  # Use a different model
config["max_debate_rounds"] = 1  # Increase debate rounds

# Configure data vendors (default uses Alpha Vantage for real-time data)
config["data_vendors"] = {
    "core_stock_apis": "alpha_vantage",      # Options: alpha_vantage, yahoo_finance, local
    "technical_indicators": "alpha_vantage", # Options: alpha_vantage, yahoo_finance, local
    "fundamental_data": "alpha_vantage",     # Options: alpha_vantage, openai, local
    "news_data": "alpha_vantage",            # Options: alpha_vantage, openai, google, local
}

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
print(decision)
```

> The default configuration now uses Alpha Vantage as the primary data provider, which provides access to real-time market data. For offline experimentation, there's a local data vendor option that uses our **Tauric TradingDB**, a curated dataset for backtesting, though this is still in development. We're currently refining this dataset and plan to release it soon alongside our upcoming projects. Stay tuned!

### Alpha Vantage MCP Integration

TradingAgents now features **Model Context Protocol (MCP)** integration with Alpha Vantage, providing enhanced real-time data access and improved reliability. The MCP integration offers:

- **Real-time data streaming** via HTTP/SSE connections
- **Enhanced error handling** and connection management
- **Better performance** with optimized data retrieval
- **Seamless integration** with existing agent workflows
- **Dynamic tool discovery** for flexible data access

#### Setup MCP Integration

1. **Install dependencies** (already included in requirements):
   ```bash
   pip install mcp>=1.9.4
   ```

2. **Configure Alpha Vantage API key**:
   ```bash
   python setup_mcp.py
   ```

The MCP integration is automatically enabled as the default data provider. The Market Analyst now uses MCP tools for real-time data retrieval, providing more accurate and up-to-date market analysis.

You can view the full list of configurations in `tradingagents/default_config.py`.

## REST API Server

TradingAgents now includes a REST API server for programmatic access to the trading analysis framework.

### Starting the Server

```bash
# Using the provided script
python server.py

# Or using uvicorn directly
uvicorn tradingagents.api.server:app --host 0.0.0.0 --port 8000
```

### API Endpoints

- **POST `/api/v1/analyze`** - Run analyst agents and return their reports
  - Request: `{"ticker": "AAPL", "date": "2024-05-10", "config": {...}}`
  - Response: **Analyst reports only** (Market, News, Social, Fundamentals)
  - Note: Trading decisions, researcher outputs, and risk manager outputs are excluded

- **POST `/api/v1/agents/run`** - Run selected analyst agents independently
  - Request: `{"ticker": "AAPL", "date": "2024-05-10", "agents": ["market_analyst", "news_analyst"], "config": {...}}`
  - Response: Reports from selected analyst agents
  - Valid agents: `market_analyst`, `news_analyst`, `social_analyst`, `fundamentals_analyst`
  - If no agents specified, all analysts run by default

- **GET `/api/v1/health`** - Health check
  - Response: `{"status": "ok", "version": "1.0.0"}`

- **GET `/api/v1/config`** - Get current configuration
  - Response: Current configuration dictionary

- **POST `/api/v1/config`** - Update configuration
  - Request: `{"config": {...}}`
  - Response: Updated configuration

- **GET `/api/v1/analyses/{ticker}/{date}`** - Get cached analyst reports
  - Response: Cached analyst reports if available (only analyst outputs, no trading decisions)

### API Documentation

Once the server is running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI) or `http://localhost:8000/redoc` for ReDoc documentation.

### Frontend Integration

For detailed instructions on connecting your frontend application to the TradingAgents Analyst API, see **[FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)**.

The guide includes:
- Complete API endpoint documentation
- TypeScript type definitions
- Examples for React, Vue, Next.js, and vanilla JavaScript
- Error handling patterns
- Best practices and production setup

### Example Usage

```bash
# Run analysis via API
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "NVDA", "date": "2024-05-10"}'

# Check health
curl http://localhost:8000/api/v1/health

# Get configuration
curl http://localhost:8000/api/v1/config
```

### Configuration

Server configuration via environment variables:
- `TRADINGAGENTS_HOST` - Server host (default: 0.0.0.0)
- `TRADINGAGENTS_PORT` - Server port (default: 8000)
- `TRADINGAGENTS_DEBUG` - Enable debug mode (default: false)

## Deployment

Deploy the TradingAgents API to production using free cloud hosting options:

### Quick Deploy to Render (Recommended)

Get your API live in **5 minutes** with Render's free tier:

1. **Create account**: https://render.com → Sign up with GitHub
2. **New Web Service** → Connect `TradingAgents` repo
3. **Configure**:
   - Branch: `feature/data-vendor-integration` (or `main`)
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn tradingagents.api.server:app --host 0.0.0.0 --port $PORT`
4. **Add environment variables**: Your API keys
5. **Deploy!**

**Your API will be live at:** `https://your-app.onrender.com`

📖 **Full guide**: [QUICK_DEPLOY_RENDER.md](QUICK_DEPLOY_RENDER.md) (5 min setup)

### Other Platforms

**Railway** ($5 monthly credit):
- Docker support, no cold starts
- Full guide: [DEPLOYMENT.md](DEPLOYMENT.md)

**Fly.io** (generous free tier):
- Global edge deployment, always-on
- Full guide: [DEPLOYMENT.md](DEPLOYMENT.md)

**Compare all options**: See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Platform comparison table
- Docker configuration
- Environment setup
- Troubleshooting
- Performance tips

## Contributing

We welcome contributions from the community! Whether it's fixing a bug, improving documentation, or suggesting a new feature, your input helps make this project better. If you are interested in this line of research, please consider joining our open-source financial AI research community [Tauric Research](https://tauric.ai/).

## Citation

Please reference our work if you find *TradingAgents* provides you with some help :)

```
@misc{xiao2025tradingagentsmultiagentsllmfinancial,
      title={TradingAgents: Multi-Agents LLM Financial Trading Framework}, 
      author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
      year={2025},
      eprint={2412.20138},
      archivePrefix={arXiv},
      primaryClass={q-fin.TR},
      url={https://arxiv.org/abs/2412.20138}, 
}
```
