# MCP Server Setup Guide for TradingAgents

This guide follows the [official MCP deployment best practices](https://modelcontextprotocol.io) and the [Alpha Vantage MCP documentation](https://mcp.alphavantage.co/).

## Quick Start

### 1. Get Your Alpha Vantage API Key

1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Get your free API key (25 calls/day on free tier)
3. Save it securely

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required: Alpha Vantage API Key
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Optional: MCP Server URL (defaults to Alpha Vantage)
ALPHA_VANTAGE_MCP_URL=https://mcp.alphavantage.co/mcp

# Optional: Category Filtering (Principle of Least Privilege)
# Only expose the tool categories your agents need
ALPHA_VANTAGE_MCP_CATEGORIES=core_stock_apis,technical_indicators,alpha_intelligence

# Optional: Rate Limiting (defaults: 25 calls/day, 24 hour window)
ALPHA_VANTAGE_RATE_LIMIT_CALLS=25
ALPHA_VANTAGE_RATE_LIMIT_WINDOW=86400
```

### 3. Test the Setup

```bash
# Test MCP server connection
python -m tradingagents.dataflows.mcp_server_manager
```

Expected output:
```
✅ MCP initialized successfully
✅ Found 118 tools
✅ Tool call successful!
```

## Architecture

### Transport: HTTP (Recommended for Production)

We use **HTTP transport** as recommended for production deployments:
- ✅ Works reliably across networks
- ✅ Supports multiple clients
- ✅ Easy to monitor and debug
- ✅ No process management overhead

The URL format: `https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY`

### Category Filtering (Principle of Least Privilege)

Alpha Vantage MCP supports category filtering to restrict which tools are available:

| Category | Tools Included | Recommended For |
|----------|----------------|-----------------|
| `core_stock_apis` | TIME_SERIES_DAILY, TIME_SERIES_WEEKLY, etc. | Market Analyst |
| `technical_indicators` | SMA, EMA, RSI, MACD, BBANDS, ATR, etc. | Market Analyst |
| `alpha_intelligence` | NEWS_SENTIMENT | News Analyst, Social Analyst |
| `fundamentals` | COMPANY_OVERVIEW, EARNINGS, BALANCE_SHEET, etc. | Fundamentals Analyst |

**Example**: If you only need market data, set:
```bash
ALPHA_VANTAGE_MCP_CATEGORIES=core_stock_apis,technical_indicators
```

This reduces the attack surface and cognitive load for your agents.

## Production Best Practices

### 1. Centralize Authentication

✅ **DO**: Store API keys in environment variables
```python
api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
```

❌ **DON'T**: Hardcode API keys in source code
```python
api_key = "TQS06EXKTHWU639G"  # BAD!
```

### 2. Rate Limiting & Caching

The `ProductionMCPServerManager` includes:
- **Rate limiting**: Prevents exceeding API quotas
- **Caching**: Reduces redundant API calls
- **Retry logic**: Handles transient failures

```python
from tradingagents.dataflows.mcp_server_manager import get_mcp_manager

async with get_mcp_manager() as manager:
    # First call: hits API
    result1 = await manager.call_tool("TIME_SERIES_DAILY", {"symbol": "AAPL"})
    
    # Second call: returns cached result (within TTL)
    result2 = await manager.call_tool("TIME_SERIES_DAILY", {"symbol": "AAPL"})
```

### 3. Observability

Monitor MCP usage with built-in statistics:

```python
stats = manager.get_stats()
print(f"Total calls: {stats['total_calls']}")
print(f"Success rate: {stats['successful_calls'] / stats['total_calls'] * 100:.1f}%")
print(f"Cached calls: {stats['cached_calls']}")
print(f"Rate limited: {stats['rate_limited_calls']}")
```

### 4. Error Handling

The manager handles:
- **Network errors**: Automatic retries with exponential backoff
- **HTTP errors**: Distinguishes between client (4xx) and server (5xx) errors
- **Rate limiting**: Automatic wait time calculation
- **Timeouts**: Configurable per-request timeouts

## Usage in TradingAgents

The MCP server manager is automatically used by:
- `MCPAgent` base class (used by all analyst agents)
- `AlphaVantageMCPClient` (direct HTTP client)
- All analyst agents (Market, News, Social, Fundamentals)

No code changes needed - just set the environment variables!

## Troubleshooting

### "Failed to initialize MCP server"

1. **Check API key**: Ensure `ALPHA_VANTAGE_API_KEY` is set
2. **Check network**: Verify you can reach `https://mcp.alphavantage.co`
3. **Check rate limit**: Free tier allows 25 calls/day

### "Rate limit reached"

- **Free tier**: 25 calls per 24 hours
- **Solution**: Upgrade to premium tier or implement better caching
- **Workaround**: Clear cache and wait for rate limit window to reset

### "Tool not found"

- **Check categories**: Ensure the tool's category is included in `ALPHA_VANTAGE_MCP_CATEGORIES`
- **Check tool name**: Alpha Vantage uses uppercase tool names (e.g., `TIME_SERIES_DAILY`)

## Local Development (Optional)

For local development with stdio transport:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run local MCP server
uvx av-mcp YOUR_API_KEY
```

Then configure your client to use stdio instead of HTTP.

## Next Steps

1. ✅ **Test the setup**: Run the test script
2. ✅ **Configure categories**: Restrict to only needed tool categories
3. ✅ **Monitor usage**: Check statistics regularly
4. ✅ **Implement caching**: Adjust cache TTL based on your needs
5. ✅ **Scale up**: Upgrade API tier if needed for production

## References

- [Alpha Vantage MCP Documentation](https://mcp.alphavantage.co/)
- [MCP Specification](https://modelcontextprotocol.io/specification)
- [OpenAI Agents SDK MCP Guide](https://openai.github.io/openai-agents-python/mcp/)

