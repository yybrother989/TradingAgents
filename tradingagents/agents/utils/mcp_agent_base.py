"""Base MCP Agent class for TradingAgents."""

import asyncio
from typing import Dict, List, Any, Optional, Union
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, ToolMessage
from tradingagents.dataflows.mcp_manager import get_mcp_manager
from .timeframe_utils import (
    calculate_timeframes_from_analysis_date,
    add_timeframe_to_existing_prompt
)


class MCPAgent:
    """Base class for MCP-enabled agents in TradingAgents."""
    
    def __init__(self, agent_name: str, mcp_servers: List[str] = None):
        self.agent_name = agent_name
        self.mcp_servers = mcp_servers or ["alphavantage"]
        self.mcp_manager = get_mcp_manager()
        self._available_tools = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize MCP connections and discover available tools."""
        if self._initialized:
            return
        
        await self.mcp_manager.ensure_initialized()
        
        # Discover tools from all configured MCP servers
        for server_name in self.mcp_servers:
            try:
                session = self.mcp_manager.get_session(server_name)
                if session:
                    tools_result = await session.list_tools()
                    # Handle both real MCP sessions and mock sessions
                    if hasattr(tools_result, 'tools'):
                        # Real MCP session
                        for tool in tools_result.tools:
                            tool_key = f"{server_name}_{tool.name}"
                            self._available_tools[tool_key] = {
                                'name': tool.name,
                                'description': tool.description,
                                'inputSchema': tool.inputSchema,
                                'server': server_name
                            }
                    elif isinstance(tools_result, list):
                        # Mock session
                        for tool in tools_result:
                            tool_key = f"{server_name}_{tool['name']}"
                            self._available_tools[tool_key] = {
                                'name': tool['name'],
                                'description': tool['description'],
                                'inputSchema': tool['inputSchema'],
                                'server': server_name
                            }
            except Exception as e:
                print(f"Warning: Failed to discover tools from {server_name}: {e}")
        
        self._initialized = True
    
    def get_available_tools(self) -> Dict[str, Any]:
        """Get list of available MCP tools."""
        return self._available_tools.copy()
    
    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions for prompts."""
        if not self._available_tools:
            return "No tools available."
        
        descriptions = []
        for tool_key, tool_info in self._available_tools.items():
            desc = f"- **{tool_info['name']}**: {tool_info['description']}"
            if tool_info.get('inputSchema', {}).get('properties'):
                params = list(tool_info['inputSchema']['properties'].keys())
                desc += f" (Parameters: {', '.join(params)})"
            descriptions.append(desc)
        
        return "\n".join(descriptions)
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """Call an MCP tool and return formatted result."""
        # Find the tool in available tools
        tool_info = None
        for tool_key, info in self._available_tools.items():
            if info['name'] == tool_name:
                tool_info = info
                break
        
        if not tool_info:
            return f"Error: Tool '{tool_name}' not found in available tools."
        
        try:
            result = await self.mcp_manager.call_tool(
                tool_info['server'], 
                tool_name, 
                arguments or {}
            )
            
            # Format the result
            if isinstance(result, dict):
                # Mock session result format
                if 'content' in result and result['content']:
                    if len(result['content']) == 1:
                        return str(result['content'][0]['text'])
                    else:
                        return "\n".join(str(item['text']) for item in result['content'])
                elif 'error' in result:
                    return f"Error: {result['error']}"
                else:
                    return f"Tool '{tool_name}' executed successfully but returned no content."
            elif hasattr(result, 'content') and result.content:
                # Real MCP session result format
                if len(result.content) == 1:
                    return str(result.content[0].text)
                else:
                    return "\n".join(str(item.text) for item in result.content)
            else:
                return f"Tool '{tool_name}' executed successfully but returned no content."
                
        except Exception as e:
            return f"Error calling tool '{tool_name}': {str(e)}"
    
    async def _execute_tool_calls_from_content(self, content: str, state: Dict[str, Any]) -> str:
        """Execute tool calls based on content analysis."""
        ticker = state.get('company_of_interest', 'AAPL')
        results = []
        
        # Check for specific tool calls in content
        if "get_time_series_daily" in content or "daily data" in content.lower():
            try:
                result = await self.call_tool("get_time_series_daily", {"symbol": ticker, "outputsize": "full"})
                results.append(f"Daily Price Data for {ticker}:\n{result}")
            except Exception as e:
                results.append(f"Error getting daily data: {str(e)}")
        
        if "get_sma" in content or "moving average" in content.lower() or "sma" in content.lower():
            try:
                result = await self.call_tool("get_sma", {"symbol": ticker, "time_period": 20})
                results.append(f"20-day SMA for {ticker}:\n{result}")
            except Exception as e:
                results.append(f"Error getting SMA: {str(e)}")
        
        if "get_rsi" in content or "rsi" in content.lower():
            try:
                result = await self.call_tool("get_rsi", {"symbol": ticker, "time_period": 14})
                results.append(f"14-day RSI for {ticker}:\n{result}")
            except Exception as e:
                results.append(f"Error getting RSI: {str(e)}")
        
        if "get_macd" in content or "macd" in content.lower():
            try:
                result = await self.call_tool("get_macd", {"symbol": ticker})
                results.append(f"MACD for {ticker}:\n{result}")
            except Exception as e:
                results.append(f"Error getting MACD: {str(e)}")
        
        if "get_bbands" in content or "bollinger" in content.lower():
            try:
                result = await self.call_tool("get_bbands", {"symbol": ticker, "time_period": 20})
                results.append(f"Bollinger Bands for {ticker}:\n{result}")
            except Exception as e:
                results.append(f"Error getting Bollinger Bands: {str(e)}")
        
        if "get_atr" in content or "atr" in content.lower():
            try:
                result = await self.call_tool("get_atr", {"symbol": ticker, "time_period": 14})
                results.append(f"14-day ATR for {ticker}:\n{result}")
            except Exception as e:
                results.append(f"Error getting ATR: {str(e)}")
        
        return "\n\n".join(results) if results else ""
    
    async def _execute_standard_tool_calls(self, ticker: str) -> str:
        """Execute standard tool calls to get comprehensive market data."""
        results = []
        
        try:
            # Get daily price data
            result = await self.call_tool("get_time_series_daily", {"symbol": ticker, "outputsize": "full"})
            results.append(f"Daily Price Data for {ticker}:\n{result}")
        except Exception as e:
            results.append(f"Error getting daily data: {str(e)}")
        
        try:
            # Get SMA
            result = await self.call_tool("get_sma", {"symbol": ticker, "time_period": 20})
            results.append(f"20-day SMA for {ticker}:\n{result}")
        except Exception as e:
            results.append(f"Error getting SMA: {str(e)}")
        
        try:
            # Get RSI
            result = await self.call_tool("get_rsi", {"symbol": ticker, "time_period": 14})
            results.append(f"14-day RSI for {ticker}:\n{result}")
        except Exception as e:
            results.append(f"Error getting RSI: {str(e)}")
        
        try:
            # Get MACD
            result = await self.call_tool("get_macd", {"symbol": ticker})
            results.append(f"MACD for {ticker}:\n{result}")
        except Exception as e:
            results.append(f"Error getting MACD: {str(e)}")
        
        try:
            # Get Bollinger Bands
            result = await self.call_tool("get_bbands", {"symbol": ticker, "time_period": 20})
            results.append(f"Bollinger Bands for {ticker}:\n{result}")
        except Exception as e:
            results.append(f"Error getting Bollinger Bands: {str(e)}")
        
        try:
            # Get ATR
            result = await self.call_tool("get_atr", {"symbol": ticker, "time_period": 14})
            results.append(f"14-day ATR for {ticker}:\n{result}")
        except Exception as e:
            results.append(f"Error getting ATR: {str(e)}")
        
        return "\n\n".join(results) if results else ""
    
    def create_simplified_prompt(self, system_message: str, llm, analysis_date: str = None) -> ChatPromptTemplate:
        """Create a simplified prompt that focuses on analysis rather than tool usage."""
        
        # Add timeframe context if analysis_date is provided
        if analysis_date:
            # Map agent name to timeframe role
            role_timeframe_mapping = {
                'Market Analyst': 'market_analyst',
                'Fundamentals Analyst': 'fundamentals_analyst', 
                'Social Media Analyst': 'social_media_analyst',
                'News Analyst': 'news_analyst',
                'Risk Manager': 'risk_manager',
                'Research Manager': 'research_manager',
                'Bull Researcher': 'bull_researcher',
                'Bear Researcher': 'bear_researcher',
                'Trader': 'trader'
            }
            
            timeframe_role = role_timeframe_mapping.get(self.agent_name, 'market_analyst')
            system_message = add_timeframe_to_existing_prompt(system_message, timeframe_role, analysis_date)
        
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                f"You are a {self.agent_name} AI assistant specializing in financial analysis. "
                f"{system_message}\n\n"
                f"You have access to the following MCP tools:\n{{tool_descriptions}}\n\n"
                f"IMPORTANT: You MUST use these tools to gather real market data before providing analysis. "
                f"Start your response by calling the appropriate tools to get current market data, "
                f"then provide detailed analysis based on the actual data retrieved.\n\n"
                f"Current context: {{context_info}}\n\n"
                f"Begin by calling get_time_series_daily to get price data, then call technical indicators "
                f"like get_sma, get_rsi, get_macd, get_bbands, and get_atr to gather comprehensive market data."
            ),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        return prompt
    
    async def execute_analysis(self, state: Dict[str, Any], llm, system_message: str) -> Dict[str, Any]:
        """Execute analysis using MCP tools and LLM."""
        await self.initialize()
        
        # Create context info
        context_info = f"Date: {state.get('trade_date', 'N/A')}, Ticker: {state.get('company_of_interest', 'N/A')}"
        
        # Get analysis date for timeframe context
        analysis_date = state.get('trade_date', 'N/A')
        
        # Create simplified prompt with timeframe support
        prompt = self.create_simplified_prompt(system_message, llm, analysis_date)
        
        # Get tool descriptions
        tool_descriptions = self.get_tool_descriptions()
        
        # Prepare prompt with context
        formatted_prompt = prompt.partial(
            tool_descriptions=tool_descriptions,
            context_info=context_info
        )
        
        # Create a chain that can handle tool calls
        # We need to create a custom tool calling mechanism for MCP
        chain = formatted_prompt | llm
        
        # Execute the chain
        result = chain.invoke(state["messages"])
        
        # Always execute tool calls to get real data
        ticker = state.get('company_of_interest', 'AAPL')
        tool_results = await self._execute_standard_tool_calls(ticker)
        
        if tool_results:
            # Create tool call messages for CLI tracking
            from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
            tool_calls = []
            tool_messages = []
            
            # Create tool call messages for each tool used
            tools_used = [
                {"name": "get_time_series_daily", "args": {"symbol": ticker, "outputsize": "full"}},
                {"name": "get_sma", "args": {"symbol": ticker, "time_period": 20}},
                {"name": "get_rsi", "args": {"symbol": ticker, "time_period": 14}},
                {"name": "get_macd", "args": {"symbol": ticker}},
                {"name": "get_bbands", "args": {"symbol": ticker, "time_period": 20}},
                {"name": "get_atr", "args": {"symbol": ticker, "time_period": 14}}
            ]
            
            for tool in tools_used:
                tool_calls.append({
                    "name": tool["name"],
                    "args": tool["args"],
                    "id": f"call_{tool['name']}_{ticker}"
                })
                tool_messages.append(ToolMessage(
                    content=f"Executed {tool['name']} for {ticker}",
                    tool_call_id=f"call_{tool['name']}_{ticker}"
                ))
            
            # Create a message with tool calls for CLI tracking
            tool_call_message = AIMessage(
                content=f"Gathering market data for {ticker} using MCP tools...",
                tool_calls=tool_calls
            )
            
            # Create a new message with tool results
            tool_message = f"Based on the following real market data for {ticker}:\n\n{tool_results}\n\nPlease provide a comprehensive technical analysis report with specific recommendations, price levels, and trading implications."
            follow_up_result = chain.invoke([HumanMessage(content=tool_message)])
            
            # Combine the tool call message with the final result
            result = AIMessage(
                content=follow_up_result.content,
                tool_calls=tool_calls
            )
        
        # Process tool calls if any
        if hasattr(result, 'tool_calls') and result.tool_calls:
            # Execute tool calls and get results
            tool_messages = []
            for tool_call in result.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call.get('args', {})
                
                # Call the MCP tool
                tool_result = await self.call_tool(tool_name, tool_args)
                
                # Create tool message
                tool_message = ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call['id']
                )
                tool_messages.append(tool_message)
            
            # Add tool messages to the conversation
            messages = state["messages"] + [result] + tool_messages
            
            # Get final analysis from LLM
            final_result = chain.invoke(messages)
            
            return {
                "messages": [result] + tool_messages + [final_result],
                "analysis_report": final_result.content if hasattr(final_result, 'content') else str(final_result)
            }
        else:
            return {
                "messages": [result],
                "analysis_report": result.content if hasattr(result, 'content') else str(result)
            }
