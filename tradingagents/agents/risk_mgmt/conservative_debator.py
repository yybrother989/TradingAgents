from langchain_core.messages import AIMessage
import time
import json
import asyncio
from tradingagents.agents.utils.mcp_agent_base import MCPAgent


def create_safe_debator(llm):
    """Create a conservative/safe debator that uses MCP tools for current market data."""
    
    # Initialize MCP agent
    mcp_agent = MCPAgent(
        agent_name="Safe/Conservative Risk Analyst",
        mcp_servers=["alphavantage"]
    )
    
    def safe_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        safe_history = risk_debate_state.get("safe_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_neutral_response = risk_debate_state.get("current_neutral_response", "")

        trader_decision = state["trader_investment_plan"]
        ticker = state.get("company_of_interest", "AAPL")
        
        # Get current market data via MCP tools
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        mcp_agent.get_research_data(ticker, state.get("trade_date"))
                    )
                    research_data = future.result()
            else:
                research_data = asyncio.run(mcp_agent.get_research_data(ticker, state.get("trade_date")))
        except RuntimeError:
            research_data = asyncio.run(mcp_agent.get_research_data(ticker, state.get("trade_date")))
        except Exception as e:
            print(f"Warning: Failed to get MCP data for safe debator: {e}")
            # Fallback to state data
            research_data = {
                "market_data": state.get("market_report", ""),
                "news_data": state.get("news_report", ""),
                "fundamentals_data": state.get("fundamentals_report", ""),
                "sentiment_data": state.get("sentiment_report", "")
            }

        prompt = f"""As the Safe/Conservative Risk Analyst, protect assets, minimize volatility, ensure steady growth. Prioritize stability, security, risk mitigation.

CRITICAL: Use MCP tools (get_time_series_daily, get_news_sentiment, get_company_overview) to fetch current data for {ticker} before arguing.

Trader's decision: {trader_decision[:500] if len(trader_decision) > 500 else trader_decision}

Task: Counter Risky and Neutral Analysts, highlight overlooked threats. Use real data from MCP tools to build a case for low-risk approach.

Conversation: {history[:400] if len(history) > 400 else history}
Risky: {current_risky_response[:300] if len(current_risky_response) > 300 else current_risky_response}
Neutral: {current_neutral_response[:300] if len(current_neutral_response) > 300 else current_neutral_response}

If no responses from others, just present your point. Question optimism, emphasize downsides, show why conservative stance is safest. Keep response concise."""

        response = llm.invoke(prompt)

        argument = f"Safe Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": safe_history + "\n" + argument,
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Safe",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": argument,
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return safe_node
