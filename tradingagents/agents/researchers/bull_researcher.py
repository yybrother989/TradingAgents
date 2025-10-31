from langchain_core.messages import AIMessage
import time
import json
import asyncio
from typing import Dict, Any
from tradingagents.agents.utils.mcp_agent_base import MCPAgent


def create_bull_researcher(llm, memory):
    """Create a bull researcher that uses MCP tools for data retrieval."""
    
    # Initialize MCP agent for research data
    mcp_agent = MCPAgent(
        agent_name="Bull Researcher",
        mcp_servers=["alphavantage"]
    )
    
    def bull_node(state) -> dict:
        investment_debate_state = state["investment_debate_state"]
        history = investment_debate_state.get("history", "")
        bull_history = investment_debate_state.get("bull_history", "")

        current_response = investment_debate_state.get("current_response", "")
        ticker = state.get("company_of_interest", "AAPL")
        
        # Get research data via MCP tools instead of from state
        try:
            # Try to run in existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        mcp_agent.get_research_data(ticker, state.get("trade_date"))
                    )
                    research_data = future.result()
            else:
                # No running loop, safe to use asyncio.run
                research_data = asyncio.run(mcp_agent.get_research_data(ticker, state.get("trade_date")))
        except RuntimeError:
            # Fallback: create new event loop
            research_data = asyncio.run(mcp_agent.get_research_data(ticker, state.get("trade_date")))
        except Exception as e:
            print(f"Warning: Failed to get MCP research data for bull researcher: {e}")
            # Fallback to state data if MCP fails
            research_data = {
                "market_data": state.get("market_report", ""),
                "news_data": state.get("news_report", ""),
                "fundamentals_data": state.get("fundamentals_report", ""),
                "sentiment_data": state.get("sentiment_report", "")
            }
        
        # Create situation string for memory lookup
        curr_situation = f"{research_data['market_data']}\n\n{research_data['sentiment_data']}\n\n{research_data['news_data']}\n\n{research_data['fundamentals_data']}"
        past_memories = memory.get_memories(curr_situation, n_matches=2)

        past_memory_str = ""
        for i, rec in enumerate(past_memories, 1):
            past_memory_str += rec["recommendation"] + "\n\n"

        # Simplified prompt - no data previews to keep prompt short
        prompt = f"""You are a Bull Analyst advocating for investing in {ticker}. Build a strong case emphasizing growth potential, competitive advantages, and positive indicators.

CRITICAL: First, use MCP tools (get_time_series_daily, get_news_sentiment, get_company_overview) to fetch current data for {ticker}. Then make your argument based on the data you retrieve.

Focus: Growth opportunities, competitive advantages, positive indicators, bear counterpoints.

History: {history[:500] if len(history) > 500 else history}
Bear argument: {current_response[:500] if len(current_response) > 500 else current_response}
Past lessons: {past_memory_str[:300] if len(past_memory_str) > 300 else past_memory_str}

Provide a compelling bull argument based on real data from MCP tools. Keep response concise."""

        response = llm.invoke(prompt)

        argument = f"Bull Analyst: {response.content}"

        new_investment_debate_state = {
            "history": history + "\n" + argument,
            "bull_history": bull_history + "\n" + argument,
            "bear_history": investment_debate_state.get("bear_history", ""),
            "current_response": argument,
            "count": investment_debate_state["count"] + 1,
        }

        return {"investment_debate_state": new_investment_debate_state}

    return bull_node
