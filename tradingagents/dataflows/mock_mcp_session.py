"""Mock MCP session that uses existing Alpha Vantage tools directly."""

import asyncio
from typing import Dict, Any, List
from mcp import ClientSession
from .alpha_vantage_indicator import get_indicator
from .alpha_vantage_common import _make_api_request


class MockMCPSession:
    """Mock MCP session that wraps existing Alpha Vantage tools."""
    
    def __init__(self):
        self.tools = [
            {
                "name": "get_time_series_daily",
                "description": "Get daily stock price data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol"},
                        "outputsize": {"type": "string", "description": "Output size (compact or full)"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_sma",
                "description": "Get Simple Moving Average",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol"},
                        "interval": {"type": "string", "description": "Data interval"},
                        "time_period": {"type": "integer", "description": "Time period"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_ema",
                "description": "Get Exponential Moving Average",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol"},
                        "interval": {"type": "string", "description": "Data interval"},
                        "time_period": {"type": "integer", "description": "Time period"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_rsi",
                "description": "Get Relative Strength Index",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol"},
                        "interval": {"type": "string", "description": "Data interval"},
                        "time_period": {"type": "integer", "description": "Time period"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_macd",
                "description": "Get MACD indicator",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol"},
                        "interval": {"type": "string", "description": "Data interval"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_bbands",
                "description": "Get Bollinger Bands",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol"},
                        "interval": {"type": "string", "description": "Data interval"},
                        "time_period": {"type": "integer", "description": "Time period"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_atr",
                "description": "Get Average True Range",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol"},
                        "interval": {"type": "string", "description": "Data interval"},
                        "time_period": {"type": "integer", "description": "Time period"}
                    },
                    "required": ["symbol"]
                }
            },
            {
                "name": "get_company_overview",
                "description": "Get company fundamental data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "symbol": {"type": "string", "description": "Stock symbol"}
                    },
                    "required": ["symbol"]
                }
            }
        ]
    
    async def list_tools(self):
        """List available tools."""
        return self.tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]):
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
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            return {"error": f"Error calling {name}: {str(e)}"}
    
    async def _get_time_series_daily(self, args: Dict[str, Any]):
        """Get daily time series data."""
        symbol = args.get("symbol")
        if not symbol:
            return {"error": "Symbol is required"}
        
        try:
            data = _make_api_request("TIME_SERIES_DAILY", {"symbol": symbol})
            if data:
                return {"content": [{"text": f"Daily data for {symbol}: {str(data)[:1000]}..."}]}
            else:
                return {"content": [{"text": f"No data available for {symbol}"}]}
        except Exception as e:
            return {"error": f"Error getting daily data: {str(e)}"}
    
    async def _get_sma(self, args: Dict[str, Any]):
        """Get SMA indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 20)
        
        if not symbol:
            return {"error": "Symbol is required"}
        
        try:
            result = get_indicator(symbol, "close_50_sma", "2024-01-01", 100, "daily", time_period)
            return {"content": [{"text": f"SMA({time_period}) for {symbol}: {result}"}]}
        except Exception as e:
            return {"error": f"Error getting SMA: {str(e)}"}
    
    async def _get_ema(self, args: Dict[str, Any]):
        """Get EMA indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 20)
        
        if not symbol:
            return {"error": "Symbol is required"}
        
        try:
            result = get_indicator(symbol, "close_10_ema", "2024-01-01", 100, "daily", time_period)
            return {"content": [{"text": f"EMA({time_period}) for {symbol}: {result}"}]}
        except Exception as e:
            return {"error": f"Error getting EMA: {str(e)}"}
    
    async def _get_rsi(self, args: Dict[str, Any]):
        """Get RSI indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 14)
        
        if not symbol:
            return {"error": "Symbol is required"}
        
        try:
            result = get_indicator(symbol, "rsi", "2024-01-01", 100, "daily", time_period)
            return {"content": [{"text": f"RSI({time_period}) for {symbol}: {result}"}]}
        except Exception as e:
            return {"error": f"Error getting RSI: {str(e)}"}
    
    async def _get_macd(self, args: Dict[str, Any]):
        """Get MACD indicator."""
        symbol = args.get("symbol")
        
        if not symbol:
            return {"error": "Symbol is required"}
        
        try:
            result = get_indicator(symbol, "macd", "2024-01-01", 100, "daily")
            return {"content": [{"text": f"MACD for {symbol}: {result}"}]}
        except Exception as e:
            return {"error": f"Error getting MACD: {str(e)}"}
    
    async def _get_bbands(self, args: Dict[str, Any]):
        """Get Bollinger Bands indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 20)
        
        if not symbol:
            return {"error": "Symbol is required"}
        
        try:
            result = get_indicator(symbol, "boll", "2024-01-01", 100, "daily", time_period)
            return {"content": [{"text": f"Bollinger Bands({time_period}) for {symbol}: {result}"}]}
        except Exception as e:
            return {"error": f"Error getting Bollinger Bands: {str(e)}"}
    
    async def _get_atr(self, args: Dict[str, Any]):
        """Get ATR indicator."""
        symbol = args.get("symbol")
        time_period = args.get("time_period", 14)
        
        if not symbol:
            return {"error": "Symbol is required"}
        
        try:
            result = get_indicator(symbol, "atr", "2024-01-01", 100, "daily", time_period)
            return {"content": [{"text": f"ATR({time_period}) for {symbol}: {result}"}]}
        except Exception as e:
            return {"error": f"Error getting ATR: {str(e)}"}
    
    async def _get_company_overview(self, args: Dict[str, Any]):
        """Get company overview."""
        symbol = args.get("symbol")
        
        if not symbol:
            return {"error": "Symbol is required"}
        
        try:
            data = _make_api_request("OVERVIEW", {"symbol": symbol})
            if data:
                return {"content": [{"text": f"Company overview for {symbol}: {str(data)[:1000]}..."}]}
            else:
                return {"content": [{"text": f"No company data available for {symbol}"}]}
        except Exception as e:
            return {"error": f"Error getting company overview: {str(e)}"}

