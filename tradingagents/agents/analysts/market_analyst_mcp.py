"""MCP-enabled Market Analyst for TradingAgents."""

import asyncio
from typing import Dict, Any
from tradingagents.agents.utils.mcp_agent_base import MCPAgent


def create_market_analyst_mcp(llm):
    """Create an MCP-enabled market analyst."""
    
    # Initialize MCP agent
    mcp_agent = MCPAgent(
        agent_name="Market Analyst",
        mcp_servers=["alphavantage"]
    )
    
    def market_analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Market analyst node using MCP tools."""
        
        # Simplified system message focused on analysis rather than tool usage
        system_message = (
            "You are a financial market analyst specializing in technical analysis. "
            "Your role is to analyze market trends and provide actionable insights for trading decisions. "
            "Use the available MCP tools to gather real-time market data and technical indicators. "
            "Focus on identifying key trends, support/resistance levels, momentum shifts, and volatility patterns. "
            "Provide detailed analysis with specific price levels, trend directions, and trading implications. "
            "End your analysis with a clear summary table of key findings."
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
            print(f"Error in market analyst MCP: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to simple analysis
            from langchain_core.messages import HumanMessage
            result = {
                "messages": [HumanMessage(content="Error in MCP analysis, using fallback")],
                "analysis_report": "Error occurred during MCP analysis."
            }
        
        # Ensure tool call messages are included for CLI tracking
        messages = result["messages"]
        
        # The first message should contain the tool calls for CLI tracking
        # This is already handled by the MCP agent base class
        
        # Add a debug message to show tool calls are being made
        from langchain_core.messages import HumanMessage
        tool_call_count = len([m for m in messages if hasattr(m, 'tool_calls') and m.tool_calls])
        debug_message = HumanMessage(
            content=f"🔧 MCP Agent completed analysis with {tool_call_count} tool call messages"
        )
        messages.append(debug_message)
        
        # Also add individual tool call messages for CLI tracking
        for i, msg in enumerate(messages):
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool in msg.tool_calls:
                    tool_msg = HumanMessage(
                        content=f"🔧 MCP Tool: {tool['name']} - {tool['args']}"
                    )
                    messages.append(tool_msg)
        
        return {
            "messages": messages,
            "market_report": result["analysis_report"]
        }
    
    # Store mcp_agent for potential direct access
    market_analyst_node._mcp_agent = mcp_agent
    return market_analyst_node


# For backward compatibility, create a wrapper that can replace the original
def create_market_analyst(llm):
    """Create market analyst - MCP version (replaces original)."""
    return create_market_analyst_mcp(llm)
