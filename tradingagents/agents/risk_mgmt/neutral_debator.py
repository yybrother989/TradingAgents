import time
import json
import asyncio
from tradingagents.agents.utils.mcp_agent_base import MCPAgent


def create_neutral_debator(llm):
    """Create a neutral debator that uses MCP tools for current market data."""
    
    # Initialize MCP agent
    mcp_agent = MCPAgent(
        agent_name="Neutral Risk Analyst",
        mcp_servers=["alphavantage"]
    )
    
    def neutral_node(state) -> dict:
        risk_debate_state = state["risk_debate_state"]
        history = risk_debate_state.get("history", "")
        neutral_history = risk_debate_state.get("neutral_history", "")

        current_risky_response = risk_debate_state.get("current_risky_response", "")
        current_safe_response = risk_debate_state.get("current_safe_response", "")

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
            print(f"Warning: Failed to get MCP data for neutral debator: {e}")
            # Fallback to state data
            research_data = {
                "market_data": state.get("market_report", ""),
                "news_data": state.get("news_report", ""),
                "fundamentals_data": state.get("fundamentals_report", ""),
                "sentiment_data": state.get("sentiment_report", "")
            }

        prompt = f"""As the Neutral Risk Analyst, provide balanced perspective weighing benefits and risks. Prioritize well-rounded approach evaluating upsides and downsides.

CRITICAL: Use MCP tools (get_time_series_daily, get_news_sentiment, get_company_overview) to fetch current data for {ticker} before arguing.

Trader's decision: {trader_decision[:500] if len(trader_decision) > 500 else trader_decision}

Task: Challenge both Risky and Safe Analysts, point out where each is overly optimistic or cautious. Use real data from MCP tools to support moderate strategy.

Conversation: {history[:400] if len(history) > 400 else history}
Risky: {current_risky_response[:300] if len(current_risky_response) > 300 else current_risky_response}
Safe: {current_safe_response[:300] if len(current_safe_response) > 300 else current_safe_response}

If no responses from others, just present your point. Analyze both sides critically, show why moderate risk offers best of both worlds. Keep response concise."""

        response = llm.invoke(prompt)

        argument = f"Neutral Analyst: {response.content}"

        new_risk_debate_state = {
            "history": history + "\n" + argument,
            "risky_history": risk_debate_state.get("risky_history", ""),
            "safe_history": risk_debate_state.get("safe_history", ""),
            "neutral_history": neutral_history + "\n" + argument,
            "latest_speaker": "Neutral",
            "current_risky_response": risk_debate_state.get(
                "current_risky_response", ""
            ),
            "current_safe_response": risk_debate_state.get("current_safe_response", ""),
            "current_neutral_response": argument,
            "count": risk_debate_state["count"] + 1,
        }

        return {"risk_debate_state": new_risk_debate_state}

    return neutral_node
