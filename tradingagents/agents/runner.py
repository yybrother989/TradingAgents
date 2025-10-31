"""Agent runner for executing agents independently."""

import time
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional, AsyncIterator, Callable
from dataclasses import dataclass

from tradingagents.agents.base_agent import BaseAgent, AgentCategory, AgentResult
from tradingagents.agents.registry import AgentRegistry
from tradingagents.agents.graph_agent_adapter import GraphAgentAdapter


@dataclass
class ExecutionPlan:
    """Plan for executing multiple agents."""
    categories: List[AgentCategory]
    dependencies: Dict[AgentCategory, List[AgentCategory]]
    execution_order: List[List[AgentCategory]]  # Agents grouped by execution level


class AgentRunner:
    """Runner for executing agents independently."""
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        """Initialize runner.
        
        Args:
            registry: Agent registry instance (uses global if None)
        """
        from tradingagents.agents.registry import get_registry
        self.registry = registry or get_registry()
    
    def create_execution_plan(
        self,
        categories: List[AgentCategory]
    ) -> ExecutionPlan:
        """
        Create execution plan based on agent dependencies.
        
        Args:
            categories: List of agent categories to execute
        
        Returns:
            ExecutionPlan with ordered execution groups
        """
        # Build dependency map
        dependencies = {}
        for category in categories:
            agent = self.registry.get_agent(category)
            if agent:
                dependencies[category] = agent.get_required_context()
        
        # Create execution order using topological sort
        execution_order = []
        remaining = set(categories)
        completed = set()
        
        while remaining:
            # Find agents that can run now (no unmet dependencies)
            ready = []
            for category in remaining:
                agent = self.registry.get_agent(category)
                if agent:
                    required_context = agent.get_required_context()
                    # Check if all required context is available from completed agents
                    deps_satisfied = True
                    if required_context:
                        # Build available context keys from completed agents
                        available_keys = set()
                        for completed_cat in completed:
                            key = self._get_context_key(completed_cat)
                            if key:
                                available_keys.add(key)
                        
                        # Check if all required keys are available
                        deps_satisfied = all(key in available_keys for key in required_context)
                    
                    if deps_satisfied or not required_context:
                        ready.append(category)
            
            if not ready:
                # Circular dependency or missing dependency - add remaining anyway
                ready = list(remaining)
            
            execution_order.append(ready)
            completed.update(ready)
            remaining -= set(ready)
        
        return ExecutionPlan(
            categories=categories,
            dependencies=dependencies,
            execution_order=execution_order
        )
    
    def _context_key_matches_category(self, context_key: str, category: AgentCategory) -> bool:
        """Check if context key matches an agent category."""
        # For now, return True to allow execution - dependencies handled by required_context
        return True
    
    def execute_agents(
        self,
        categories: List[AgentCategory],
        ticker: str,
        date: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[AgentCategory, AgentResult]:
        """
        Execute multiple agents in dependency order.
        
        Args:
            categories: List of agent categories to execute
            ticker: Stock ticker symbol
            date: Analysis date
            config: Optional configuration
        
        Returns:
            Dict mapping category to AgentResult
        """
        plan = self.create_execution_plan(categories)
        results: Dict[AgentCategory, AgentResult] = {}
        context: Dict[str, str] = {}
        
        # Execute agents in order with parallel execution within each level
        for level in plan.execution_order:
            level_results = {}
            
            # Execute agents in parallel within the same level (they're independent)
            if len(level) > 1:
                # Parallel execution for independent agents
                with concurrent.futures.ThreadPoolExecutor(max_workers=len(level)) as executor:
                    future_to_category = {}
                    for category in level:
                        agent = self.registry.get_agent(category)
                        if agent:
                            future = executor.submit(
                                agent.execute, ticker, date, context.copy()
                            )
                            future_to_category[future] = category
                    
                    # Collect results
                    for future in concurrent.futures.as_completed(future_to_category):
                        category = future_to_category[future]
                        try:
                            result = future.result()
                            results[category] = result
                            level_results[category] = result
                        except Exception as e:
                            results[category] = AgentResult(
                                agent_name=category.value,
                                agent_category=category,
                                report="",
                                metadata={},
                                execution_time=0.0,
                                success=False,
                                error=f"Execution failed: {str(e)}"
                            )
            else:
                # Single agent - execute directly
                category = level[0]
                agent = self.registry.get_agent(category)
                if not agent:
                    results[category] = AgentResult(
                        agent_name=category.value,
                        agent_category=category,
                        report="",
                        metadata={},
                        execution_time=0.0,
                        success=False,
                        error=f"Agent {category.value} not found in registry"
                    )
                else:
                    result = agent.execute(ticker, date, context)
                    results[category] = result
                    level_results[category] = result
            
            # Update context after level completes
            for category, result in level_results.items():
                # Update context with this agent's output
                context_key = self._get_context_key(category)
                if context_key and result.success:
                    context[context_key] = result.report
                    
                # Also update state-like context for complex agents
                if result.success and result.metadata.get("state"):
                    state = result.metadata["state"]
                    # Add investment_debate_state if available
                    if "investment_debate_state" in state:
                        context["investment_debate_state"] = state["investment_debate_state"]
                    # Add risk_debate_state if available
                    if "risk_debate_state" in state:
                        context["risk_debate_state"] = state["risk_debate_state"]
        
        return results
    
    def execute_single_agent(
        self,
        category: AgentCategory,
        ticker: str,
        date: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Execute a single agent independently.
        
        Args:
            category: Agent category to execute
            ticker: Stock ticker symbol
            date: Analysis date
            context: Optional context from other agents
        
        Returns:
            AgentResult
        """
        agent = self.registry.get_agent(category)
        if not agent:
            return AgentResult(
                agent_name=category.value,
                agent_category=category,
                report="",
                metadata={},
                execution_time=0.0,
                success=False,
                error=f"Agent {category.value} not found in registry"
            )
        
        return agent.execute(ticker, date, context or {})
    
    def _get_context_key(self, category: AgentCategory) -> Optional[str]:
        """Get context key for an agent category."""
        mapping = {
            AgentCategory.MARKET_ANALYST: "market_report",
            AgentCategory.SOCIAL_ANALYST: "sentiment_report",
            AgentCategory.NEWS_ANALYST: "news_report",
            AgentCategory.FUNDAMENTALS_ANALYST: "fundamentals_report",
            AgentCategory.BULL_RESEARCHER: None,  # Handled via investment_debate_state
            AgentCategory.BEAR_RESEARCHER: None,
            AgentCategory.RESEARCH_MANAGER: "investment_plan",
            AgentCategory.TRADER: "trader_investment_plan",
            AgentCategory.RISKY_ANALYST: None,  # Handled via risk_debate_state
            AgentCategory.NEUTRAL_ANALYST: None,
            AgentCategory.CONSERVATIVE_ANALYST: None,
            AgentCategory.RISK_MANAGER: "final_trade_decision",
        }
        return mapping.get(category)

