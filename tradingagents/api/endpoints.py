"""API endpoint handlers for TradingAgents."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import HTTPException, BackgroundTasks, Body
from fastapi.responses import StreamingResponse
import json
import asyncio
from tradingagents.api.models import (
    AnalysisRequest,
    AnalysisResponse,
    ConfigRequest,
    ConfigResponse,
    HealthResponse,
    ErrorResponse,
    CachedAnalysisResponse
)
from tradingagents.api.service import TradingAgentsService

# Get package version
try:
    import importlib.metadata
    package_version = importlib.metadata.version("tradingagents")
except Exception:
    package_version = "1.0.0"


# Global service instance
_service: TradingAgentsService = None


def get_service() -> TradingAgentsService:
    """Get or create the global service instance."""
    global _service
    if _service is None:
        _service = TradingAgentsService()
    return _service


async def analyze_handler(request: AnalysisRequest) -> AnalysisResponse:
    """
    Handle analysis requests.
    
    Args:
        request: Analysis request with ticker, date, and optional config
    
    Returns:
        Analysis response with decision and reports
    """
    try:
        service = get_service()
        result = service.analyze(
            ticker=request.ticker,
            date=request.date,
            config_override=request.config
        )
        
        # Convert reports dict to AnalysisReports model
        from tradingagents.api.models import AnalysisReports, ReportSection
        
        reports_data = result["reports"]
        
        # Safely convert report sections
        def safe_report_section(report_data):
            if report_data and isinstance(report_data, dict):
                return ReportSection(**report_data)
            elif report_data and isinstance(report_data, str):
                return ReportSection(content=report_data)
            return None
        
        # Only include analyst reports
        reports = AnalysisReports(
            market_report=safe_report_section(reports_data.get("market_report")),
            sentiment_report=safe_report_section(reports_data.get("sentiment_report")),
            news_report=safe_report_section(reports_data.get("news_report")),
            fundamentals_report=safe_report_section(reports_data.get("fundamentals_report"))
        )
        
        return AnalysisResponse(
            ticker=result["ticker"],
            date=result["date"],
            reports=reports,
            execution_time=result["execution_time"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


async def health_handler() -> HealthResponse:
    """Handle health check requests."""
    return HealthResponse(
        status="ok",
        version=package_version if hasattr(package_version, '__version__') else "1.0.0"
    )


async def get_config_handler() -> ConfigResponse:
    """Get current configuration."""
    try:
        service = get_service()
        config = service.get_config()
        return ConfigResponse(
            success=True,
            config=config,
            message="Configuration retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get configuration: {str(e)}"
        )


async def update_config_handler(request: ConfigRequest) -> ConfigResponse:
    """Update configuration."""
    try:
        service = get_service()
        success = service.update_config(request.config)
        if success:
            return ConfigResponse(
                success=True,
                config=service.get_config(),
                message="Configuration updated successfully"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to update configuration"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )


async def run_agents_handler(
    ticker: str = Body(..., description="Stock ticker symbol"),
    date: str = Body(..., description="Analysis date (YYYY-MM-DD)"),
    agents: Optional[List[str]] = Body(None, description="List of agent categories to run"),
    config: Optional[Dict[str, Any]] = Body(None, description="Optional configuration override")
) -> Dict[str, Any]:
    """Run selected agents independently."""
    try:
        from tradingagents.agents.base_agent import AgentCategory
        from tradingagents.agents.runner import AgentRunner
        from tradingagents.agents.agent_factory import initialize_agents
        from tradingagents.agents.registry import get_registry
        
        # Initialize agents
        service = get_service()
        agent_config = service.get_config()
        if config:
            agent_config.update(config)
        
        initialize_agents(
            config=agent_config,
            llm_provider=agent_config.get("llm_provider", "openai"),
            quick_llm_model=agent_config.get("quick_think_llm", "gpt-4o-mini"),
            deep_llm_model=agent_config.get("deep_think_llm", "gpt-4o-mini")
        )
        
        # Parse agent categories
        agent_map = {
            "market_analyst": AgentCategory.MARKET_ANALYST,
            "social_analyst": AgentCategory.SOCIAL_ANALYST,
            "news_analyst": AgentCategory.NEWS_ANALYST,
            "fundamentals_analyst": AgentCategory.FUNDAMENTALS_ANALYST,
            "bull_researcher": AgentCategory.BULL_RESEARCHER,
            "bear_researcher": AgentCategory.BEAR_RESEARCHER,
            "research_manager": AgentCategory.RESEARCH_MANAGER,
            "trader": AgentCategory.TRADER,
            "risky_analyst": AgentCategory.RISKY_ANALYST,
            "neutral_analyst": AgentCategory.NEUTRAL_ANALYST,
            "conservative_analyst": AgentCategory.CONSERVATIVE_ANALYST,
            "risk_manager": AgentCategory.RISK_MANAGER,
        }
        
        # Only allow analyst agents via API
        analyst_categories = {
            "market_analyst": AgentCategory.MARKET_ANALYST,
            "social_analyst": AgentCategory.SOCIAL_ANALYST,
            "news_analyst": AgentCategory.NEWS_ANALYST,
            "fundamentals_analyst": AgentCategory.FUNDAMENTALS_ANALYST,
        }
        
        if agents is None:
            # Default to all analysts
            categories = list(analyst_categories.values())
        else:
            # Filter to only analyst agents
            categories = [analyst_categories[a] for a in agents if a in analyst_categories]
            if not categories:
                raise HTTPException(
                    status_code=400,
                    detail=f"Only analyst agents are allowed via API. Valid options: {list(analyst_categories.keys())}"
                )
        
        # Execute agents
        registry = get_registry()
        runner = AgentRunner(registry)
        results = runner.execute_agents(categories, ticker, date, agent_config)
        
        # Format response
        return {
            "ticker": ticker,
            "date": date,
            "agents": [cat.value for cat in categories],
            "results": {
                cat.value: {
                    "report": r.report,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "error": r.error
                }
                for cat, r in results.items()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


async def stream_analysis_handler(
    ticker: str,
    date: str,
    config: Optional[Dict[str, Any]] = None
):
    """
    Stream analysis results as Server-Sent Events (SSE).
    
    This endpoint provides real-time updates as reports are generated:
    - 'start' event: Analysis started
    - 'report' event: Individual report completed
    - 'complete' event: All reports finished
    
    Args:
        ticker: Stock ticker symbol
        date: Analysis date (YYYY-MM-DD)
        config: Optional configuration override
    
    Yields:
        SSE formatted events with report progress
    """
    async def generate_events():
        """Generate SSE events from streaming analysis."""
        try:
            service = get_service()
            event_stream = service.stream_analysis(
                ticker=ticker,
                date=date,
                config_override=config
            )
            
            # Convert sync generator to async
            for event in event_stream:
                # Format as SSE: "event: type\ndata: json\n\n"
                event_type = event.get("event_type", "progress")
                data_json = json.dumps(event)
                
                yield f"event: {event_type}\ndata: {data_json}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.1)
                
        except Exception as e:
            # Send error event
            error_event = {
                "event_type": "error",
                "error": str(e),
                "ticker": ticker,
                "date": date,
                "timestamp": datetime.now().isoformat()
            }
            yield f"event: error\ndata: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


async def get_cached_analysis_handler(ticker: str, date: str) -> CachedAnalysisResponse:
    """Get cached analysis result - Returns only analyst reports."""
    try:
        service = get_service()
        cached_result = service.get_cached_analysis(ticker, date)
        
        if cached_result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No cached analysis found for {ticker} on {date}"
            )
        
        # Filter to only include analyst reports
        filtered_result = {
            "ticker": cached_result.get("ticker"),
            "date": cached_result.get("date"),
            "reports": {
                "market_report": cached_result.get("reports", {}).get("market_report"),
                "sentiment_report": cached_result.get("reports", {}).get("sentiment_report"),
                "news_report": cached_result.get("reports", {}).get("news_report"),
                "fundamentals_report": cached_result.get("reports", {}).get("fundamentals_report"),
            },
            "execution_time": cached_result.get("execution_time"),
            "timestamp": cached_result.get("timestamp"),
            "cached_at": cached_result.get("cached_at")
        }
        
        return CachedAnalysisResponse(
            ticker=filtered_result["ticker"],
            date=filtered_result["date"],
            result=filtered_result,
            cached_at=filtered_result.get("cached_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cached analysis: {str(e)}"
        )

