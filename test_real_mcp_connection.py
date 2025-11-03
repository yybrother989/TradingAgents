#!/usr/bin/env python3
"""
Test script to experiment with real Alpha Vantage MCP server connection.
This will help us understand the exact protocol requirements and fix connection issues.
"""

import asyncio
import json
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_direct_http_connection():
    """Test direct HTTP connection to Alpha Vantage MCP server."""
    import aiohttp
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'TQS06EXKTHWU639G')
    url = f"https://mcp.alphavantage.co/mcp?apikey={api_key}"
    
    print(f"🔗 Testing direct HTTP connection to: {url}")
    
    # Test 1: Simple GET request
    print("\n📡 Test 1: Simple GET request")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                text = await response.text()
                print(f"Response: {text[:200]}...")
        except Exception as e:
            print(f"❌ GET request failed: {e}")
    
    # Test 2: POST request with JSON-RPC
    print("\n📡 Test 2: POST request with JSON-RPC")
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                url,
                json=jsonrpc_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            ) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                text = await response.text()
                print(f"Response: {text[:500]}...")
        except Exception as e:
            print(f"❌ POST request failed: {e}")

async def test_mcp_client_library():
    """Test using the official MCP client library."""
    print("\n🔧 Test 3: Using official MCP client library")
    
    try:
        from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
        
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'TQS06EXKTHWU639G')
        url = f"https://mcp.alphavantage.co/mcp?apikey={api_key}"
        
        print(f"🔗 Creating MCP server with URL: {url}")
        
        # Create server parameters
        params = MCPServerStreamableHttpParams(
            url=url,
            timeout=15.0,
            sse_read_timeout=30.0
        )
        
        # Create server
        server = MCPServerStreamableHttp(params, client_session_timeout_seconds=30.0)
        
        print("✅ MCP server created successfully")
        
        # Try to start the server
        print("🔄 Starting MCP server...")
        async with server:
            print("✅ MCP server started successfully")
            
            # Try to get tools
            print("🔄 Listing tools...")
            try:
                # This might not work directly, but let's see what happens
                print("✅ Server context entered successfully")
            except Exception as e:
                print(f"❌ Error in server context: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ MCP client library test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_mcp_with_manual_handshake():
    """Test MCP connection with manual handshake."""
    print("\n🤝 Test 4: Manual MCP handshake")
    
    import aiohttp
    
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'TQS06EXKTHWU639G')
    url = f"https://mcp.alphavantage.co/mcp?apikey={api_key}"
    
    # MCP initialization request
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
                "name": "tradingagents-test",
                "version": "1.0.0"
            }
        }
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            print("🔄 Sending MCP initialization request...")
            async with session.post(
                url,
                json=init_request,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            ) as response:
                print(f"Status: {response.status}")
                text = await response.text()
                print(f"Response: {text}")
                
                if response.status == 200:
                    data = json.loads(text)
                    if "result" in data:
                        print("✅ MCP initialization successful!")
                        print(f"Server capabilities: {data['result'].get('capabilities', {})}")
                    else:
                        print(f"❌ MCP initialization failed: {data}")
                else:
                    print(f"❌ HTTP error: {response.status}")
                    
        except Exception as e:
            print(f"❌ Manual handshake failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Run all tests."""
    print("🧪 Alpha Vantage MCP Server Connection Tests")
    print("=" * 50)
    
    # Test 1: Direct HTTP connection
    await test_direct_http_connection()
    
    # Test 2: MCP client library
    await test_mcp_client_library()
    
    # Test 3: Manual MCP handshake
    await test_mcp_with_manual_handshake()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
