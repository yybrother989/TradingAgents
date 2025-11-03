"""FastAPI server for TradingAgents REST API."""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
from typing import List, Optional, Dict, Any

from tradingagents.api import endpoints
from tradingagents.api.endpoints import (
    analyze_handler,
    health_handler,
    get_config_handler,
    update_config_handler,
    get_cached_analysis_handler
)
from tradingagents.api.models import (
    AnalysisRequest,
    AnalysisResponse,
    ConfigRequest,
    ConfigResponse,
    HealthResponse,
    CachedAnalysisResponse,
    ErrorResponse
)
from tradingagents.api.service import TradingAgentsService
from tradingagents.dataflows.mcp_manager import get_mcp_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("Starting TradingAgents API server...")
    
    # Initialize MCP manager
    try:
        mcp_manager = get_mcp_manager()
        await mcp_manager.ensure_initialized()
        logger.info("MCP manager initialized successfully")
    except Exception as e:
        logger.warning(f"MCP manager initialization failed: {e}")
        logger.warning("Continuing without MCP - some features may not work")
    
    # Initialize service
    try:
        service = TradingAgentsService()
        logger.info("TradingAgents service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TradingAgents API server...")
    
    # Close MCP connections
    try:
        mcp_manager = get_mcp_manager()
        # Cleanup handled by context manager
        logger.info("MCP manager closed")
    except Exception:
        pass


# Create FastAPI app
app = FastAPI(
    title="TradingAgents API",
    description="REST API for TradingAgents multi-agent trading framework",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc)
        ).model_dump()
    )


# API Routes

@app.post("/api/v1/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze(request: AnalysisRequest) -> AnalysisResponse:
    """
    Run analyst agents and return their reports for a stock ticker on a specific date.
    
    **Returns only analyst reports:**
    - Market/Technical Analysis
    - News Analysis
    - Social Media/Sentiment Analysis
    - Fundamentals Analysis
    
    - **ticker**: Stock ticker symbol (e.g., "AAPL", "NVDA")
    - **date**: Trading date in YYYY-MM-DD format
    - **config**: Optional configuration override
    
    Note: This endpoint only returns analyst outputs. Trading decisions, 
    researcher outputs, and risk manager outputs are excluded.
    """
    return await analyze_handler(request)


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health() -> HealthResponse:
    """Health check endpoint."""
    return await health_handler()


@app.get("/api/v1/config", response_model=ConfigResponse, tags=["Configuration"])
async def get_config() -> ConfigResponse:
    """Get current TradingAgents configuration."""
    return await get_config_handler()


@app.post("/api/v1/config", response_model=ConfigResponse, tags=["Configuration"])
async def update_config(request: ConfigRequest) -> ConfigResponse:
    """Update TradingAgents configuration."""
    return await update_config_handler(request)


@app.get(
    "/api/v1/analyses/{ticker}/{date}",
    response_model=CachedAnalysisResponse,
    tags=["Analysis"]
)
async def get_cached_analysis(ticker: str, date: str) -> CachedAnalysisResponse:
    """
    Get cached analysis result for a ticker and date.
    
    Returns only analyst reports from the cache:
    - Market/Technical Analysis
    - News Analysis
    - Social Media/Sentiment Analysis
    - Fundamentals Analysis
    
    - **ticker**: Stock ticker symbol
    - **date**: Trading date in YYYY-MM-DD format
    
    Returns cached analyst reports if available, 404 otherwise.
    """
    return await get_cached_analysis_handler(ticker, date)


@app.post("/api/v1/agents/run", tags=["Agents"])
async def run_agents(
    ticker: str = Body(..., description="Stock ticker symbol"),
    date: str = Body(..., description="Analysis date (YYYY-MM-DD)"),
    agents: Optional[List[str]] = Body(
        None, 
        description="List of analyst agents to run. Valid options: market_analyst, news_analyst, social_analyst, fundamentals_analyst"
    ),
    config: Optional[Dict[str, Any]] = Body(None, description="Optional configuration override")
):
    """
    Run selected analyst agents independently and return their reports.
    
    **Only analyst agents are allowed via API:**
    - market_analyst: Market/Technical analysis
    - news_analyst: News and macroeconomic analysis
    - social_analyst: Social media sentiment analysis
    - fundamentals_analyst: Company fundamentals analysis
    
    If no agents specified, all analysts are run by default.
    """
    from tradingagents.api.endpoints import run_agents_handler
    return await run_agents_handler(
        ticker=ticker,
        date=date,
        agents=agents,
        config=config
    )


@app.get("/api/v1/analyze/stream", tags=["Analysis"])
async def stream_analysis(
    ticker: str,
    date: str,
    config: Optional[str] = None
):
    """
    Stream analysis results in real-time using Server-Sent Events (SSE).
    
    **Perfect for daily report generation with progressive updates:**
    - Frontend receives updates as each analyst completes
    - No need to wait for all reports
    - Real-time progress tracking
    - Efficient for daily scheduled reports
    
    **Event Types:**
    - `start`: Analysis started
    - `report`: Individual report completed (contains report data)
    - `complete`: All reports finished
    - `error`: Error occurred
    
    **Usage:**
    ```javascript
    const eventSource = new EventSource(
      `/api/v1/analyze/stream?ticker=TSLA&date=2024-10-31`
    );
    
    eventSource.addEventListener('report', (e) => {
      const data = JSON.parse(e.data);
      console.log(`${data.agent} completed:`, data.report);
    });
    
    eventSource.addEventListener('complete', (e) => {
      const data = JSON.parse(e.data);
      console.log('All reports complete:', data.reports);
      eventSource.close();
    });
    ```
    
    - **ticker**: Stock ticker symbol (e.g., "TSLA", "AAPL")
    - **date**: Trading date in YYYY-MM-DD format
    - **config**: Optional JSON-encoded configuration override
    """
    from tradingagents.api.endpoints import stream_analysis_handler
    
    config_dict = None
    if config:
        try:
            config_dict = json.loads(config)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON in config parameter"
            )
    
    return await stream_analysis_handler(ticker, date, config_dict)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "TradingAgents API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("TRADINGAGENTS_HOST", "0.0.0.0")
    port = int(os.getenv("TRADINGAGENTS_PORT", 8000))
    debug = os.getenv("TRADINGAGENTS_DEBUG", "false").lower() == "true"
    
    uvicorn.run(
        "tradingagents.api.server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )

