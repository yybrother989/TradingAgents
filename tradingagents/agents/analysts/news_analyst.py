"""MCP-enabled News Analyst for TradingAgents."""

import asyncio
from typing import Dict, Any
from tradingagents.agents.utils.mcp_agent_base import MCPAgent


def create_news_analyst(llm):
    """Create an MCP-enabled news analyst."""
    
    # Initialize MCP agent
    mcp_agent = MCPAgent(
        agent_name="News Analyst",
        mcp_servers=["alphavantage"]
    )
    
    def news_analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """News analyst node using MCP tools."""
        
        # Get analysis date from state
        analysis_date = state.get("trade_date", "N/A")
        ticker = state.get("company_of_interest", "N/A")
        
        # Create system message with date context
        system_message = (
            f"You are a news researcher and macroeconomics analyst specializing in financial markets. "
            f"Your role is to analyze recent news and global economic trends relevant to trading and investment decisions as of {analysis_date}. "
            f"IMPORTANT: This analysis is for the date {analysis_date}. When examining news, interpret it in the context of what was known or available up to {analysis_date}. "
            f"Use the available MCP tools (NEWS_SENTIMENT) to gather news data for the company {ticker}. "
            f"Focus on: "
            f"- Company-specific news and sentiment trends "
            f"- Macroeconomic news that impacts the broader market "
            f"- Market-moving events and their implications "
            f"- Sentiment analysis from news sources "
            f"Provide detailed analysis with specific insights, implications for traders, and a clear summary table. "
            f"Include the analysis date ({analysis_date}) prominently in your report."
        )
        
        # Execute analysis using MCP tools
        try:
            # Try to run in existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, mcp_agent.execute_analysis(state, llm, system_message))
                    result = future.result()
            else:
                # No running loop, safe to use asyncio.run
                result = asyncio.run(mcp_agent.execute_analysis(state, llm, system_message))
        except RuntimeError:
            # Fallback: create new event loop
            result = asyncio.run(mcp_agent.execute_analysis(state, llm, system_message))
        except Exception as e:
            print(f"Error in news analyst MCP: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simple analysis
            from langchain_core.messages import HumanMessage
            result = {
                "messages": [HumanMessage(content="Error in MCP analysis, using fallback")],
                "news_report": "Error occurred during MCP news analysis."
            }
        
        # Ensure tool call messages are included for CLI tracking
        messages = result["messages"]
        
        return {
            "messages": messages,
            "news_report": result["analysis_report"]
        }
    
    # Store mcp_agent for potential direct access
    news_analyst_node._mcp_agent = mcp_agent
    return news_analyst_node
