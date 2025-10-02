"""
Custom MCP client for Alpha Vantage that works around the compatibility issues.
Based on the test results, we know the server works with proper JSON-RPC requests.
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class AlphaVantageMCPClient:
    """Custom MCP client for Alpha Vantage that bypasses the official client library issues."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = f"https://mcp.alphavantage.co/mcp?apikey={api_key}"
        self.session_id = None
        self.protocol_version = None
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def initialize(self):
        """Initialize the MCP connection."""
        try:
            # Send MCP initialization request
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
                self.url,
                json=init_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "result" in data:
                        self.protocol_version = data["result"].get("protocolVersion")
                        logger.info(f"✅ MCP initialized successfully with protocol version: {self.protocol_version}")
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
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            async with self.session.post(
                self.url,
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
                        logger.info(f"✅ Retrieved {len(tools)} tools from MCP server")
                        return tools
                    else:
                        logger.error(f"❌ Failed to get tools: {data}")
                        return []
                else:
                    logger.error(f"❌ HTTP error getting tools: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Error listing tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                }
            }
            
            async with self.session.post(
                self.url,
                json=request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if "result" in data:
                        logger.info(f"✅ Tool {tool_name} called successfully")
                        return data["result"]
                    else:
                        logger.error(f"❌ Tool call failed: {data}")
                        return {"error": data.get("error", "Unknown error")}
                else:
                    logger.error(f"❌ HTTP error calling tool: {response.status}")
                    return {"error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"❌ Error calling tool {tool_name}: {e}")
            return {"error": str(e)}

async def test_alpha_vantage_mcp_client():
    """Test the custom Alpha Vantage MCP client."""
    print("🧪 Testing Custom Alpha Vantage MCP Client")
    print("=" * 50)
    
    api_key = "TQS06EXKTHWU639G"  # Use the API key from your .env
    
    async with AlphaVantageMCPClient(api_key) as client:
        # Test listing tools
        print("🔄 Listing tools...")
        tools = await client.list_tools()
        print(f"📊 Found {len(tools)} tools")
        
        # Show first few tools
        for i, tool in enumerate(tools[:5]):
            print(f"  {i+1}. {tool['name']}: {tool['description'][:100]}...")
        
        # Test calling a tool
        print("\n🔄 Testing tool call...")
        result = await client.call_tool("TIME_SERIES_DAILY", {
            "symbol": "AAPL",
            "outputsize": "compact"
        })
        
        if "error" not in result:
            print("✅ Tool call successful!")
            print(f"📊 Result keys: {list(result.keys())}")
        else:
            print(f"❌ Tool call failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_alpha_vantage_mcp_client())
