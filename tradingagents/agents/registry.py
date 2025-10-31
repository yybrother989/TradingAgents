"""Agent registry for managing and discovering agents."""

from typing import Dict, List, Optional, Type, Any
from enum import Enum
from tradingagents.agents.base_agent import BaseAgent, AgentCategory, AgentType
from tradingagents.agents.graph_agent_adapter import GraphAgentAdapter


class AgentRegistry:
    """Registry for managing all available agents."""
    
    def __init__(self):
        """Initialize the registry."""
        self._agents: Dict[AgentCategory, BaseAgent] = {}
    
    def register_agent(self, agent: BaseAgent, category: Optional[AgentCategory] = None):
        """Register a standalone agent or adapter."""
        cat = category or agent.agent_category
        self._agents[cat] = agent
    
    def register_graph_adapter(
        self,
        adapter: GraphAgentAdapter,
        category: AgentCategory
    ):
        """Register a graph agent adapter."""
        self._agents[category] = adapter
    
    def get_agent(self, category: AgentCategory) -> Optional[BaseAgent]:
        """Get agent by category."""
        return self._agents.get(category)
    
    def list_agents(self) -> List[AgentCategory]:
        """List all available agent categories."""
        return sorted(list(self._agents.keys()), key=lambda x: x.value)
    
    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        """Get all agents of a specific type."""
        return [
            agent for agent in self._agents.values()
            if agent.agent_type == agent_type
        ]
    
    def can_execute(
        self,
        categories: List[AgentCategory],
        available_context: Optional[Dict[str, str]] = None
    ) -> Dict[AgentCategory, bool]:
        """
        Check which agents can be executed with available context.
        
        Args:
            categories: List of agent categories to check
            available_context: Available context from other agents
        
        Returns:
            Dict mapping category to whether it can execute
        """
        available_context = available_context or {}
        results = {}
        
        for category in categories:
            agent = self.get_agent(category)
            if agent is None:
                results[category] = False
                continue
            
            if isinstance(agent, GraphAgentAdapter):
                # Graph adapters can always run with minimal state
                results[category] = True
            elif isinstance(agent, BaseAgent):
                required = agent.get_required_context()
                if not required:
                    results[category] = True
                else:
                    # Check if all required context is available
                    results[category] = all(
                        key in available_context for key in required
                    )
            else:
                results[category] = False
        
        return results


# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry

