"""
Trading Agent Paper Trading Integration
=====================================

This module integrates the existing trading agent system with paper trading
for forward testing and validation of trading recommendations.

Features:
- Seamless integration with existing trading agents
- Automated execution of agent recommendations
- Performance tracking and reporting
- Risk management integration
- Real-time portfolio monitoring
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from .paper_trading import TradingAgentPaperTrader, PaperTradingEngine
from .config import get_config


@dataclass
class AgentTradingSession:
    """Trading session data for an agent"""
    agent_name: str
    symbol: str
    start_time: datetime
    end_time: Optional[datetime] = None
    recommendations: List[Dict[str, Any]] = None
    trades_executed: List[Dict[str, Any]] = None
    performance_metrics: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []
        if self.trades_executed is None:
            self.trades_executed = []
        if self.performance_metrics is None:
            self.performance_metrics = {}


class AgentPaperTradingManager:
    """
    Manager class for integrating trading agents with paper trading
    
    This class handles:
    - Agent recommendation processing
    - Trade execution based on agent decisions
    - Performance tracking per agent
    - Risk management across agents
    - Reporting and analytics
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize the agent paper trading manager
        
        Args:
            initial_capital: Starting capital for paper trading
        """
        self.paper_trader = TradingAgentPaperTrader(initial_capital=initial_capital)
        self.active_sessions: Dict[str, AgentTradingSession] = {}
        self.agent_performance: Dict[str, Dict[str, Any]] = {}
        
        # Setup logging
        self.setup_logging()
        
        # Risk management settings
        self.max_agents_per_symbol = 3
        self.max_daily_trades_per_agent = 10
        self.agent_confidence_threshold = 0.6
        
        self.logger.info("Agent Paper Trading Manager initialized")
    
    def setup_logging(self):
        """Setup logging for agent paper trading"""
        log_dir = os.path.join(get_config()["data_dir"], "agent_paper_trading_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"agent_paper_trading_{datetime.now().strftime('%Y%m%d')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('AgentPaperTradingManager')
    
    def start_agent_session(self, agent_name: str, symbol: str) -> str:
        """
        Start a new trading session for an agent
        
        Args:
            agent_name: Name of the trading agent
            symbol: Stock symbol to trade
            
        Returns:
            Session ID
        """
        session_id = f"{agent_name}_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = AgentTradingSession(
            agent_name=agent_name,
            symbol=symbol,
            start_time=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        self.logger.info(f"Started trading session {session_id} for {agent_name} on {symbol}")
        
        return session_id
    
    def end_agent_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a trading session and calculate performance
        
        Args:
            session_id: Session ID to end
            
        Returns:
            Session performance summary
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session.end_time = datetime.now()
        
        # Calculate session performance
        session.performance_metrics = self._calculate_session_performance(session)
        
        # Update agent performance
        if session.agent_name not in self.agent_performance:
            self.agent_performance[session.agent_name] = {
                "total_sessions": 0,
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_return": 0.0,
                "best_session": None,
                "worst_session": None
            }
        
        self._update_agent_performance(session)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        self.logger.info(f"Ended trading session {session_id}")
        return session.performance_metrics
    
    def process_agent_recommendation(self, 
                                   session_id: str, 
                                   recommendation: str, 
                                   confidence: float = 1.0,
                                   additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a trading agent recommendation
        
        Args:
            session_id: Active session ID
            recommendation: Trading recommendation from agent
            confidence: Confidence level (0.0 to 1.0)
            additional_context: Additional context from agent analysis
            
        Returns:
            Execution result
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        
        # Check if agent has exceeded daily trade limit
        if len(session.trades_executed) >= self.max_daily_trades_per_agent:
            self.logger.warning(f"Agent {session.agent_name} has exceeded daily trade limit")
            return {
                "action": "LIMIT_EXCEEDED",
                "message": "Daily trade limit exceeded",
                "session_id": session_id
            }
        
        # Check confidence threshold
        if confidence < self.agent_confidence_threshold:
            self.logger.info(f"Recommendation confidence {confidence} below threshold {self.agent_confidence_threshold}")
            return {
                "action": "LOW_CONFIDENCE",
                "message": f"Confidence {confidence} below threshold {self.agent_confidence_threshold}",
                "session_id": session_id
            }
        
        # Record recommendation
        recommendation_record = {
            "timestamp": datetime.now().isoformat(),
            "recommendation": recommendation,
            "confidence": confidence,
            "context": additional_context or {}
        }
        session.recommendations.append(recommendation_record)
        
        # Execute trade
        try:
            execution_result = self.paper_trader.execute_agent_recommendation(
                recommendation=recommendation,
                symbol=session.symbol,
                confidence=confidence
            )
            
            # Record trade execution
            if execution_result["action"] in ["BUY", "SELL"]:
                trade_record = {
                    "timestamp": datetime.now().isoformat(),
                    "action": execution_result["action"],
                    "symbol": execution_result["symbol"],
                    "quantity": execution_result.get("quantity", 0),
                    "price": execution_result.get("price", 0.0),
                    "order_id": execution_result.get("order_id", ""),
                    "confidence": confidence,
                    "context": additional_context or {}
                }
                session.trades_executed.append(trade_record)
                
                self.logger.info(f"Executed trade: {execution_result['action']} {execution_result.get('quantity', 0)} {execution_result['symbol']}")
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Failed to execute recommendation: {e}")
            return {
                "action": "ERROR",
                "message": f"Execution failed: {e}",
                "session_id": session_id
            }
    
    def _calculate_session_performance(self, session: AgentTradingSession) -> Dict[str, Any]:
        """
        Calculate performance metrics for a trading session
        
        Args:
            session: Trading session to analyze
            
        Returns:
            Performance metrics
        """
        try:
            # Get current portfolio metrics
            portfolio_metrics = self.paper_trader.get_portfolio_summary()
            
            # Calculate session-specific metrics
            total_trades = len(session.trades_executed)
            buy_trades = [t for t in session.trades_executed if t["action"] == "BUY"]
            sell_trades = [t for t in session.trades_executed if t["action"] == "SELL"]
            
            # Calculate win rate
            profitable_trades = 0
            for sell_trade in sell_trades:
                # Find corresponding buy trades for the same symbol
                symbol_buy_trades = [t for t in buy_trades if t["symbol"] == sell_trade["symbol"] and t["timestamp"] < sell_trade["timestamp"]]
                if symbol_buy_trades:
                    avg_buy_price = sum(t["price"] for t in symbol_buy_trades) / len(symbol_buy_trades)
                    if sell_trade["price"] > avg_buy_price:
                        profitable_trades += 1
            
            win_rate = (profitable_trades / len(sell_trades) * 100) if sell_trades else 0
            
            # Calculate average confidence
            avg_confidence = sum(r["confidence"] for r in session.recommendations) / len(session.recommendations) if session.recommendations else 0
            
            # Calculate session duration
            duration = (session.end_time - session.start_time).total_seconds() / 3600  # hours
            
            performance = {
                "session_id": f"{session.agent_name}_{session.symbol}_{session.start_time.strftime('%Y%m%d_%H%M%S')}",
                "agent_name": session.agent_name,
                "symbol": session.symbol,
                "duration_hours": duration,
                "total_recommendations": len(session.recommendations),
                "total_trades": total_trades,
                "buy_trades": len(buy_trades),
                "sell_trades": len(sell_trades),
                "win_rate": win_rate,
                "avg_confidence": avg_confidence,
                "portfolio_impact": {
                    "total_value": portfolio_metrics.get("total_value", 0),
                    "total_return": portfolio_metrics.get("total_return", 0),
                    "total_pnl": portfolio_metrics.get("total_pnl", 0)
                }
            }
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Failed to calculate session performance: {e}")
            return {"error": str(e)}
    
    def _update_agent_performance(self, session: AgentTradingSession):
        """
        Update overall agent performance metrics
        
        Args:
            session: Completed trading session
        """
        try:
            agent_name = session.agent_name
            performance = session.performance_metrics
            
            if agent_name not in self.agent_performance:
                self.agent_performance[agent_name] = {
                    "total_sessions": 0,
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "avg_return": 0.0,
                    "best_session": None,
                    "worst_session": None
                }
            
            agent_perf = self.agent_performance[agent_name]
            
            # Update counters
            agent_perf["total_sessions"] += 1
            agent_perf["total_trades"] += performance.get("total_trades", 0)
            
            # Update win rate (rolling average)
            current_win_rate = performance.get("win_rate", 0)
            if agent_perf["total_sessions"] == 1:
                agent_perf["win_rate"] = current_win_rate
            else:
                agent_perf["win_rate"] = (agent_perf["win_rate"] * (agent_perf["total_sessions"] - 1) + current_win_rate) / agent_perf["total_sessions"]
            
            # Update best/worst session
            session_return = performance.get("portfolio_impact", {}).get("total_return", 0)
            if agent_perf["best_session"] is None or session_return > agent_perf["best_session"].get("portfolio_impact", {}).get("total_return", 0):
                agent_perf["best_session"] = performance
            if agent_perf["worst_session"] is None or session_return < agent_perf["worst_session"].get("portfolio_impact", {}).get("total_return", 0):
                agent_perf["worst_session"] = performance
            
        except Exception as e:
            self.logger.error(f"Failed to update agent performance: {e}")
    
    def get_agent_performance_summary(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance summary for agents
        
        Args:
            agent_name: Specific agent name, or None for all agents
            
        Returns:
            Performance summary
        """
        if agent_name:
            return self.agent_performance.get(agent_name, {})
        else:
            return self.agent_performance
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about active trading sessions
        
        Returns:
            Dictionary of active sessions
        """
        active_info = {}
        for session_id, session in self.active_sessions.items():
            active_info[session_id] = {
                "agent_name": session.agent_name,
                "symbol": session.symbol,
                "start_time": session.start_time.isoformat(),
                "duration_hours": (datetime.now() - session.start_time).total_seconds() / 3600,
                "recommendations_count": len(session.recommendations),
                "trades_count": len(session.trades_executed)
            }
        
        return active_info
    
    def generate_comprehensive_report(self) -> str:
        """
        Generate a comprehensive report of all agent performance
        
        Returns:
            Formatted report string
        """
        try:
            # Get portfolio summary
            portfolio_summary = self.paper_trader.get_portfolio_summary()
            
            # Get active sessions
            active_sessions = self.get_active_sessions()
            
            # Get agent performance
            agent_performance = self.get_agent_performance_summary()
            
            report = f"""
