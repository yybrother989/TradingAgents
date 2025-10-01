"""Official MCP-enabled Market Analyst using OpenAI Agents SDK."""

import asyncio
from typing import Dict, Any
from tradingagents.agents.utils.official_mcp_agent import OfficialMCPMarketAnalyst


def create_market_analyst_official(llm):
    """Create an official MCP-enabled market analyst."""
    
    # Extract model name from LLM
    model_name = getattr(llm, 'model_name', 'gpt-4o-mini')
    if hasattr(llm, 'model'):
        model_name = llm.model
    
    # Initialize the official MCP market analyst
    mcp_analyst = OfficialMCPMarketAnalyst(model=model_name)
    
    def market_analyst_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Market analyst node using official MCP tools."""
        
        # Execute analysis using official MCP agent
        try:
            # Try to run in existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, create a task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, mcp_analyst.analyze(state))
                    result = future.result()
            else:
                # No running loop, safe to use asyncio.run
                result = asyncio.run(mcp_analyst.analyze(state))
        except RuntimeError:
            # Fallback: create new event loop
            result = asyncio.run(mcp_analyst.analyze(state))
        
        return result
    
    # Store mcp_analyst for potential direct access
    market_analyst_node._mcp_analyst = mcp_analyst
    return market_analyst_node


# For backward compatibility, create a wrapper that can replace the original
def create_market_analyst(llm):
    """Create market analyst - Official MCP version (replaces original)."""
    return create_market_analyst_official(llm)
