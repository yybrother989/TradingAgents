"""
Production-ready MCP Server Manager for TradingAgents.
Follows MCP best practices: HTTP transport, category filtering, caching, rate limiting, and observability.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from functools import lru_cache
import aiohttp
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    url: str
    api_key: str
    categories: Optional[List[str]] = None  # Principle of least privilege - restrict tool categories
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_calls: int = 25  # Alpha Vantage free tier: 25 calls/day
    rate_limit_window: int = 86400  # 24 hours in seconds
    
    def get_url_with_params(self) -> str:
        """Get URL with query parameters (API key and optional categories)."""
        url = self.url
        if "?" in url:
            url += f"&apikey={self.api_key}"
        else:
            url += f"?apikey={self.api_key}"
        
        if self.categories:
            # Add category filtering for principle of least privilege
            categories_param = ",".join(self.categories)
            url += f"&categories={categories_param}"
        
        return url


@dataclass
class RateLimiter:
    """Simple rate limiter for MCP tool calls."""
    max_calls: int
    window_seconds: int
    calls: List[float] = field(default_factory=list)
    
    def can_call(self) -> bool:
        """Check if a call is allowed."""
        now = time.time()
        # Remove calls outside the time window
        self.calls = [t for t in self.calls if now - t < self.window_seconds]
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a call."""
        self.calls.append(time.time())
    
    def wait_time(self) -> float:
        """Get time to wait before next call is allowed."""
        if not self.calls:
            return 0.0
        
        oldest_call = min(self.calls)
        elapsed = time.time() - oldest_call
        remaining = self.window_seconds - elapsed
        
        return max(0.0, remaining)


