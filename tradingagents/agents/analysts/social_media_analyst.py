"""MCP-enabled Social Media Analyst for TradingAgents."""

import asyncio
from typing import Dict, Any
from tradingagents.agents.utils.mcp_agent_base import MCPAgent


def create_social_media_analyst(llm):
    """Create an MCP-enabled social media analyst."""
    
    # Initialize MCP agent
    mcp_agent = MCPAgent(
        agent_name="Social Media Analyst",
        mcp_servers=["alphavantage"]
    )
    
    def social_media_analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Social media analyst node using MCP tools."""
        
        # Get analysis date from state
        analysis_date = state.get("trade_date", "N/A")
        ticker = state.get("company_of_interest", "N/A")
        company_name = state.get("company_of_interest", ticker)
        
        # Create system message with date context
        system_message = (
            f"You are a social media and company-specific news researcher/analyst. "
            f"Your role is to analyze social media posts, recent company news, and public sentiment for {company_name} ({ticker}) over the past week leading up to {analysis_date}. "
            f"IMPORTANT: This analysis is for the date {analysis_date}. When examining sentiment data and news, interpret it in the context of what was known or available up to {analysis_date}. "
            f"Use the available MCP tools (NEWS_SENTIMENT) to gather company-specific news, social media discussions, and sentiment data. "
            f"Focus on: "
            f"- Social media sentiment trends and what people are saying about the company "
            f"- Company-specific news and announcements "
            f"- Public perception and sentiment shifts "
            f"- Implications for traders and investors "
            f"Do not simply state that trends are mixed - provide detailed and fine-grained analysis and insights that may help traders make decisions. "
            f"Provide comprehensive analysis with specific examples, sentiment scores, and actionable insights. "
            f"End your report with a Markdown table organizing key points. "
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
            print(f"Error in social media analyst MCP: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simple analysis
            from langchain_core.messages import HumanMessage
            result = {
                "messages": [HumanMessage(content="Error in MCP analysis, using fallback")],
                "sentiment_report": "Error occurred during MCP social media analysis."
            }
        
        # Ensure tool call messages are included for CLI tracking
        messages = result["messages"]
        
        return {
            "messages": messages,
            "sentiment_report": result["analysis_report"]
        }
    
    # Store mcp_agent for potential direct access
    social_media_analyst_node._mcp_agent = mcp_agent
    return social_media_analyst_node
