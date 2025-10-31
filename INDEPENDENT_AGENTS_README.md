# Independent Agent Execution

This document describes the redesigned CLI and agent structure that allows each agent to run independently.

## Architecture Overview

### Components

1. **BaseAgent** (`tradingagents/agents/base_agent.py`)
   - Abstract base class for all agents
   - Defines interface for standalone execution
   - Tracks agent metadata and dependencies

2. **GraphAgentAdapter** (`tradingagents/agents/graph_agent_adapter.py`)
   - Adapter that wraps existing graph-based agents
   - Allows graph nodes to run independently
   - Handles state conversion and report extraction

3. **AgentRegistry** (`tradingagents/agents/registry.py`)
   - Central registry for all available agents
   - Supports both standalone agents and graph adapters
   - Provides agent discovery and lookup

4. **AgentRunner** (`tradingagents/agents/runner.py`)
   - Executes agents independently or in dependency order
   - Handles context passing between agents
   - Creates execution plans based on dependencies

5. **AgentFactory** (`tradingagents/agents/agent_factory.py`)
   - Initializes all agents and registers them
   - Configures LLMs and memories
   - Wraps graph nodes as adapters

## Usage

### CLI Commands

#### List Available Agents
```bash
python -m cli.agent_cli list
```

#### Run Selected Agents
```bash
# Run specific agents
python -m cli.agent_cli run --ticker AAPL --date 2024-05-10 --agents "market_analyst,news_analyst"

# Run all agents
python -m cli.agent_cli run --ticker AAPL --date 2024-05-10 --agents all

# Interactive selection (if questionary installed)
python -m cli.agent_cli run --ticker AAPL --date 2024-05-10
```

#### Get Agent Information
```bash
python -m cli.agent_cli info market_analyst
```

### Available Agents

- **Analysts** (can run standalone):
  - `market_analyst` - Market/technical analysis
  - `social_analyst` - Social media sentiment
  - `news_analyst` - News analysis
  - `fundamentals_analyst` - Fundamental analysis

- **Researchers** (require analyst reports):
  - `bull_researcher` - Bull case research
  - `bear_researcher` - Bear case research
  - `research_manager` - Research decision maker

- **Trader** (requires research plan):
  - `trader` - Trading decision maker

- **Risk Managers** (require trader plan):
  - `risky_analyst` - Aggressive risk analysis
  - `neutral_analyst` - Balanced risk analysis
  - `conservative_analyst` - Conservative risk analysis
  - `risk_manager` - Final risk decision

### API Endpoint

#### Run Agents Independently
```bash
POST /api/v1/agents/run
Content-Type: application/json

{
  "ticker": "AAPL",
  "date": "2024-05-10",
  "agents": ["market_analyst", "news_analyst"],
  "config": {
    "llm_provider": "openai",
    "quick_think_llm": "gpt-4o-mini"
  }
}
```

Response:
```json
{
  "ticker": "AAPL",
  "date": "2024-05-10",
  "agents": ["market_analyst", "news_analyst"],
  "results": {
    "market_analyst": {
      "report": "...",
      "success": true,
      "execution_time": 12.34,
      "error": null
    },
    "news_analyst": {
      "report": "...",
      "success": true,
      "execution_time": 8.76,
      "error": null
    }
  }
}
```

## Agent Dependencies

Agents automatically resolve dependencies when executed together:

1. **Level 0** (Independent): Analysts
   - market_analyst
   - social_analyst
   - news_analyst
   - fundamentals_analyst

2. **Level 1** (Requires analysts): Researchers
   - bull_researcher (needs: market_report, sentiment_report, news_report, fundamentals_report)
   - bear_researcher (needs: market_report, sentiment_report, news_report, fundamentals_report)

3. **Level 2** (Requires researchers): Research Manager
   - research_manager (needs: investment_debate_state)

4. **Level 3** (Requires research): Trader
   - trader (needs: investment_plan)

5. **Level 4** (Requires trader): Risk Analysts
   - risky_analyst (needs: trader_investment_plan, market_report, news_report)
   - neutral_analyst (needs: trader_investment_plan, market_report, news_report)
   - conservative_analyst (needs: trader_investment_plan, market_report, news_report)

6. **Level 5** (Requires risk analysts): Risk Manager
   - risk_manager (needs: risk_debate_state)

## Backward Compatibility

The original graph-based workflow is still available:

```bash
# Legacy command (runs full graph)
python -m cli.main analyze

# New command (independent agents)
python -m cli.main analyze-new --ticker AAPL --date 2024-05-10 --agents "market_analyst,news_analyst"
```

## Implementation Details

### Graph Agent Adapter

The `GraphAgentAdapter` wraps existing graph node functions:

1. Creates minimal state from ticker/date/context
2. Executes the graph node function
3. Extracts report based on agent category
4. Returns structured `AgentResult`

### Execution Plan

The `AgentRunner` creates an execution plan:

1. Analyzes dependencies for all selected agents
2. Groups agents by execution level (topological sort)
3. Executes agents level by level
4. Passes context from completed agents to dependent agents

### Context Passing

Context is automatically passed between agents:

- Analyst reports → Researchers
- Research debate state → Research Manager
- Investment plan → Trader
- Trader plan → Risk Analysts
- Risk debate state → Risk Manager

## Benefits

1. **Flexibility**: Run any combination of agents
2. **Efficiency**: Only run needed agents
3. **Debugging**: Test individual agents in isolation
4. **Modularity**: Easy to add new agents
5. **Backward Compatible**: Original graph workflow still works

## Examples

### Run Only Market Analysis
```bash
python -m cli.agent_cli run -t AAPL -d 2024-05-10 -a market_analyst
```

### Run Full Pipeline
```bash
python -m cli.agent_cli run -t AAPL -d 2024-05-10 -a all
```

### Run Analysis Chain
```bash
python -m cli.agent_cli run -t AAPL -d 2024-05-10 -a "market_analyst,news_analyst,bull_researcher,bear_researcher"
```

