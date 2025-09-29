"""
Paper Trading Integration for Trading Agents
==========================================

This module provides paper trading capabilities using Alpaca Markets API
to validate trading agent recommendations through forward testing.

Features:
- Real-time paper trading simulation
- Portfolio tracking and performance metrics
- Integration with existing trading agent system
- Risk management and position sizing
- Trade logging and reporting
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, StopOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass, OrderType
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
    from alpaca.common.exceptions import APIError
except ImportError:
    print("Alpaca-py not installed. Run: pip install alpaca-py")
    raise

from .config import get_config


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Trade:
    """Trade data structure"""
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: int
    price: float
    timestamp: datetime
    order_id: str
    status: OrderStatus
    commission: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class Position:
    """Position data structure"""
    symbol: str
    quantity: int
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float


@dataclass
class Portfolio:
    """Portfolio data structure"""
    total_value: float
    buying_power: float
    cash: float
    positions: List[Position]
    total_pnl: float
    day_pnl: float


class PaperTradingEngine:
    """
    Paper Trading Engine for validating trading agent recommendations
    
    This class handles:
    - Order execution simulation
    - Portfolio tracking
    - Performance metrics calculation
    - Risk management
    - Trade logging
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 secret_key: Optional[str] = None,
                 paper: bool = True,
                 initial_capital: float = 100000.0):
        """
        Initialize the paper trading engine
        
        Args:
            api_key: Alpaca API key (if None, will try to get from environment)
            secret_key: Alpaca secret key (if None, will try to get from environment)
            paper: Whether to use paper trading (True) or live trading (False)
            initial_capital: Starting capital for paper trading
        """
        self.paper = paper
        self.initial_capital = initial_capital
        
        # Get API credentials
        self.api_key = api_key or os.getenv('ALPACA_API_KEY')
        self.secret_key = secret_key or os.getenv('ALPACA_SECRET_KEY')
        
        if not self.api_key or not self.secret_key:
            raise ValueError("Alpaca API credentials not found. Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables.")
        
        # Initialize Alpaca clients
        self.trading_client = TradingClient(
            api_key=self.api_key,
            secret_key=self.secret_key,
            paper=paper
        )
        
        self.data_client = StockHistoricalDataClient(
            api_key=self.api_key,
            secret_key=self.secret_key
        )
        
        # Portfolio tracking
        self.portfolio = None
        self.trades: List[Trade] = []
        self.positions: Dict[str, Position] = {}
        
        # Risk management
        self.max_position_size = 0.1  # 10% of portfolio per position
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.take_profit_pct = 0.15  # 15% take profit
        
        # Logging
        self.setup_logging()
        
        # Initialize portfolio
        self._initialize_portfolio()
    
    def setup_logging(self):
        """Setup logging for paper trading"""
        log_dir = os.path.join(get_config()["data_dir"], "paper_trading_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"paper_trading_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('PaperTrading')
    
    def _initialize_portfolio(self):
        """Initialize portfolio with starting capital"""
        try:
            account = self.trading_client.get_account()
            self.portfolio = Portfolio(
                total_value=float(account.portfolio_value),
                buying_power=float(account.buying_power),
                cash=float(account.cash),
                positions=[],
                total_pnl=0.0,
                day_pnl=0.0
            )
            self.logger.info(f"Portfolio initialized with ${self.portfolio.total_value:,.2f}")
        except Exception as e:
            self.logger.error(f"Failed to initialize portfolio: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current market price
        """
        try:
            # Get latest bar data
            request_params = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=TimeFrame.Minute,
                start=datetime.now() - timedelta(minutes=5),
                end=datetime.now()
            )
            
            bars = self.data_client.get_stock_bars(request_params)
            
            if symbol in bars.data:
                latest_bar = bars.data[symbol][-1]
                return float(latest_bar.close)
            else:
                raise ValueError(f"No data found for symbol {symbol}")
                
        except Exception as e:
            self.logger.error(f"Failed to get current price for {symbol}: {e}")
            raise
    
    def execute_trade(self, 
                     symbol: str, 
                     side: str, 
                     quantity: int, 
                     order_type: str = "market",
                     limit_price: Optional[float] = None,
                     stop_price: Optional[float] = None) -> Trade:
        """
        Execute a paper trade
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            quantity: Number of shares
            order_type: 'market', 'limit', or 'stop'
            limit_price: Price for limit orders
            stop_price: Price for stop orders
            
        Returns:
            Trade object with execution details
        """
        try:
            # Validate order
            if not self._validate_order(symbol, side, quantity):
                raise ValueError("Order validation failed")
            
            # Get current price
            current_price = self.get_current_price(symbol)
            
            # Create order request
            if order_type == "market":
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY
                )
            elif order_type == "limit":
                if not limit_price:
                    raise ValueError("Limit price required for limit orders")
                order_request = LimitOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    limit_price=limit_price
                )
            elif order_type == "stop":
                if not stop_price:
                    raise ValueError("Stop price required for stop orders")
                order_request = StopOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                    stop_price=stop_price
                )
            else:
                raise ValueError(f"Unsupported order type: {order_type}")
            
            # Submit order
            order = self.trading_client.submit_order(order_request)
            
            # Create trade record
            trade = Trade(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=current_price,
                timestamp=datetime.now(),
                order_id=order.id,
                status=OrderStatus.PENDING
            )
            
            self.trades.append(trade)
            self.logger.info(f"Order submitted: {side.upper()} {quantity} {symbol} @ ${current_price:.2f}")
            
            return trade
            
        except Exception as e:
            self.logger.error(f"Failed to execute trade: {e}")
            raise
    
    def _validate_order(self, symbol: str, side: str, quantity: int) -> bool:
        """
        Validate order before execution
        
        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            quantity: Number of shares
            
        Returns:
            True if order is valid, False otherwise
        """
        try:
            # Check if we have enough buying power for buy orders
            if side == "buy":
                current_price = self.get_current_price(symbol)
                required_capital = current_price * quantity
                
                if required_capital > self.portfolio.buying_power:
                    self.logger.warning(f"Insufficient buying power. Required: ${required_capital:,.2f}, Available: ${self.portfolio.buying_power:,.2f}")
                    return False
            
            # Check position limits
            if side == "sell":
                current_position = self.positions.get(symbol, Position(symbol, 0, 0, 0, 0, 0))
                if current_position.quantity < quantity:
                    self.logger.warning(f"Insufficient shares to sell. Required: {quantity}, Available: {current_position.quantity}")
                    return False
            
            # Check position size limits
            current_price = self.get_current_price(symbol)
            position_value = current_price * quantity
            max_position_value = self.portfolio.total_value * self.max_position_size
            
            if position_value > max_position_value:
                self.logger.warning(f"Position size exceeds limit. Value: ${position_value:,.2f}, Max: ${max_position_value:,.2f}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Order validation failed: {e}")
            return False
    
    def update_portfolio(self):
        """Update portfolio with current market values"""
        try:
            account = self.trading_client.get_account()
            positions = self.trading_client.get_all_positions()
            
            # Update portfolio
            self.portfolio.total_value = float(account.portfolio_value)
            self.portfolio.buying_power = float(account.buying_power)
            self.portfolio.cash = float(account.cash)
            self.portfolio.total_pnl = float(account.unrealized_pl)
            self.portfolio.day_pnl = float(account.day_trade_buying_power)
            
            # Update positions
            self.positions = {}
            for pos in positions:
                position = Position(
                    symbol=pos.symbol,
                    quantity=int(pos.qty),
                    avg_cost=float(pos.avg_entry_price),
                    market_value=float(pos.market_value),
                    unrealized_pnl=float(pos.unrealized_pl),
                    realized_pnl=0.0  # This would need to be tracked separately
                )
                self.positions[pos.symbol] = position
            
            self.portfolio.positions = list(self.positions.values())
            
        except Exception as e:
            self.logger.error(f"Failed to update portfolio: {e}")
            raise
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate performance metrics
        
        Returns:
            Dictionary with performance metrics
        """
        try:
            self.update_portfolio()
            
            # Calculate returns
            total_return = (self.portfolio.total_value - self.initial_capital) / self.initial_capital
            
            # Calculate trade statistics
            filled_trades = [t for t in self.trades if t.status == OrderStatus.FILLED]
            buy_trades = [t for t in filled_trades if t.side == "buy"]
            sell_trades = [t for t in filled_trades if t.side == "sell"]
            
            # Calculate win rate
            profitable_trades = 0
            total_trades = len(sell_trades)
            
            for sell_trade in sell_trades:
                # Find corresponding buy trades
                buy_trades_for_symbol = [t for t in buy_trades if t.symbol == sell_trade.symbol and t.timestamp < sell_trade.timestamp]
                if buy_trades_for_symbol:
                    avg_buy_price = sum(t.price for t in buy_trades_for_symbol) / len(buy_trades_for_symbol)
                    if sell_trade.price > avg_buy_price:
                        profitable_trades += 1
            
            win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0
            
            metrics = {
                "total_value": self.portfolio.total_value,
                "total_return": total_return,
                "total_pnl": self.portfolio.total_pnl,
                "day_pnl": self.portfolio.day_pnl,
                "total_trades": len(filled_trades),
                "win_rate": win_rate,
                "positions": len(self.positions),
                "buying_power": self.portfolio.buying_power
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to calculate performance metrics: {e}")
            return {}
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive trading report
        
        Returns:
            Formatted trading report
        """
        try:
            metrics = self.get_performance_metrics()
            
            report = f"""
# Paper Trading Performance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Portfolio Summary
- Total Value: ${metrics.get('total_value', 0):,.2f}
- Total Return: {metrics.get('total_return', 0):.2%}
- Total P&L: ${metrics.get('total_pnl', 0):,.2f}
- Day P&L: ${metrics.get('day_pnl', 0):,.2f}
- Buying Power: ${metrics.get('buying_power', 0):,.2f}

## Trading Statistics
- Total Trades: {metrics.get('total_trades', 0)}
- Win Rate: {metrics.get('win_rate', 0):.1f}%
- Active Positions: {metrics.get('positions', 0)}

## Current Positions
"""
            
            for symbol, position in self.positions.items():
                report += f"""
### {symbol}
- Quantity: {position.quantity}
- Avg Cost: ${position.avg_cost:.2f}
- Market Value: ${position.market_value:,.2f}
- Unrealized P&L: ${position.unrealized_pnl:,.2f}
"""
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate report: {e}")
            return f"Error generating report: {e}"


class TradingAgentPaperTrader:
    """
    Integration class for trading agents with paper trading
    
    This class provides a simple interface for trading agents to execute
    paper trades based on their recommendations.
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize the trading agent paper trader
        
        Args:
            initial_capital: Starting capital for paper trading
        """
        self.engine = PaperTradingEngine(initial_capital=initial_capital)
        self.logger = logging.getLogger('TradingAgentPaperTrader')
    
    def execute_agent_recommendation(self, 
                                   recommendation: str, 
                                   symbol: str, 
                                   confidence: float = 1.0) -> Dict[str, Any]:
        """
        Execute a trading agent recommendation
        
        Args:
            recommendation: Trading recommendation ('BUY', 'SELL', 'HOLD')
            symbol: Stock symbol
            confidence: Confidence level (0.0 to 1.0)
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Parse recommendation
            recommendation = recommendation.upper().strip()
            
            if recommendation not in ['BUY', 'SELL', 'HOLD']:
                raise ValueError(f"Invalid recommendation: {recommendation}")
            
            if recommendation == 'HOLD':
                return {
                    "action": "HOLD",
                    "symbol": symbol,
                    "message": "No action taken - holding position",
                    "confidence": confidence
                }
            
            # Calculate position size based on confidence
            position_size = self._calculate_position_size(symbol, confidence)
            
            if position_size == 0:
                return {
                    "action": "SKIP",
                    "symbol": symbol,
                    "message": "Position size too small or insufficient capital",
                    "confidence": confidence
                }
            
            # Execute trade
            side = "buy" if recommendation == "BUY" else "sell"
            trade = self.engine.execute_trade(symbol, side, position_size)
            
            return {
                "action": recommendation,
                "symbol": symbol,
                "quantity": position_size,
                "price": trade.price,
                "order_id": trade.order_id,
                "confidence": confidence,
                "message": f"Trade executed: {side.upper()} {position_size} {symbol} @ ${trade.price:.2f}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute agent recommendation: {e}")
            return {
                "action": "ERROR",
                "symbol": symbol,
                "message": f"Error executing trade: {e}",
                "confidence": confidence
            }
    
    def _calculate_position_size(self, symbol: str, confidence: float) -> int:
        """
        Calculate position size based on confidence and available capital
        
        Args:
            symbol: Stock symbol
            confidence: Confidence level (0.0 to 1.0)
            
        Returns:
            Number of shares to trade
        """
        try:
            # Get current price
            current_price = self.engine.get_current_price(symbol)
            
            # Calculate maximum position value based on confidence
            max_position_value = self.engine.portfolio.total_value * self.engine.max_position_size * confidence
            
            # Calculate number of shares
            max_shares = int(max_position_value / current_price)
            
            # Ensure minimum trade size
            min_shares = 1
            if max_shares < min_shares:
                return 0
            
            return max_shares
            
        except Exception as e:
            self.logger.error(f"Failed to calculate position size: {e}")
            return 0
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        return self.engine.get_performance_metrics()
    
    def generate_trading_report(self) -> str:
        """Generate trading report"""
        return self.engine.generate_report()


# Example usage and testing functions
def test_paper_trading():
    """Test the paper trading functionality"""
    try:
        # Initialize paper trader
        trader = TradingAgentPaperTrader(initial_capital=100000.0)
        
        # Test buy recommendation
        result = trader.execute_agent_recommendation("BUY", "AAPL", confidence=0.8)
        print("Buy recommendation result:", result)
        
        # Test sell recommendation
        result = trader.execute_agent_recommendation("SELL", "AAPL", confidence=0.6)
        print("Sell recommendation result:", result)
        
        # Test hold recommendation
        result = trader.execute_agent_recommendation("HOLD", "AAPL", confidence=0.5)
        print("Hold recommendation result:", result)
        
        # Get portfolio summary
        summary = trader.get_portfolio_summary()
        print("Portfolio summary:", summary)
        
        # Generate report
        report = trader.generate_trading_report()
        print("Trading report:", report)
        
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    test_paper_trading()
