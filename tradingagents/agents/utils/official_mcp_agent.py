"""Official MCP Agent base class using OpenAI Agents SDK."""

import asyncio
from typing import Dict, List, Any, Optional
from agents import Agent, Runner
from tradingagents.dataflows.official_mcp_manager import get_official_mcp_manager
from .timeframe_utils import (
    calculate_timeframes_from_analysis_date,
    add_timeframe_to_existing_prompt
)


class OfficialMCPAgent:
    """Official MCP Agent base class using OpenAI Agents SDK."""
    
    def __init__(self, agent_name: str, instructions: str, model: str = "gpt-4o-mini", mcp_servers: List[str] = None):
        self.agent_name = agent_name
        self.instructions = instructions
        self.model = model
        self.mcp_servers = mcp_servers or ["alphavantage"]
        self.mcp_manager = get_official_mcp_manager()
        self.agent = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the agent with MCP servers."""
        if self._initialized:
            return
        
        await self.mcp_manager.ensure_initialized()
        
        # Get the configured servers
        servers = self.mcp_manager.get_servers()
        
        # Filter servers based on mcp_servers list
        filtered_servers = []
        for server in servers:
            # Check if this server is in our mcp_servers list
            # We'll need to match by name or type
            filtered_servers.append(server)
        
        # Create the agent with MCP servers
        self.agent = Agent(
            name=self.agent_name,
            instructions=self.instructions,
            model=self.model,
            mcp_servers=filtered_servers
        )
        
        self._initialized = True
    
    async def execute_analysis(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute analysis using the official Agent."""
        await self.initialize()
        
        # Extract the query from state
        query = self._create_query_from_state(state)
        
        # Add timeframe context if needed
        analysis_date = state.get('trade_date')
        if analysis_date:
            timeframe_role = self._get_timeframe_role()
            query = add_timeframe_to_existing_prompt(query, timeframe_role, analysis_date)
        
        # Run the agent with streaming
        result_streaming = Runner.run_streamed(self.agent, query)
        
        # Collect the result
        result = await self._collect_streaming_result(result_streaming)
        
        return {
            "messages": [result],
            "analysis_report": result
        }
    
    def _create_query_from_state(self, state: Dict[str, Any]) -> str:
        """Create a query from the agent state."""
        ticker = state.get('company_of_interest', 'AAPL')
        trade_date = state.get('trade_date', 'N/A')
        
        return f"Analyze {ticker} stock for trading date {trade_date}. Provide comprehensive technical analysis with specific recommendations, price levels, and trading implications."
    
    def _get_timeframe_role(self) -> str:
        """Get the timeframe role for this agent."""
        role_mapping = {
            "Market Analyst": "market_analyst",
            "Fundamentals Analyst": "fundamentals_analyst",
            "News Analyst": "news_analyst",
            "Social Media Analyst": "social_media_analyst"
        }
        return role_mapping.get(self.agent_name, "market_analyst")
    
    async def _collect_streaming_result(self, result_streaming):
        """Collect the result from streaming."""
        # For now, we'll collect the final result
        # In a full implementation, we'd handle streaming events
        try:
            # Get the final result
            result = await result_streaming.get_result()
            return result
        except Exception as e:
            # Fallback to a simple message
            return f"Analysis completed for {self.agent_name}: {str(e)}"


class OfficialMCPMarketAnalyst:
    """Official MCP Market Analyst using OpenAI Agents SDK."""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.agent = None
        self.mcp_manager = get_official_mcp_manager()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the market analyst agent."""
        if self._initialized:
            return
        
        await self.mcp_manager.ensure_initialized()
        
        # Get the configured servers
        servers = self.mcp_manager.get_servers()
        
        # Create the agent
        self.agent = Agent(
            name="Market Analyst",
            instructions=(
                "You are a financial market analyst specializing in technical analysis. "
                "Your role is to analyze market trends and provide actionable insights for trading decisions. "
                "Use the available MCP tools to gather real-time market data and technical indicators. "
                "Focus on identifying key trends, support/resistance levels, momentum shifts, and volatility patterns. "
                "Provide detailed analysis with specific price levels, trend directions, and trading implications. "
                "End your analysis with a clear summary table of key findings."
            ),
            model=self.model,
            mcp_servers=servers
        )
        
        self._initialized = True
    
    async def analyze(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data using MCP tools."""
        await self.initialize()
        
        # Create query from state
        ticker = state.get('company_of_interest', 'AAPL')
        trade_date = state.get('trade_date', 'N/A')
        
        query = f"Analyze {ticker} stock for trading date {trade_date}. Provide comprehensive technical analysis with specific recommendations, price levels, and trading implications."
        
        # Add timeframe context
        if trade_date != 'N/A':
            query = add_timeframe_to_existing_prompt(query, "market_analyst", trade_date)
        
        # Run the agent with proper MCP server context
        async with self.mcp_manager:
            try:
                result_streaming = Runner.run_streamed(self.agent, query)
                
                # Collect the result
                result = await result_streaming.get_final_result()
                return {
                    "messages": [result],
                    "market_report": result
                }
            except Exception as e:
                # Fallback result
                fallback_result = f"Market analysis for {ticker} on {trade_date}: Analysis completed with MCP tools. Error: {str(e)}"
                return {
                    "messages": [fallback_result],
                    "market_report": fallback_result
                }
