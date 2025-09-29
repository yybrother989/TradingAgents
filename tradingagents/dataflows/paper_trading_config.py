"""
Paper Trading Configuration
=========================

Configuration settings for paper trading integration with trading agents.
This module contains all the necessary configuration options for setting up
and customizing the paper trading system.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PaperTradingConfig:
    """Configuration class for paper trading settings"""
    
    # API Configuration
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    alpaca_paper_trading: bool = True
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    
    # Portfolio Configuration
    initial_capital: float = 100000.0
    max_position_size: float = 0.1  # 10% of portfolio per position
    max_daily_trades_per_agent: int = 10
    max_agents_per_symbol: int = 3
    
    # Risk Management
    stop_loss_percentage: float = 0.05  # 5% stop loss
    take_profit_percentage: float = 0.15  # 15% take profit
    max_drawdown_percentage: float = 0.20  # 20% max drawdown
    agent_confidence_threshold: float = 0.6  # Minimum confidence to execute trades
    
    # Trading Settings
    commission_per_trade: float = 0.0  # Commission-free trading
    slippage_percentage: float = 0.001  # 0.1% slippage simulation
    min_trade_amount: float = 100.0  # Minimum $100 per trade
    
    # Logging and Reporting
    log_level: str = "INFO"
    log_retention_days: int = 30
    generate_daily_reports: bool = True
    generate_weekly_reports: bool = True
    generate_monthly_reports: bool = True
    
    # Data Storage
    data_directory: str = "data/paper_trading"
    trades_log_file: str = "trades.json"
    performance_log_file: str = "performance.json"
    reports_directory: str = "reports"
    
    # Market Hours (EST/EDT)
    market_open_hour: int = 9
    market_open_minute: int = 30
    market_close_hour: int = 16
    market_close_minute: int = 0
    
    # Agent-specific settings
    agent_settings: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize default values after object creation"""
        if self.agent_settings is None:
            self.agent_settings = {
                "BullResearcher": {
                    "max_position_size": 0.15,
                    "confidence_threshold": 0.7,
                    "risk_tolerance": "moderate"
                },
                "BearResearcher": {
                    "max_position_size": 0.12,
                    "confidence_threshold": 0.8,
                    "risk_tolerance": "conservative"
                },
                "MarketAnalyst": {
                    "max_position_size": 0.10,
                    "confidence_threshold": 0.6,
                    "risk_tolerance": "moderate"
                },
                "NewsAnalyst": {
                    "max_position_size": 0.08,
                    "confidence_threshold": 0.75,
                    "risk_tolerance": "aggressive"
                },
                "FundamentalsAnalyst": {
                    "max_position_size": 0.20,
                    "confidence_threshold": 0.65,
                    "risk_tolerance": "conservative"
                },
                "Trader": {
                    "max_position_size": 0.25,
                    "confidence_threshold": 0.5,
                    "risk_tolerance": "aggressive"
                }
            }
        
        # Set API keys from environment if not provided
        if self.alpaca_api_key is None:
            self.alpaca_api_key = os.getenv('ALPACA_API_KEY')
        if self.alpaca_secret_key is None:
            self.alpaca_secret_key = os.getenv('ALPACA_SECRET_KEY')


def get_paper_trading_config(config_file: Optional[str] = None) -> PaperTradingConfig:
    """
    Get paper trading configuration
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        PaperTradingConfig instance
    """
    if config_file and os.path.exists(config_file):
        # Load from file (implement JSON/YAML loading if needed)
        pass
    
    return PaperTradingConfig()


