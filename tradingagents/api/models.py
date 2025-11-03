"""Pydantic models for TradingAgents API requests and responses."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class AnalysisRequest(BaseModel):
    """Request model for analysis endpoint."""
    ticker: str = Field(..., description="Stock ticker symbol (e.g., 'AAPL', 'NVDA')")
    date: str = Field(..., description="Trading date in YYYY-MM-DD format")
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional configuration override for this analysis"
    )


class ReportSection(BaseModel):
    """Individual report section."""
    content: str = Field(..., description="Report content")
    timestamp: Optional[str] = Field(None, description="Report generation timestamp")


class AnalysisReports(BaseModel):
    """Analyst reports only - Market, News, Social, and Fundamentals analysis."""
    market_report: Optional[ReportSection] = Field(None, description="Market/Technical analysis report")
    sentiment_report: Optional[ReportSection] = Field(None, description="Social media sentiment analysis report")
    news_report: Optional[ReportSection] = Field(None, description="News and macroeconomic analysis report")
    fundamentals_report: Optional[ReportSection] = Field(None, description="Company fundamentals analysis report")


class AnalysisResponse(BaseModel):
    """Response model for analysis endpoint - Analyst reports only."""
    ticker: str = Field(..., description="Analyzed ticker symbol")
    date: str = Field(..., description="Analysis date")
    reports: AnalysisReports = Field(..., description="Analyst reports (Market, News, Social, Fundamentals)")
    execution_time: float = Field(..., description="Analysis execution time in seconds")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Response timestamp"
    )


class ConfigRequest(BaseModel):
    """Request model for configuration update."""
    config: Dict[str, Any] = Field(..., description="Configuration dictionary to update")


class ConfigResponse(BaseModel):
    """Response model for configuration operations."""
    success: bool = Field(..., description="Whether operation succeeded")
    config: Optional[Dict[str, Any]] = Field(None, description="Current configuration")
    message: Optional[str] = Field(None, description="Optional message")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(default="ok", description="Service status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Health check timestamp"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Error timestamp"
    )


class CachedAnalysisResponse(BaseModel):
    """Response model for cached analysis retrieval."""
    ticker: str = Field(..., description="Ticker symbol")
    date: str = Field(..., description="Analysis date")
    result: Dict[str, Any] = Field(..., description="Cached analysis result")
    cached_at: Optional[str] = Field(None, description="Cache timestamp")


class ReportProgressEvent(BaseModel):
    """Event model for streaming report updates."""
    event_type: str = Field(..., description="Event type: 'start', 'progress', 'report', 'complete', 'error'")
    agent: Optional[str] = Field(None, description="Agent name for progress/report events")
    progress: Optional[Dict[str, Any]] = Field(None, description="Progress information")
    report: Optional[ReportSection] = Field(None, description="Completed report (for 'report' events)")
    status: Optional[str] = Field(None, description="Status message")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status/progress."""
    ticker: str = Field(..., description="Stock ticker symbol")
    date: str = Field(..., description="Analysis date")
    status: str = Field(..., description="Overall status: 'pending', 'in_progress', 'completed', 'failed'")
    progress: Dict[str, str] = Field(..., description="Individual agent statuses")
    completed_reports: Dict[str, bool] = Field(..., description="Which reports are completed")
    started_at: Optional[str] = Field(None, description="When analysis started")
    completed_at: Optional[str] = Field(None, description="When analysis completed")
    execution_time: Optional[float] = Field(None, description="Total execution time in seconds")

