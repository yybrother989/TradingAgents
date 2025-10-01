"""Alpha Vantage MCP integration for TradingAgents."""

import asyncio
import pandas as pd
from typing import Dict, Any, Optional
from .mcp_manager import get_mcp_manager, call_alpha_vantage_tool
from .config import get_config


async def get_stock_data_mcp(
    symbol: str,
    start_date: str,
    end_date: str,
    interval: str = "daily"
) -> str:
    """
    Get stock data using Alpha Vantage MCP server.
    
    Args:
        symbol: Stock symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        interval: Data interval (daily, weekly, monthly)
    
    Returns:
        Formatted string containing stock data
    """
    try:
        # Call the Alpha Vantage MCP tool for time series data
        result = await call_alpha_vantage_tool(
            "get_time_series_daily",
            {
                "symbol": symbol,
                "outputsize": "full"
            }
        )
        
        # Process the result and filter by date range
        if hasattr(result, 'content') and result.content:
            # Convert to DataFrame for processing
            data = []
            for item in result.content:
                if hasattr(item, 'text'):
                    # Parse the text content (assuming it's JSON)
                    import json
                    try:
                        data_dict = json.loads(item.text)
                        if 'Time Series (Daily)' in data_dict:
                            time_series = data_dict['Time Series (Daily)']
                            for date, values in time_series.items():
                                if start_date <= date <= end_date:
                                    data.append({
                                        'date': date,
                                        'open': float(values['1. open']),
                                        'high': float(values['2. high']),
                                        'low': float(values['3. low']),
                                        'close': float(values['4. close']),
                                        'volume': int(values['5. volume'])
                                    })
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Warning: Error parsing Alpha Vantage data: {e}")
                        continue
            
            if data:
                df = pd.DataFrame(data)
                df = df.sort_values('date')
                return f"Stock data for {symbol} from {start_date} to {end_date}:\n{df.to_string(index=False)}"
            else:
                return f"No data found for {symbol} in the specified date range."
        else:
            return f"Failed to retrieve data for {symbol}"
            
    except Exception as e:
        return f"Error retrieving stock data for {symbol}: {str(e)}"


async def get_indicators_mcp(
    symbol: str,
    indicators: list,
    interval: str = "daily"
) -> str:
    """
    Get technical indicators using Alpha Vantage MCP server.
    
    Args:
        symbol: Stock symbol
        indicators: List of indicator names
        interval: Data interval (daily, weekly, monthly)
    
    Returns:
        Formatted string containing indicator data
    """
    try:
        results = []
        
        for indicator in indicators:
            try:
                # Map indicator names to Alpha Vantage function names
                indicator_mapping = {
                    'sma': 'get_sma',
                    'ema': 'get_ema',
                    'rsi': 'get_rsi',
                    'macd': 'get_macd',
                    'bollinger_bands': 'get_bbands',
                    'stoch': 'get_stoch',
                    'adx': 'get_adx',
                    'cci': 'get_cci',
                    'williams_r': 'get_willr',
                    'atr': 'get_atr'
                }
                
                av_function = indicator_mapping.get(indicator.lower())
                if not av_function:
                    results.append(f"Indicator '{indicator}' not supported")
                    continue
                
                # Call the appropriate Alpha Vantage MCP tool
                result = await call_alpha_vantage_tool(
                    av_function,
                    {
                        "symbol": symbol,
                        "interval": interval,
                        "time_period": 20  # Default period
                    }
                )
                
                if hasattr(result, 'content') and result.content:
                    results.append(f"{indicator.upper()} data for {symbol}:\n{result.content[0].text if result.content else 'No data'}")
                else:
                    results.append(f"No {indicator} data available for {symbol}")
                    
            except Exception as e:
                results.append(f"Error retrieving {indicator} for {symbol}: {str(e)}")
        
        return "\n\n".join(results)
        
    except Exception as e:
        return f"Error retrieving indicators for {symbol}: {str(e)}"


async def get_fundamentals_mcp(symbol: str) -> str:
    """
    Get fundamental data using Alpha Vantage MCP server.
    
    Args:
        symbol: Stock symbol
    
    Returns:
        Formatted string containing fundamental data
    """
    try:
        # Get company overview
        overview_result = await call_alpha_vantage_tool(
            "get_company_overview",
            {"symbol": symbol}
        )
        
        if hasattr(overview_result, 'content') and overview_result.content:
            return f"Fundamental data for {symbol}:\n{overview_result.content[0].text if overview_result.content else 'No data'}"
        else:
            return f"No fundamental data available for {symbol}"
            
    except Exception as e:
        return f"Error retrieving fundamental data for {symbol}: {str(e)}"


async def get_news_mcp(symbol: str, limit: int = 10) -> str:
    """
    Get news data using Alpha Vantage MCP server.
    
    Args:
        symbol: Stock symbol
        limit: Maximum number of news items
    
    Returns:
        Formatted string containing news data
    """
    try:
        result = await call_alpha_vantage_tool(
            "get_news_sentiment",
            {
                "symbol": symbol,
                "limit": limit
            }
        )
        
        if hasattr(result, 'content') and result.content:
            return f"News data for {symbol}:\n{result.content[0].text if result.content else 'No data'}"
        else:
            return f"No news data available for {symbol}"
            
    except Exception as e:
        return f"Error retrieving news data for {symbol}: {str(e)}"


# Synchronous wrapper functions for compatibility with existing interface
def get_stock_data_mcp_sync(symbol: str, start_date: str, end_date: str, interval: str = "daily") -> str:
    """Synchronous wrapper for get_stock_data_mcp."""
    return asyncio.run(get_stock_data_mcp(symbol, start_date, end_date, interval))


def get_indicators_mcp_sync(symbol: str, indicators: list, interval: str = "daily") -> str:
    """Synchronous wrapper for get_indicators_mcp."""
    return asyncio.run(get_indicators_mcp(symbol, indicators, interval))


def get_fundamentals_mcp_sync(symbol: str) -> str:
    """Synchronous wrapper for get_fundamentals_mcp."""
    return asyncio.run(get_fundamentals_mcp(symbol))


def get_news_mcp_sync(symbol: str, limit: int = 10) -> str:
    """Synchronous wrapper for get_news_mcp."""
    return asyncio.run(get_news_mcp(symbol, limit))
