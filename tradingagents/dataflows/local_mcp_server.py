"""Local MCP server implementation for TradingAgents."""

import asyncio
import json
from typing import Dict, Any, List
from mcp.server import Server
from mcp.server.models import Tool, TextContent
from mcp.types import Tool as MCPTool

# Import existing Alpha Vantage tools
from .alpha_vantage_indicator import get_indicator
from .alpha_vantage_common import _make_api_request


class LocalMCPServer:
    """Local MCP server that wraps existing Alpha Vantage tools."""
    
    def __init__(self):
        self.server = Server("tradingagents-local")
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools."""
        
        @self.server.list_tools()
        async def list_tools() -> List[MCPTool]:
            """List available tools."""
            return [
                MCPTool(
                    name="get_time_series_daily",
                    description="Get daily stock price data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"},
                            "outputsize": {"type": "string", "description": "Output size (compact or full)"}
                        },
                        "required": ["symbol"]
                    }
                ),
                MCPTool(
                    name="get_sma",
                    description="Get Simple Moving Average",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"},
                            "interval": {"type": "string", "description": "Data interval"},
                            "time_period": {"type": "integer", "description": "Time period"}
                        },
                        "required": ["symbol"]
                    }
                ),
                MCPTool(
                    name="get_ema",
                    description="Get Exponential Moving Average",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"},
                            "interval": {"type": "string", "description": "Data interval"},
                            "time_period": {"type": "integer", "description": "Time period"}
                        },
                        "required": ["symbol"]
                    }
                ),
                MCPTool(
                    name="get_rsi",
                    description="Get Relative Strength Index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"},
                            "interval": {"type": "string", "description": "Data interval"},
                            "time_period": {"type": "integer", "description": "Time period"}
                        },
                        "required": ["symbol"]
                    }
                ),
                MCPTool(
                    name="get_macd",
                    description="Get MACD indicator",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"},
                            "interval": {"type": "string", "description": "Data interval"}
                        },
                        "required": ["symbol"]
                    }
                ),
                MCPTool(
                    name="get_bbands",
                    description="Get Bollinger Bands",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"},
                            "interval": {"type": "string", "description": "Data interval"},
                            "time_period": {"type": "integer", "description": "Time period"}
                        },
                        "required": ["symbol"]
                    }
                ),
                MCPTool(
                    name="get_atr",
                    description="Get Average True Range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"},
                            "interval": {"type": "string", "description": "Data interval"},
                            "time_period": {"type": "integer", "description": "Time period"}
                        },
                        "required": ["symbol"]
                    }
                ),
                MCPTool(
                    name="get_company_overview",
                    description="Get company fundamental data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Stock symbol"}
                        },
                        "required": ["symbol"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Call a tool by name with arguments."""
            try:
                if name == "get_time_series_daily":
                    return await self._get_time_series_daily(arguments)
                elif name == "get_sma":
                    return await self._get_sma(arguments)
                elif name == "get_ema":
                    return await self._get_ema(arguments)
                elif name == "get_rsi":
                    return await self._get_rsi(arguments)
                elif name == "get_macd":
                    return await self._get_macd(arguments)
                elif name == "get_bbands":
                    return await self._get_bbands(arguments)
                elif name == "get_atr":
                    return await self._get_atr(arguments)
                elif name == "get_company_overview":
                    return await self._get_company_overview(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error calling {name}: {str(e)}")]
    
    async def _get_time_series_daily(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get daily time series data."""
        symbol = args.get("symbol")
        if not symbol:
            return [TextContent(type="text", text="Symbol is required")]
        
        try:
            # Use existing Alpha Vantage API
            data = _make_api_request("TIME_SERIES_DAILY", symbol=symbol)
            if data:
                return [TextContent(type="text", text=f"Daily data for {symbol}: {json.dumps(data, indent=2)}")]
            else:
                return [TextContent(type="text", text=f"No data available for {symbol}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting daily data: {str(e)}")]
    
    async def _get_sma(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get SMA indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 20)
        
        if not symbol:
            return [TextContent(type="text", text="Symbol is required")]
        
        try:
            result = get_indicator(symbol, "SMA", "2024-01-01", 100, "daily", time_period)
            return [TextContent(type="text", text=f"SMA({time_period}) for {symbol}: {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting SMA: {str(e)}")]
    
    async def _get_ema(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get EMA indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 20)
        
        if not symbol:
            return [TextContent(type="text", text="Symbol is required")]
        
        try:
            result = get_indicator(symbol, "EMA", "2024-01-01", 100, "daily", time_period)
            return [TextContent(type="text", text=f"EMA({time_period}) for {symbol}: {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting EMA: {str(e)}")]
    
    async def _get_rsi(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get RSI indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 14)
        
        if not symbol:
            return [TextContent(type="text", text="Symbol is required")]
        
        try:
            result = get_indicator(symbol, "RSI", "2024-01-01", 100, "daily", time_period)
            return [TextContent(type="text", text=f"RSI({time_period}) for {symbol}: {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting RSI: {str(e)}")]
    
    async def _get_macd(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get MACD indicator."""
        symbol = args.get("symbol")
        
        if not symbol:
            return [TextContent(type="text", text="Symbol is required")]
        
        try:
            result = get_indicator(symbol, "MACD", "2024-01-01", 100, "daily")
            return [TextContent(type="text", text=f"MACD for {symbol}: {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting MACD: {str(e)}")]
    
    async def _get_bbands(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get Bollinger Bands indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 20)
        
        if not symbol:
            return [TextContent(type="text", text="Symbol is required")]
        
        try:
            result = get_indicator(symbol, "BBANDS", "2024-01-01", 100, "daily", time_period)
            return [TextContent(type="text", text=f"Bollinger Bands({time_period}) for {symbol}: {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting Bollinger Bands: {str(e)}")]
    
    async def _get_atr(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get ATR indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 14)
        
        if not symbol:
            return [TextContent(type="text", text="Symbol is required")]
        
        try:
            result = get_indicator(symbol, "ATR", "2024-01-01", 100, "daily", time_period)
            return [TextContent(type="text", text=f"ATR({time_period}) for {symbol}: {result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting ATR: {str(e)}")]
    
    async def _get_company_overview(self, args: Dict[str, Any]) -> List[TextContent]:
        """Get company overview."""
        symbol = args.get("symbol")
        
        if not symbol:
            return [TextContent(type="text", text="Symbol is required")]
        
        try:
            data = _make_api_request("OVERVIEW", symbol=symbol)
            if data:
                return [TextContent(type="text", text=f"Company overview for {symbol}: {json.dumps(data, indent=2)}")]
            else:
                return [TextContent(type="text", text=f"No company data available for {symbol}")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting company overview: {str(e)}")]


# Global server instance
_local_server = None

def get_local_server():
    """Get the local MCP server instance."""
    global _local_server
    if _local_server is None:
        _local_server = LocalMCPServer()
    return _local_server

