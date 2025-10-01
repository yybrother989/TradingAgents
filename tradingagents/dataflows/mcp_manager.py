"""MCP Server Manager for Alpha Vantage integration in TradingAgents."""

import json
import os
from contextlib import AsyncExitStack
from typing import List, Dict, Optional, Union, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
import logging

# Create a logger for this module
logger = logging.getLogger("mcp_manager")

try:
    import json5
except ImportError:
    json5 = None


class MCPServerConfig:
    """Configuration for a single MCP server."""
    
    def __init__(self, name: str, server_type: str, **kwargs):
        self.name = name
        self.server_type = server_type
        
        if server_type == "stdio":
            self.command = kwargs.get("command")
            self.args = kwargs.get("args", [])
        elif server_type == "http":
            self.url = kwargs.get("url")
        else:
            raise ValueError(f"Unsupported server type: {server_type}")


class TradingAgentsMCPManager:
    """Manages MCP server connections for TradingAgents."""
    
    def __init__(self, config_path: str = None):
        self.sessions: Dict[str, ClientSession] = {}
        self.configs: Dict[str, MCPServerConfig] = {}
        self._context_managers: Dict[str, Any] = {}
        self._initialized = False
        self._exit_stack = AsyncExitStack()
        
        # Default config path
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "mcp_config.json")
        self.config_path = config_path
        
        # Load configuration from file
        self._load_config()
    
    async def ensure_initialized(self):
        """Ensure servers are initialized."""
        if not self._initialized:
            await self.initialize_servers()
            self._initialized = True
    
    def _load_config(self):
        """Load MCP server configuration from JSON file."""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"Config file not found: {self.config_path}")
                # Create default config
                self._create_default_config()
                return
                
            with open(self.config_path, 'r') as f:
                if json5:
                    config_data = json5.load(f)
                else:
                    config_data = json.load(f)
            
            servers = config_data.get("servers", {})
            for name, server_config in servers.items():
                try:
                    config = MCPServerConfig(name=name, server_type=server_config['type'], **server_config)
                    self.add_server_config(config)
                    logger.info(f"Loaded configuration for server: {name}")
                except Exception as e:
                    logger.error(f"Failed to load config for server {name}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to load config file {self.config_path}: {e}")
            # Create default config
            self._create_default_config()
    
    def _create_default_config(self):
        """Create a default MCP configuration file."""
        default_config = {
            "servers": {
                "alphavantage": {
                    "type": "http",
                    "url": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
                }
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default MCP config at {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
    
    def add_server_config(self, config: MCPServerConfig):
        """Add a server configuration."""
        self.configs[config.name] = config
    
    async def initialize_servers(self) -> List[ClientSession]:
        """Initialize all configured MCP servers."""
        sessions = []
        
        for name, config in self.configs.items():
            try:
                logger.info(f"Initializing MCP server: {name}")
                
                if config.server_type == "stdio":
                    params = StdioServerParameters(
                        command=config.command,
                        args=config.args
                    )
                    session = await stdio_client(params)
                elif config.server_type == "http":
                    # sse_client returns an async context manager, we need to use it properly
                    # Store the context manager and enter it
                    context_manager = sse_client(config.url)
                    session = await context_manager.__aenter__()
                    # Store the context manager for cleanup later
                    self._context_managers[name] = context_manager
                else:
                    logger.error(f"Unsupported server type for {name}: {config.server_type}")
                    continue
                
                self.sessions[name] = session
                sessions.append(session)
                
                logger.info(f"Successfully initialized MCP server: {name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize MCP server {name}: {e}")
                # If external server fails, use mock session
                if name == "alphavantage":
                    logger.info("Falling back to mock MCP session for alphavantage")
                    from .mock_mcp_session import MockMCPSession
                    session = MockMCPSession()
                    self.sessions[name] = session
                    sessions.append(session)
                    logger.info("Successfully initialized mock MCP session for alphavantage")
                else:
                    raise
        
        return sessions
    
    def get_session(self, name: str) -> Optional[ClientSession]:
        """Get a specific server session by name."""
        return self.sessions.get(name)
    
    def get_all_sessions(self) -> Dict[str, ClientSession]:
        """Get all server sessions."""
        return self.sessions.copy()
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a tool on a specific MCP server."""
        if not self._initialized:
            await self.ensure_initialized()
        
        session = self.get_session(server_name)
        if not session:
            raise ValueError(f"Server '{server_name}' not found")
        
        try:
            # Check if it's a mock session
            if hasattr(session, 'tools'):
                # Mock session - call directly
                result = await session.call_tool(tool_name, arguments or {})
                return result
            else:
                # Real MCP session - list tools first
                tools = await session.list_tools()
                logger.debug(f"Available tools for {server_name}: {[tool.name for tool in tools.tools]}")
                
                # Call the tool
                result = await session.call_tool(tool_name, arguments or {})
                return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on server {server_name}: {e}")
            raise
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.ensure_initialized()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Close all sessions
        for name, session in self.sessions.items():
            try:
                await session.close()
                logger.info(f"Closed MCP server session: {name}")
            except Exception as e:
                logger.error(f"Error closing session {name}: {e}")
        
        self.sessions.clear()


# Global MCP manager instance
_mcp_manager: Optional[TradingAgentsMCPManager] = None


def get_mcp_manager() -> TradingAgentsMCPManager:
    """Get the global MCP manager instance."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = TradingAgentsMCPManager()
    return _mcp_manager


async def call_alpha_vantage_tool(tool_name: str, arguments: Dict[str, Any] = None) -> Any:
    """Convenience function to call Alpha Vantage MCP tools."""
    manager = get_mcp_manager()
    return await manager.call_tool("alphavantage", tool_name, arguments)
