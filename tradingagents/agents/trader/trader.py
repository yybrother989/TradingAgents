import functools
import time
import json
import asyncio
from tradingagents.agents.utils.mcp_agent_base import MCPAgent


def create_trader(llm, memory):
    """Create a trader that uses MCP tools for current market data."""
    
    # Initialize MCP agent for market data
    mcp_agent = MCPAgent(
        agent_name="Trader",
        mcp_servers=["alphavantage"]
    )
    
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        ticker = state.get("company_of_interest", "AAPL")
        
        # Get current market data via MCP tools for context
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
            print(f"Warning: Failed to get MCP data for trader: {e}")
            # Fallback to state data
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
        if past_memories:
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"
        else:
            past_memory_str = "No past memories found."

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nUse MCP tools to get the latest market data for {ticker} to make an informed decision. Leverage these insights to make an informed and strategic decision.",
        }

        messages = [
            {
                "role": "system",
                "content": f"""You are a trading agent analyzing market data to make investment decisions. Based on your analysis, provide a specific recommendation to buy, sell, or hold. 

IMPORTANT: Before making your decision, use MCP tools (get_time_series_daily, get_news_sentiment, get_company_overview) to fetch the latest data for {ticker} to ensure your decision is based on current market conditions.

End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' to confirm your recommendation. Do not forget to utilize lessons from past decisions to learn from your mistakes. Here is some reflections from similar situations you traded in and the lessons learned: {past_memory_str}""",
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": result.content,
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")
