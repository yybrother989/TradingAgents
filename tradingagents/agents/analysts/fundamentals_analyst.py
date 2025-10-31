"""MCP-enabled Fundamentals Analyst for TradingAgents."""

import asyncio
from typing import Dict, Any
from tradingagents.agents.utils.mcp_agent_base import MCPAgent


def create_fundamentals_analyst(llm):
    """Create an MCP-enabled fundamentals analyst."""
    
    # Initialize MCP agent
    mcp_agent = MCPAgent(
        agent_name="Fundamentals Analyst",
        mcp_servers=["alphavantage"]
    )
    
    def fundamentals_analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Fundamentals analyst node using MCP tools."""
        
        # Get analysis date from state
        analysis_date = state.get("trade_date", "N/A")
        ticker = state.get("company_of_interest", "N/A")
        company_name = state.get("company_of_interest", ticker)
        
        # Create system message with date context
        system_message = (
            f"You are a fundamental analysis researcher specializing in company financials and business metrics. "
            f"Your role is to analyze fundamental information about {company_name} ({ticker}) as of {analysis_date}. "
            f"IMPORTANT: This analysis is for the date {analysis_date}. When examining financial data, interpret it in the context of what was known or available up to {analysis_date}. "
            f"Use the available MCP tools to gather comprehensive fundamental data: "
            f"- COMPANY_OVERVIEW: Company profile, business description, key metrics "
            f"- EARNINGS: Earnings data and trends "
            f"- BALANCE_SHEET: Balance sheet information "
            f"- INCOME_STATEMENT: Income statement data "
            f"- CASH_FLOW: Cash flow statement data "
            f"Focus on: "
            f"- Company financial health and stability "
            f"- Revenue and profit trends "
            f"- Balance sheet strength (assets, liabilities, equity) "
            f"- Cash flow patterns and liquidity "
            f"- Valuation metrics and ratios "
            f"- Business model and competitive position "
            f"Do not simply state that trends are mixed - provide detailed and fine-grained analysis and insights that may help traders make decisions. "
            f"Provide comprehensive analysis with specific numbers, ratios, trends, and implications for investors. "
            f"End your report with a Markdown table organizing key financial metrics and findings. "
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
            print(f"Error in fundamentals analyst MCP: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simple analysis
            from langchain_core.messages import HumanMessage
            result = {
                "messages": [HumanMessage(content="Error in MCP analysis, using fallback")],
                "fundamentals_report": "Error occurred during MCP fundamentals analysis."
            }
        
        # Ensure tool call messages are included for CLI tracking
        messages = result["messages"]
        
        return {
            "messages": messages,
            "fundamentals_report": result["analysis_report"]
        }
    
    # Store mcp_agent for potential direct access
    fundamentals_analyst_node._mcp_agent = mcp_agent
    return fundamentals_analyst_node
