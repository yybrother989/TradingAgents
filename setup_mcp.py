#!/usr/bin/env python3
"""Setup script for Alpha Vantage MCP integration in TradingAgents."""

import os
import json
import sys
from pathlib import Path


def setup_alpha_vantage_mcp():
    """Setup Alpha Vantage MCP configuration."""
    print("🔧 Setting up Alpha Vantage MCP integration for TradingAgents...")
    
    # Get Alpha Vantage API key
    api_key = input("Enter your Alpha Vantage API key (get one free at https://www.alphavantage.co/support/#api-key): ").strip()
    
    if not api_key:
        print("❌ API key is required. Exiting.")
        sys.exit(1)
    
    # Update MCP configuration
    mcp_config_path = Path("tradingagents/dataflows/mcp_config.json")
    
    try:
        with open(mcp_config_path, 'r') as f:
            config = json.load(f)
        
        # Update the API key
        config["servers"]["alphavantage"]["url"] = f"https://mcp.alphavantage.co/mcp?apikey={api_key}"
        
        with open(mcp_config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Updated MCP configuration at {mcp_config_path}")
        
    except Exception as e:
        print(f"❌ Error updating MCP configuration: {e}")
        sys.exit(1)
    
    # Check if we should update default config
    update_default = input("Do you want to set alpha_vantage_mcp as the default vendor? (y/n): ").strip().lower()
    
    if update_default == 'y':
        try:
            config_path = Path("tradingagents/default_config.py")
            
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Update the default vendors to use MCP
            content = content.replace('"core_stock_apis": "alpha_vantage",', '"core_stock_apis": "alpha_vantage_mcp",')
            content = content.replace('"technical_indicators": "alpha_vantage",', '"technical_indicators": "alpha_vantage_mcp",')
            content = content.replace('"fundamental_data": "alpha_vantage",', '"fundamental_data": "alpha_vantage_mcp",')
            content = content.replace('"news_data": "alpha_vantage",', '"news_data": "alpha_vantage_mcp",')
            
            with open(config_path, 'w') as f:
                f.write(content)
            
            print("✅ Updated default configuration to use Alpha Vantage MCP")
            
        except Exception as e:
            print(f"❌ Error updating default configuration: {e}")
    
    print("\n🎉 Setup complete! Alpha Vantage MCP integration is ready.")
    print("\nTo test the integration, run:")
    print("  python -c \"from tradingagents.dataflows.alpha_vantage_mcp import get_stock_data_mcp_sync; print(get_stock_data_mcp_sync('AAPL', '2024-01-01', '2024-01-31'))\"")


if __name__ == "__main__":
    setup_alpha_vantage_mcp()