def validate_config(config: PaperTradingConfig) -> bool:
    """
    Validate paper trading configuration
    
    Args:
        config: Configuration to validate
        
    Returns:
        True if valid, False otherwise
    """
    errors = []
    
    # Check API credentials
    if not config.alpaca_api_key:
        errors.append("Alpaca API key is required")
    if not config.alpaca_secret_key:
        errors.append("Alpaca secret key is required")
    
    # Check portfolio settings
    if config.initial_capital <= 0:
        errors.append("Initial capital must be positive")
    if not 0 < config.max_position_size <= 1:
        errors.append("Max position size must be between 0 and 1")
    if config.max_daily_trades_per_agent <= 0:
        errors.append("Max daily trades per agent must be positive")
    
    # Check risk management
    if not 0 < config.stop_loss_percentage < 1:
        errors.append("Stop loss percentage must be between 0 and 1")
    if not 0 < config.take_profit_percentage < 1:
        errors.append("Take profit percentage must be between 0 and 1")
    if not 0 < config.max_drawdown_percentage < 1:
        errors.append("Max drawdown percentage must be between 0 and 1")
    if not 0 <= config.agent_confidence_threshold <= 1:
        errors.append("Agent confidence threshold must be between 0 and 1")
    
    # Check trading settings
    if config.commission_per_trade < 0:
        errors.append("Commission per trade cannot be negative")
    if config.slippage_percentage < 0:
        errors.append("Slippage percentage cannot be negative")
    if config.min_trade_amount <= 0:
        errors.append("Minimum trade amount must be positive")
    
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True


def create_sample_config_file(file_path: str = "paper_trading_config.json"):
    """
    Create a sample configuration file
    
    Args:
        file_path: Path where to create the configuration file
    """
    config = PaperTradingConfig()
    
    config_dict = {
        "api_configuration": {
            "alpaca_api_key": "YOUR_ALPACA_API_KEY_HERE",
            "alpaca_secret_key": "YOUR_ALPACA_SECRET_KEY_HERE",
            "alpaca_paper_trading": True,
            "alpaca_base_url": "https://paper-api.alpaca.markets"
        },
        "portfolio_configuration": {
            "initial_capital": 100000.0,
            "max_position_size": 0.1,
            "max_daily_trades_per_agent": 10,
            "max_agents_per_symbol": 3
        },
        "risk_management": {
            "stop_loss_percentage": 0.05,
            "take_profit_percentage": 0.15,
            "max_drawdown_percentage": 0.20,
            "agent_confidence_threshold": 0.6
        },
        "trading_settings": {
            "commission_per_trade": 0.0,
            "slippage_percentage": 0.001,
            "min_trade_amount": 100.0
        },
        "logging_and_reporting": {
            "log_level": "INFO",
            "log_retention_days": 30,
            "generate_daily_reports": True,
            "generate_weekly_reports": True,
            "generate_monthly_reports": True
        },
        "data_storage": {
            "data_directory": "data/paper_trading",
            "trades_log_file": "trades.json",
            "performance_log_file": "performance.json",
            "reports_directory": "reports"
        },
        "market_hours": {
            "market_open_hour": 9,
            "market_open_minute": 30,
            "market_close_hour": 16,
            "market_close_minute": 0
        },
        "agent_settings": config.agent_settings
    }
    
    import json
    with open(file_path, 'w') as f:
        json.dump(config_dict, f, indent=2)
    
    print(f"Sample configuration file created at: {file_path}")
    print("Please update the API keys and other settings as needed.")


# Environment variable setup instructions
ENVIRONMENT_SETUP_INSTRUCTIONS = """
# Paper Trading Environment Setup
# ===============================

# 1. Install required packages:
pip install alpaca-py

# 2. Set up environment variables:
export ALPACA_API_KEY="your_api_key_here"
export ALPACA_SECRET_KEY="your_secret_key_here"

# 3. For Windows users, use:
set ALPACA_API_KEY=your_api_key_here
set ALPACA_SECRET_KEY=your_secret_key_here

# 4. Or create a .env file in your project root:
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here

# 5. Get your API keys from:
# https://app.alpaca.markets/paper/dashboard/overview
"""


if __name__ == "__main__":
    # Create sample configuration file
    create_sample_config_file()
    print(ENVIRONMENT_SETUP_INSTRUCTIONS)
