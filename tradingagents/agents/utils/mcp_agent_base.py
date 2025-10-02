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
        
        try:
            await self.mcp_manager.ensure_initialized()
        except Exception as e:
            print(f"Warning: Failed to initialize MCP manager: {e}")
            # Continue with mock MCP session
        except BaseException as e:
            print(f"Warning: MCP manager initialization failed: {e}")
            # Continue with mock MCP session
        
        # Discover tools from all configured MCP servers
        for server_name in self.mcp_servers:
            try:
                # Try real MCP server first
                if server_name == "alphavantage":
                    from tradingagents.dataflows.alpha_vantage_mcp_client import AlphaVantageMCPClient
                    import os
                    
                    api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'TQS06EXKTHWU639G')
                    async with AlphaVantageMCPClient(api_key) as client:
                        tools_result = await client.list_tools()
                        if tools_result:
                            for tool in tools_result:
                                tool_key = f"{server_name}_{tool['name']}"
                                self._available_tools[tool_key] = {
                                    'name': tool['name'],
                                    'description': tool['description'],
                                    'inputSchema': tool['inputSchema'],
                                    'server': server_name
                                }
                            print(f"✅ Connected to real Alpha Vantage MCP server - {len(tools_result)} tools available")
                            continue
                
                # Fallback to mock MCP session
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
                # Continue with other servers
        
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
    
    def _map_alpha_vantage_parameters(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Map parameters for Alpha Vantage MCP tools."""
        # Default parameters for technical indicators
        if tool_name in ['SMA', 'EMA', 'RSI', 'MACD', 'BBANDS', 'ATR']:
            mapped = {
                'symbol': arguments.get('symbol', 'AAPL'),
                'interval': 'daily'
            }
            
            # Add specific parameters for each tool
            if tool_name in ['SMA', 'EMA', 'RSI']:
                mapped.update({
                    'series_type': 'close',
                    'time_period': arguments.get('time_period', 20)
                })
            elif tool_name == 'ATR':
                # ATR doesn't need series_type, only symbol, interval, and time_period
                mapped['time_period'] = arguments.get('time_period', 14)
            elif tool_name == 'MACD':
                # MACD has different default parameters
                mapped.update({
                    'series_type': 'close',
                    'fastperiod': 12,
                    'slowperiod': 26,
                    'signalperiod': 9
                })
            elif tool_name == 'BBANDS':
                mapped.update({
                    'series_type': 'close',
                    'time_period': arguments.get('time_period', 20),
                    'nbdevup': 2,
                    'nbdevdn': 2
                })
            
            return mapped
        
        # For TIME_SERIES_DAILY, use the original arguments
        elif tool_name == 'TIME_SERIES_DAILY':
            return {
                'symbol': arguments.get('symbol', 'AAPL'),
                'outputsize': arguments.get('outputsize', 'compact')
            }
        
        # For other tools, return original arguments
        return arguments
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """Call an MCP tool and return formatted result."""
        # Map mock tool names to real MCP tool names
        tool_name_mapping = {
            'get_time_series_daily': 'TIME_SERIES_DAILY',
            'get_sma': 'SMA',
            'get_rsi': 'RSI',
            'get_macd': 'MACD',
            'get_bbands': 'BBANDS',
            'get_atr': 'ATR'
        }
        
        # Use mapped name if available
        real_tool_name = tool_name_mapping.get(tool_name, tool_name)
        
        # Find the tool in available tools
        tool_info = None
        for tool_key, info in self._available_tools.items():
            if info['name'] == real_tool_name:
                tool_info = info
                break
        
        if not tool_info:
            return f"Error: Tool '{real_tool_name}' not found in available tools."
        
        try:
            # Use custom Alpha Vantage MCP client for real server
            if tool_info['server'] == "alphavantage":
                from tradingagents.dataflows.alpha_vantage_mcp_client import AlphaVantageMCPClient
                import os
                
                # Map parameters for Alpha Vantage tools
                mapped_arguments = self._map_alpha_vantage_parameters(real_tool_name, arguments or {})
                
                api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'TQS06EXKTHWU639G')
                async with AlphaVantageMCPClient(api_key) as client:
                    result = await client.call_tool(real_tool_name, mapped_arguments)
            else:
                # Use regular MCP manager for other servers
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
                        content = str(result['content'][0]['text'])
                    else:
                        content = "\n".join(str(item['text']) for item in result['content'])
                    
                # Truncate large responses to prevent context length issues
                # Use more aggressive truncation like the Alpha Vantage example
                if len(content) > 10000:  # Limit to ~10k characters (more conservative)
                    content = content[:10000] + "\n\n[Data truncated due to size - showing first 10,000 characters]"
                    
                    return content
                elif 'error' in result:
                    return f"Error: {result['error']}"
                else:
                    return f"Tool '{tool_name}' executed successfully but returned no content."
            elif hasattr(result, 'content') and result.content:
                # Real MCP session result format
                if len(result.content) == 1:
                    content = str(result.content[0].text)
                else:
                    content = "\n".join(str(item.text) for item in result.content)
                
                # Truncate large responses to prevent context length issues
                # Use more aggressive truncation like the Alpha Vantage example
                if len(content) > 10000:  # Limit to ~10k characters (more conservative)
                    # For time series data, try to extract recent data instead of just truncating
                    if 'time_series' in tool_name.lower() or 'daily' in tool_name.lower():
                        content = self._extract_recent_time_series_data(content, 10000)
                    else:
                        content = content[:10000] + "\n\n[Data truncated due to size - showing first 10,000 characters]"
                
                return content
            else:
                return f"Tool '{tool_name}' executed successfully but returned no content."
                
        except Exception as e:
            return f"Error calling tool '{tool_name}': {str(e)}"
    
    def _extract_recent_time_series_data(self, content: str, max_length: int) -> str:
        """Extract recent time series data instead of just truncating from the beginning."""
        try:
            # Split by lines to process time series data
            lines = content.split('\n')
            
            # If it looks like CSV data (date,value format), take the most recent entries
            if len(lines) > 10 and ',' in lines[0]:
                # Take the last portion of the data (most recent)
                recent_lines = lines[-50:]  # Take last 50 data points
                recent_content = '\n'.join(recent_lines)
                
                if len(recent_content) <= max_length:
                    return f"[Showing most recent data points]\n{recent_content}"
                else:
                    return recent_content[:max_length] + "\n\n[Data truncated - showing most recent entries]"
            else:
                # For other data types, just truncate from the end
                return content[:max_length] + "\n\n[Data truncated due to size]"
                
        except Exception:
            # Fallback to simple truncation
            return content[:max_length] + "\n\n[Data truncated due to size]"
    
    
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
            
            # Log tool calls for CLI tracking
            print(f"🔧 MCP Tool Calls: {len(tool_calls)} tools used for {ticker}")
            for tool in tool_calls:
                print(f"  - {tool['name']}: {tool['args']}")
            
            # Also log to message log for CLI tracking
            import logging
            logger = logging.getLogger("mcp_tool_calls")
            for tool in tool_calls:
                logger.info(f"MCP Tool Call: {tool['name']} - {tool['args']}")
            
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