# Trading Agent Paper Trading Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Portfolio Overview
- Total Value: ${portfolio_summary.get('total_value', 0):,.2f}
- Total Return: {portfolio_summary.get('total_return', 0):.2%}
- Total P&L: ${portfolio_summary.get('total_pnl', 0):,.2f}
- Day P&L: ${portfolio_summary.get('day_pnl', 0):,.2f}
- Total Trades: {portfolio_summary.get('total_trades', 0)}
- Win Rate: {portfolio_summary.get('win_rate', 0):.1f}%

## Active Trading Sessions
"""
            
            if active_sessions:
                for session_id, session_info in active_sessions.items():
                    report += f"""
### {session_info['agent_name']} - {session_info['symbol']}
- Session ID: {session_id}
- Duration: {session_info['duration_hours']:.1f} hours
- Recommendations: {session_info['recommendations_count']}
- Trades Executed: {session_info['trades_count']}
"""
            else:
                report += "\nNo active trading sessions.\n"
            
            report += "\n## Agent Performance Summary\n"
            
            if agent_performance:
                for agent_name, perf in agent_performance.items():
                    report += f"""
### {agent_name}
- Total Sessions: {perf.get('total_sessions', 0)}
- Total Trades: {perf.get('total_trades', 0)}
- Average Win Rate: {perf.get('win_rate', 0):.1f}%
- Best Session Return: {perf.get('best_session', {}).get('portfolio_impact', {}).get('total_return', 0):.2%}
- Worst Session Return: {perf.get('worst_session', {}).get('portfolio_impact', {}).get('total_return', 0):.2%}
"""
            else:
                report += "\nNo agent performance data available.\n"
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive report: {e}")
            return f"Error generating report: {e}"


# Integration functions for existing trading agents
def integrate_with_trading_agent(agent_manager: AgentPaperTradingManager, 
                                agent_name: str, 
                                symbol: str, 
                                recommendation: str, 
                                confidence: float = 1.0,
                                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Integration function for existing trading agents
    
    Args:
        agent_manager: Agent paper trading manager instance
        agent_name: Name of the trading agent
        symbol: Stock symbol
        recommendation: Trading recommendation
        confidence: Confidence level
        context: Additional context
        
    Returns:
        Execution result
    """
    try:
        # Check if there's an active session for this agent and symbol
        active_sessions = agent_manager.get_active_sessions()
        session_id = None
        
        for sid, session_info in active_sessions.items():
            if session_info['agent_name'] == agent_name and session_info['symbol'] == symbol:
                session_id = sid
                break
        
        # Start new session if none exists
        if session_id is None:
            session_id = agent_manager.start_agent_session(agent_name, symbol)
        
        # Process the recommendation
        result = agent_manager.process_agent_recommendation(
            session_id=session_id,
            recommendation=recommendation,
            confidence=confidence,
            additional_context=context
        )
        
        return result
        
    except Exception as e:
        logging.error(f"Failed to integrate with trading agent: {e}")
        return {
            "action": "ERROR",
            "message": f"Integration failed: {e}",
            "agent_name": agent_name,
            "symbol": symbol
        }


# Example usage
def example_usage():
    """Example of how to use the agent paper trading system"""
    
    # Initialize the manager
    manager = AgentPaperTradingManager(initial_capital=100000.0)
    
    # Start a trading session for an agent
    session_id = manager.start_agent_session("BullResearcher", "AAPL")
    
    # Process some recommendations
    result1 = manager.process_agent_recommendation(session_id, "BUY", confidence=0.8)
    print("Buy recommendation result:", result1)
    
    result2 = manager.process_agent_recommendation(session_id, "HOLD", confidence=0.6)
    print("Hold recommendation result:", result2)
    
    result3 = manager.process_agent_recommendation(session_id, "SELL", confidence=0.9)
    print("Sell recommendation result:", result3)
    
    # End the session
    performance = manager.end_agent_session(session_id)
    print("Session performance:", performance)
    
    # Generate comprehensive report
    report = manager.generate_comprehensive_report()
    print("Comprehensive report:", report)


if __name__ == "__main__":
    example_usage()
