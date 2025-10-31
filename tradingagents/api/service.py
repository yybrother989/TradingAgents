"""Service layer for TradingAgents API."""

import time
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, AsyncIterator, Callable
from datetime import datetime

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.agents.runner import AgentRunner
from tradingagents.agents.registry import get_registry
from tradingagents.agents.base_agent import AgentCategory


class TradingAgentsService:
    """Service class that wraps TradingAgentsGraph and manages caching."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the service with configuration."""
        self.config = config or DEFAULT_CONFIG.copy()
        self.graph: Optional[TradingAgentsGraph] = None
        self.cache_dir = Path(self.config.get("results_dir", "./results"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_graph(self) -> TradingAgentsGraph:
        """Get or create TradingAgentsGraph instance."""
        if self.graph is None:
            self.graph = TradingAgentsGraph(
                debug=self.config.get("debug", False),
                config=self.config
            )
        return self.graph
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update configuration."""
        try:
            self.config.update(new_config)
            # Recreate graph with new config
            self.graph = None
            return True
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()
    
    def analyze(
        self,
        ticker: str,
        date: str,
        config_override: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run analysis for a ticker on a specific date.
        
        Args:
            ticker: Stock ticker symbol
            date: Trading date in YYYY-MM-DD format
            config_override: Optional configuration override for this analysis
        
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        
        # Use config override if provided, otherwise use service config
        analysis_config = self.config.copy()
        if config_override:
            analysis_config.update(config_override)
        
        # Check cache first
        cache_key = self._get_cache_key(ticker, date)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            cached_result["execution_time"] = time.time() - start_time
            cached_result["from_cache"] = True
            return cached_result
        
        # Create graph with analysis config
        graph = TradingAgentsGraph(
            debug=analysis_config.get("debug", False),
            config=analysis_config
        )
        
        # Run analysis
        try:
            final_state, decision = graph.propagate(ticker, date)
            
            execution_time = time.time() - start_time
            
            # Format response - Only include analyst reports
            reports_dict = {}
            
            # Only include analyst report sections (exclude researchers, traders, risk managers)
            if final_state.get("market_report"):
                reports_dict["market_report"] = self._format_report(final_state.get("market_report", ""))
            if final_state.get("sentiment_report"):
                reports_dict["sentiment_report"] = self._format_report(final_state.get("sentiment_report", ""))
            if final_state.get("news_report"):
                reports_dict["news_report"] = self._format_report(final_state.get("news_report", ""))
            if final_state.get("fundamentals_report"):
                reports_dict["fundamentals_report"] = self._format_report(final_state.get("fundamentals_report", ""))
            
            result = {
                "ticker": ticker,
                "date": date,
                "reports": reports_dict,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "from_cache": False
            }
            
            # Cache the result
            self._save_to_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
    
    def get_cached_analysis(self, ticker: str, date: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result if available."""
        cache_key = self._get_cache_key(ticker, date)
        return self._get_from_cache(cache_key)
    
    def _get_cache_key(self, ticker: str, date: str) -> str:
        """Generate cache key for ticker and date."""
        return f"{ticker}_{date}"
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache entry."""
        return self.cache_dir / f"{cache_key}_cache.json"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve result from cache if available."""
        cache_path = self._get_cache_path(cache_key)
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
                # Check if cache is still valid (24 hours)
                cached_at = datetime.fromisoformat(data.get("cached_at", ""))
                if (datetime.now() - cached_at).total_seconds() > 86400:
                    cache_path.unlink()  # Delete expired cache
                    return None
                return data
        except Exception:
            return None
    
    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Save result to cache."""
        cache_path = self._get_cache_path(cache_key)
        try:
            result["cached_at"] = datetime.now().isoformat()
            with open(cache_path, 'w') as f:
                json.dump(result, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save cache: {e}")
    
    def _format_report(self, report_content: str) -> Dict[str, Any]:
        """Format report content for response."""
        return {
            "content": report_content,
            "timestamp": datetime.now().isoformat()
        }
    
    def stream_analysis(
        self,
        ticker: str,
        date: str,
        config_override: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Stream analysis results as they're generated (for daily report generation).
        
        Args:
            ticker: Stock ticker symbol
            date: Trading date in YYYY-MM-DD format
            config_override: Optional configuration override
            progress_callback: Optional callback for progress updates
        
        Yields:
            Progress events with report updates
        """
        start_time = time.time()
        
        # Use config override if provided
        analysis_config = self.config.copy()
        if config_override:
            analysis_config.update(config_override)
        
        # Check cache first
        cache_key = self._get_cache_key(ticker, date)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            # Yield cached result
            yield {
                "event_type": "complete",
                "ticker": ticker,
                "date": date,
                "reports": cached_result["reports"],
                "from_cache": True,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
            return
        
        # Initialize agents for streaming execution
        from tradingagents.agents.agent_factory import initialize_agents
        initialize_agents(
            config=analysis_config,
            llm_provider=analysis_config.get("llm_provider", "openai"),
            quick_llm_model=analysis_config.get("quick_think_llm", "gpt-4o-mini"),
            deep_llm_model=analysis_config.get("deep_think_llm", "gpt-4o-mini")
        )
        
        # Define analyst categories only (for API exposure)
        analyst_categories = {
            "market_analyst": AgentCategory.MARKET_ANALYST,
            "news_analyst": AgentCategory.NEWS_ANALYST,
            "social_analyst": AgentCategory.SOCIAL_ANALYST,
            "fundamentals_analyst": AgentCategory.FUNDAMENTALS_ANALYST,
        }
        
        categories = list(analyst_categories.values())
        
        # Create runner and execution plan
        registry = get_registry()
        runner = AgentRunner(registry)
        plan = runner.create_execution_plan(categories)
        
        # Track progress
        total_agents = len(categories)
        completed = 0
        reports_dict = {}
        context = {}
        
        # Yield start event
        yield {
            "event_type": "start",
            "ticker": ticker,
            "date": date,
            "total_agents": total_agents,
            "timestamp": datetime.now().isoformat()
        }
        
        # Execute agents level by level
        for level_idx, level in enumerate(plan.execution_order):
            # Execute agents in parallel within level
            import concurrent.futures
            level_results = {}
            
            def execute_agent(category: AgentCategory) -> tuple:
                """Execute single agent and return (category, result)."""
                agent = registry.get_agent(category)
                if not agent:
                    return category, AgentResult(
                        agent_name=category.value,
                        agent_category=category,
                        report="",
                        metadata={},
                        execution_time=0.0,
                        success=False,
                        error=f"Agent {category.value} not found"
                    )
                return category, agent.execute(ticker, date, context.copy())
            
            # Execute in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(level)) as executor:
                futures = {executor.submit(execute_agent, cat): cat for cat in level}
                
                for future in concurrent.futures.as_completed(futures):
                    category, result = future.result()
                    level_results[category] = result
                    completed += 1
                    
                    # Yield progress update
                    if result.success:
                        context_key = runner._get_context_key(category)
                        if context_key:
                            reports_dict[context_key] = self._format_report(result.report)
                            context[context_key] = result.report
                            
                            # Map category to report name
                            report_name_map = {
                                "market_report": "market_analyst",
                                "news_report": "news_analyst",
                                "sentiment_report": "social_analyst",
                                "fundamentals_report": "fundamentals_analyst",
                            }
                            agent_name = report_name_map.get(context_key, category.value)
                            
                            # Yield report completion event
                            yield {
                                "event_type": "report",
                                "ticker": ticker,
                                "date": date,
                                "agent": agent_name,
                                "report_key": context_key,
                                "report": reports_dict[context_key],
                                "progress": {
                                    "completed": completed,
                                    "total": total_agents,
                                    "percentage": int((completed / total_agents) * 100)
                                },
                                "timestamp": datetime.now().isoformat()
                            }
                    
                    # Yield progress event
                    if progress_callback:
                        progress_callback({
                            "completed": completed,
                            "total": total_agents,
                            "current_agent": category.value
                        })
            
            # Update context after level
            for category, result in level_results.items():
                context_key = runner._get_context_key(category)
                if context_key and result.success:
                    context[context_key] = result.report
        
        # Final result
        execution_time = time.time() - start_time
        
        # Cache the result
        result = {
            "ticker": ticker,
            "date": date,
            "reports": reports_dict,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "from_cache": False
        }
        self._save_to_cache(cache_key, result)
        
        # Yield completion event
        yield {
            "event_type": "complete",
            "ticker": ticker,
            "date": date,
            "reports": reports_dict,
            "execution_time": execution_time,
            "from_cache": False,
            "timestamp": datetime.now().isoformat()
        }