class ProductionMCPServerManager:
    """
    Production-ready MCP Server Manager with:
    - HTTP transport (recommended for production)
    - Category filtering (principle of least privilege)
    - Rate limiting and caching
    - Error handling with retries
    - Observability/logging
    """
    
    def __init__(self, config: Optional[MCPServerConfig] = None):
        """Initialize the MCP server manager."""
        if config is None:
            config = self._load_config_from_env()
        
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(
            max_calls=config.rate_limit_calls,
            window_seconds=config.rate_limit_window
        )
        self._tool_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        
        # Observability: Track call statistics
        self.stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "cached_calls": 0,
            "rate_limited_calls": 0,
        }
    
    @staticmethod
    def _load_config_from_env() -> MCPServerConfig:
        """Load configuration from environment variables."""
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            # Fallback to default demo key (should be replaced)
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'TQS06EXKTHWU639G')
            logger.warning("Using default API key. Set ALPHA_VANTAGE_API_KEY env var for production.")
        
        # Base URL
        base_url = os.getenv('ALPHA_VANTAGE_MCP_URL', 'https://mcp.alphavantage.co/mcp')
        
        # Category filtering (principle of least privilege)
        categories_str = os.getenv('ALPHA_VANTAGE_MCP_CATEGORIES')
        categories = categories_str.split(',') if categories_str else None
        
        # Rate limiting (Alpha Vantage free tier: 25 calls/day)
        rate_limit_calls = int(os.getenv('ALPHA_VANTAGE_RATE_LIMIT_CALLS', '25'))
        rate_limit_window = int(os.getenv('ALPHA_VANTAGE_RATE_LIMIT_WINDOW', '86400'))  # 24 hours
        
        return MCPServerConfig(
            name="alphavantage",
            url=base_url,
            api_key=api_key,
            categories=categories,
            rate_limit_calls=rate_limit_calls,
            rate_limit_window=rate_limit_window
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def ensure_session(self):
        """Ensure HTTP session is initialized."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def initialize(self) -> bool:
        """Initialize MCP connection (send initialize request)."""
        await self.ensure_session()
        
        try:
            url = self.config.get_url_with_params()
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "tradingagents",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with self.session.post(
                url,
                json=init_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "result" in data:
                        protocol_version = data["result"].get("protocolVersion")
                        logger.info(f"✅ MCP initialized successfully with protocol version: {protocol_version}")
                        return True
                    else:
                        logger.error(f"❌ MCP initialization failed: {data}")
                        return False
                else:
                    logger.error(f"❌ HTTP error during initialization: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ MCP initialization error: {e}")
            return False
    
    async def list_tools(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """List available tools from MCP server (with caching)."""
        cache_key = "tools_list"
        
        # Check cache
        if use_cache and cache_key in self._tool_cache:
            cached = self._tool_cache[cache_key]
            if time.time() - cached["timestamp"] < self._cache_ttl:
                logger.debug("Returning cached tools list")
                self.stats["cached_calls"] += 1
                return cached["data"]
        
        await self.ensure_session()
        
        try:
            url = self.config.get_url_with_params()
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            async with self.session.post(
                url,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "result" in data and "tools" in data["result"]:
                        tools = data["result"]["tools"]
                        
                        # Cache the result
                        self._tool_cache[cache_key] = {
                            "data": tools,
                            "timestamp": time.time()
                        }
                        
                        logger.info(f"✅ Retrieved {len(tools)} tools from MCP server")
                        self.stats["successful_calls"] += 1
                        return tools
                    else:
                        logger.error(f"❌ Failed to get tools: {data}")
                        self.stats["failed_calls"] += 1
                        return []
                else:
                    logger.error(f"❌ HTTP error getting tools: {response.status}")
                    self.stats["failed_calls"] += 1
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error listing tools: {e}")
            self.stats["failed_calls"] += 1
            return []
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call a tool on the MCP server with:
        - Rate limiting
        - Retry logic
        - Caching
        - Error handling
        """
        await self.ensure_session()
        
        # Check rate limit
        if not self.rate_limiter.can_call():
            wait_time = self.rate_limiter.wait_time()
            logger.warning(f"⏳ Rate limit reached. Waiting {wait_time:.1f}s before next call.")
            self.stats["rate_limited_calls"] += 1
            await asyncio.sleep(wait_time)
        
        # Check cache (for idempotent tool calls)
        if use_cache and arguments:
            cache_key = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
            if cache_key in self._tool_cache:
                cached = self._tool_cache[cache_key]
                ttl = cache_ttl or self._cache_ttl
                if time.time() - cached["timestamp"] < ttl:
                    logger.debug(f"Returning cached result for {tool_name}")
                    self.stats["cached_calls"] += 1
                    return cached["data"]
        
        # Execute with retries
        url = self.config.get_url_with_params()
        arguments = arguments or {}
        
        for attempt in range(self.config.max_retries):
            try:
                self.stats["total_calls"] += 1
                self.rate_limiter.record_call()
                
                request = {
                    "jsonrpc": "2.0",
                    "id": 3 + attempt,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    }
                }
                
                # Log the request for observability
                logger.debug(f"Calling MCP tool: {tool_name} with args: {arguments}")
                
                async with self.session.post(
                    url,
                    json=request,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "result" in data:
                            result = data["result"]
                            
                            # Cache successful results
                            if use_cache and arguments:
                                cache_key = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
                                self._tool_cache[cache_key] = {
                                    "data": result,
                                    "timestamp": time.time()
                                }
                            
                            logger.info(f"✅ Tool {tool_name} called successfully")
                            self.stats["successful_calls"] += 1
                            return result
                        else:
                            error = data.get("error", {})
                            error_msg = error.get("message", "Unknown error")
                            logger.error(f"❌ Tool call failed: {error_msg}")
                            
                            # Don't retry on client errors (4xx)
                            if error.get("code") and 400 <= error.get("code") < 500:
                                self.stats["failed_calls"] += 1
                                return {"error": error_msg}
                            
                            # Retry on server errors (5xx)
                            if attempt < self.config.max_retries - 1:
                                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                                continue
                            
                            self.stats["failed_calls"] += 1
                            return {"error": error_msg}
                    else:
                        # HTTP error - retry on 5xx
                        if 500 <= response.status < 600 and attempt < self.config.max_retries - 1:
                            logger.warning(f"⚠️ HTTP {response.status}, retrying ({attempt + 1}/{self.config.max_retries})...")
                            await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                            continue
                        
                        logger.error(f"❌ HTTP error calling tool: {response.status}")
                        self.stats["failed_calls"] += 1
                        return {"error": f"HTTP {response.status}"}
                        
            except aiohttp.ClientError as e:
                # Network error - retry
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"⚠️ Network error, retrying ({attempt + 1}/{self.config.max_retries}): {e}")
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    continue
                
                logger.error(f"❌ Error calling tool {tool_name}: {e}")
                self.stats["failed_calls"] += 1
                return {"error": str(e)}
            
            except Exception as e:
                logger.error(f"❌ Unexpected error calling tool {tool_name}: {e}")
                self.stats["failed_calls"] += 1
                return {"error": str(e)}
        
        return {"error": "Max retries exceeded"}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get observability statistics."""
        return {
            **self.stats,
            "cache_size": len(self._tool_cache),
            "rate_limit_status": {
                "calls_remaining": max(0, self.rate_limiter.max_calls - len(self.rate_limiter.calls)),
                "calls_in_window": len(self.rate_limiter.calls),
                "wait_time": self.rate_limiter.wait_time()
            }
        }
    
    def clear_cache(self):
        """Clear the tool cache."""
        self._tool_cache.clear()
        logger.info("Cache cleared")


# Global instance
_mcp_manager: Optional[ProductionMCPServerManager] = None


def get_mcp_manager(config: Optional[MCPServerConfig] = None) -> ProductionMCPServerManager:
    """Get the global MCP manager instance."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = ProductionMCPServerManager(config)
    return _mcp_manager


async def test_mcp_server():
    """Test the production MCP server setup."""
    print("🧪 Testing Production MCP Server Setup")
    print("=" * 60)
    
    # Load config from environment
    manager = get_mcp_manager()
    
    async with manager:
        # Initialize
        print("\n1️⃣ Initializing MCP connection...")
        if await manager.initialize():
            print("✅ MCP initialized successfully")
        else:
            print("❌ MCP initialization failed")
            return
        
        # List tools
        print("\n2️⃣ Listing available tools...")
        tools = await manager.list_tools()
        print(f"✅ Found {len(tools)} tools")
        
        if tools:
            print("\n📋 Sample tools:")
            for tool in tools[:5]:
                print(f"  - {tool['name']}: {tool['description'][:80]}...")
        
        # Test tool call
        print("\n3️⃣ Testing tool call (TIME_SERIES_DAILY)...")
        result = await manager.call_tool("TIME_SERIES_DAILY", {
            "symbol": "AAPL",
            "outputsize": "compact"
        })
        
        if "error" not in result:
            print("✅ Tool call successful!")
            if isinstance(result, dict):
                print(f"📊 Result keys: {list(result.keys())[:10]}")
        else:
            print(f"❌ Tool call failed: {result.get('error')}")
        
        # Show statistics
        print("\n4️⃣ Statistics:")
        stats = manager.get_stats()
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())

