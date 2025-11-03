import time
import json
import asyncio
from tradingagents.agents.utils.mcp_agent_base import MCPAgent


def create_risky_debator(llm):
    """Create a risky debator that uses MCP tools for current market data."""
    
    # Initialize MCP agent
    mcp_agent = MCPAgent(
        agent_name="Risky Risk Analyst",
        mcp_servers=["alphavantage"]
    )
    
    def risky_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        risky_history = risk_debate_state.get("risky_history", "")

        current_safe_response = risk_debate_state.get("current_safe_response", "")
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
            print(f"Warning: Failed to get MCP data for risky debator: {e}")
            # Fallback to state data
            research_data = {
                "market_data": state.get("market_report", ""),
                "news_data": state.get("news_report", ""),
                "fundamentals_data": state.get("fundamentals_report", ""),
                "sentiment_data": state.get("sentiment_report", "")
            }

        prompt = f"""As the Risky Risk Analyst, champion high-reward, high-risk opportunities with bold strategies. Focus on upside potential, growth, and innovation benefits.

CRITICAL: Use MCP tools (get_time_series_daily, get_news_sentiment, get_company_overview) to fetch current data for {ticker} before arguing.

Trader's decision: {trader_decision[:500] if len(trader_decision) > 500 else trader_decision}

Task: Create a compelling case for the trader's decision by questioning conservative and neutral stances. Use real data from MCP tools to show why high-reward perspective offers the best path.

Conversation: {history[:400] if len(history) > 400 else history}
Conservative: {current_safe_response[:300] if len(current_safe_response) > 300 else current_safe_response}
Neutral: {current_neutral_response[:300] if len(current_neutral_response) > 300 else current_neutral_response}

If no responses from others, just present your point. Engage actively, refute concerns with data, and assert benefits of risk-taking. Keep response concise."""

        response = llm.invoke(prompt)

        argument = f"Risky Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risky_history + "\n" + argument,
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": risk_debate_state.get("neutral_history", ""),
            "latest_speaker": "Risky",
            "current_risky_response": argument,
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": risk_debate_state.get(
                "current_neutral_response", ""
            ),
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return risky_node
