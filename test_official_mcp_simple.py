#!/usr/bin/env python3
"""Simple test for Official MCP integration without MCP server dependency."""

import asyncio
import os
from dotenv import load_dotenv
from tradingagents.agents.analysts.market_analyst_official import create_market_analyst_official
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

def test_official_mcp_simple():
    """Test the official MCP integration without MCP server."""
    
    print("🧪 Testing Official MCP Integration (Simple)...")
    
    # Check API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not found!")
        return False
    
    print("✅ API keys found")
    
    # Initialize LLM
    llm = ChatOpenAI(model='gpt-4o-mini')
    
    # Create market analyst
    analyst = create_market_analyst_official(llm)
    
    # Test state
    state = {
        'company_of_interest': 'AAPL',
        'trade_date': '2024-01-15',
        'messages': []
    }
    
    print("🔄 Running market analysis...")
    
    try:
        # Run analysis
        result = analyst(state)
        
        print("✅ Analysis completed!")
        print(f"📊 Market report length: {len(result.get('market_report', ''))} characters")
        print(f"💬 Messages: {len(result.get('messages', []))}")
        
        # Show first 200 characters of the report
        report = result.get('market_report', '')
        if report:
            print(f"\n📝 Report preview:\n{report[:200]}...")
        else:
            print("\n⚠️ No report generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Official MCP Integration Test (Simple)")
    print("=" * 50)
    
    success = test_official_mcp_simple()
    
    if success:
        print("\n🎉 Official MCP integration test PASSED!")
    else:
        print("\n💥 Official MCP integration test FAILED!")
    
    return success

if __name__ == "__main__":
    main()
