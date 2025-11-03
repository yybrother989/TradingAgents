"""Base agent interface for standalone execution."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class AgentType(Enum):
    """Types of agents in the TradingAgents framework."""
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    TRADER = "trader"
    RISK_MANAGER = "risk_manager"
    MANAGER = "manager"


class AgentCategory(Enum):
    """Agent categories for grouping."""
    MARKET_ANALYST = "market_analyst"
    SOCIAL_ANALYST = "social_analyst"
    NEWS_ANALYST = "news_analyst"
    FUNDAMENTALS_ANALYST = "fundamentals_analyst"
    BULL_RESEARCHER = "bull_researcher"
    BEAR_RESEARCHER = "bear_researcher"
    RESEARCH_MANAGER = "research_manager"
    TRADER = "trader"
    RISKY_ANALYST = "risky_analyst"
    NEUTRAL_ANALYST = "neutral_analyst"
    CONSERVATIVE_ANALYST = "conservative_analyst"
    RISK_MANAGER = "risk_manager"


@dataclass
class AgentResult:
    """Result from agent execution."""
    agent_name: str
    agent_category: AgentCategory
    report: str
    metadata: Dict[str, Any]
    execution_time: float
    success: bool
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base class for all agents that can run independently."""
    
    def __init__(
        self,
        agent_name: str,
        agent_category: AgentCategory,
        agent_type: AgentType,
        llm,
        config: Optional[Dict[str, Any]] = None,
        memory=None
    ):
        """Initialize base agent.
        
        Args:
            agent_name: Human-readable name of the agent
            agent_category: Category enum for this agent
            agent_type: Type of agent (analyst, researcher, etc.)
            llm: Language model instance
            config: Optional configuration dict
            memory: Optional memory instance
        """
        self.agent_name = agent_name
        self.agent_category = agent_category
        self.agent_type = agent_type
        self.llm = llm
        self.config = config or {}
        self.memory = memory
    
    @abstractmethod
    def execute(
        self,
        ticker: str,
        date: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Execute the agent independently.
        
        Args:
            ticker: Stock ticker symbol
            date: Analysis date in YYYY-MM-DD format
            context: Optional context from other agents (e.g., previous reports)
        
        Returns:
            AgentResult with report and metadata
        """
        pass
    
    @abstractmethod
    def get_required_context(self) -> List[str]:
        """
        Get list of context keys this agent requires from other agents.
        Returns empty list if agent can run standalone.
        
        Returns:
            List of context keys (e.g., ['market_report', 'news_report'])
        """
        pass
    
    def can_run_standalone(self) -> bool:
        """Check if agent can run without context from other agents."""
        return len(self.get_required_context()) == 0
    
    def get_description(self) -> str:
        """Get human-readable description of what this agent does."""
        return f"{self.agent_name} - {self.agent_category.value}"


class GraphAgentAdapter:
    """Adapter to make graph-based agents compatible with BaseAgent interface."""
    
    def __init__(self, graph_node_func, agent_name: str, agent_category: AgentCategory):
        """Initialize adapter.
        
        Args:
            graph_node_func: The original graph node function
            agent_name: Name of the agent
            agent_category: Category of the agent
        """
        self.graph_node_func = graph_node_func
        self.agent_name = agent_name
        self.agent_category = agent_category
    
    def execute(
        self,
        ticker: str,
        date: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute graph node with minimal state."""
        # Create minimal state for graph node
        state = {
            "company_of_interest": ticker,
            "trade_date": date,
            "messages": [("human", ticker)],
        }
        
        # Add context if provided
        if context:
            state.update(context)
        
        # Execute the graph node function
        result = self.graph_node_func(state)
        
        return result

