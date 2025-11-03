#!/usr/bin/env python3
"""Setup script for Official MCP integration with Alpha Vantage."""

import os
import json
from pathlib import Path


def setup_official_mcp():
    """Setup official MCP configuration."""
    
    print("🚀 Setting up Official MCP integration with Alpha Vantage...")
    
    # Get Alpha Vantage API key
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("❌ ALPHA_VANTAGE_API_KEY environment variable not found!")
        print("Please set your Alpha Vantage API key:")
        print("export ALPHA_VANTAGE_API_KEY=your_api_key_here")
        return False
    
    # Create MCP configuration
    mcp_config = {
        "servers": {
            "alphavantage": {
                "type": "http",
                "url": f"https://mcp.alphavantage.co/mcp?apikey={api_key}"
            }
        }
    }
    
    # Write configuration file
    config_path = Path("tradingagents/dataflows/mcp.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(mcp_config, f, indent=2)
    
    print(f"✅ MCP configuration saved to: {config_path}")
    print("🎉 Official MCP integration setup complete!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Test the integration: python test_official_mcp.py")
    
    return True


if __name__ == "__main__":
    setup_official_mcp()
