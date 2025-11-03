#!/usr/bin/env python3
"""CLI entry point for TradingAgents API server."""

import os
import sys
import socket
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def is_port_in_use(host: str, port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

def find_free_port(start_port: int, max_attempts: int = 10) -> int:
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if not is_port_in_use("0.0.0.0", port):
            return port
    raise RuntimeError(f"Could not find a free port after {max_attempts} attempts")

if __name__ == "__main__":
    host = os.getenv("TRADINGAGENTS_HOST", "0.0.0.0")
    default_port = int(os.getenv("TRADINGAGENTS_PORT", 8000))
    debug = os.getenv("TRADINGAGENTS_DEBUG", "false").lower() == "true"
    
    # Check if port is in use and find alternative if needed
    port = default_port
    if is_port_in_use(host, port):
        print(f"⚠️  Port {port} is already in use. Finding alternative port...")
        try:
            port = find_free_port(default_port + 1)
            print(f"✅ Using port {port} instead")
        except RuntimeError as e:
            print(f"❌ Error: {e}")
            print(f"\nTo free up port {default_port}, run:")
            print(f"  lsof -ti:{default_port} | xargs kill -9")
            sys.exit(1)
    
    print(f"Starting TradingAgents API server on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"API docs available at: http://{host}:{port}/docs")
    print(f"Health check: http://{host}:{port}/api/v1/health")
    
    uvicorn.run(
        "tradingagents.api.server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

