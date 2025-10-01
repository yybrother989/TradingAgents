"""Official MCP Server Manager for TradingAgents based on Alpha Vantage MCP example."""

import json
import os
from contextlib import AsyncExitStack
from typing import List, Dict, Optional, Union
from agents.mcp import MCPServerStdio, MCPServerStdioParams, MCPServerStreamableHttp, MCPServerStreamableHttpParams
import logging

# Create a logger for this module
logger = logging.getLogger("official_mcp_manager")

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


class OfficialMCPServerManager:
    """Official MCP Server Manager based on Alpha Vantage MCP example."""
    
    def __init__(self, config_path: str = "mcp.json"):
        self.servers: Dict[str, Union[MCPServerStdio, MCPServerStreamableHttp]] = {}
        self.configs: Dict[str, MCPServerConfig] = {}
        self._initialized = False
        self._exit_stack = AsyncExitStack()
        
        # Load config from the same directory as this file
        if not os.path.isabs(config_path):
            config_path = os.path.join(os.path.dirname(__file__), config_path)
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
    
    def add_server_config(self, config: MCPServerConfig):
        """Add a server configuration."""
        self.configs[config.name] = config
    
    async def initialize_servers(self) -> List[Union[MCPServerStdio, MCPServerStreamableHttp]]:
        """Initialize all configured MCP servers."""
        servers = []
        
        for name, config in self.configs.items():
            try:
                logger.info(f"Initializing MCP server: {name}")
                
                if config.server_type == "stdio":
                    params = MCPServerStdioParams(
                        command=config.command,
                        args=config.args
                    )
                    server = MCPServerStdio(params, client_session_timeout_seconds=30.0)
                elif config.server_type == "http":
                    params = MCPServerStreamableHttpParams(
                        url=config.url,
                        timeout=15.0,
                        sse_read_timeout=30.0
                    )
                    server = MCPServerStreamableHttp(params, client_session_timeout_seconds=30.0)
                else:
                    logger.error(f"Unsupported server type for {name}: {config.server_type}")
                    continue
                
                self.servers[name] = server
                servers.append(server)
                
                logger.info(f"Successfully initialized MCP server: {name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize MCP server {name}: {e}")
                raise
        
        return servers
    
    def get_servers(self) -> List[Union[MCPServerStdio, MCPServerStreamableHttp]]:
        """Get list of all initialized servers."""
        return list(self.servers.values())
    
    def get_server(self, name: str) -> Optional[Union[MCPServerStdio, MCPServerStreamableHttp]]:
        """Get a specific server by name."""
        return self.servers.get(name)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.ensure_initialized()
        
        # Start servers using exit stack for proper cleanup
        for name, server in self.servers.items():
            logger.info(f"Starting MCP server: {name}")
            try:
                await self._exit_stack.enter_async_context(server)
            except Exception as e:
                logger.error(f"Failed to start server {name}: {e}")
                # Exit stack will clean up any servers that were started
                await self._exit_stack.aclose()
                raise
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # This closes servers in LIFO order in the SAME task that entered them
        try:
            await self._exit_stack.aclose()
        finally:
            self.servers.clear()


# Global instance for easy access
_official_mcp_manager = None

def get_official_mcp_manager(config_path: str = None) -> OfficialMCPServerManager:
    """Get the global MCP manager instance."""
    global _official_mcp_manager
    if _official_mcp_manager is None:
        config_path = config_path or os.path.join(os.path.dirname(__file__), "mcp_config.json")
        _official_mcp_manager = OfficialMCPServerManager(config_path)
    return _official_mcp_manager
