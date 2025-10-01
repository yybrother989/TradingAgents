from datetime import datetime, timedelta
from typing import Dict, Any


def calculate_timeframes_from_analysis_date(analysis_date: str) -> Dict[str, Dict[str, Any]]:
    """Calculate specific date ranges backward from user's analysis date"""
    base_date = datetime.strptime(analysis_date, "%Y-%m-%d")
    
    timeframes = {
        'fundamental': {
            'start_date': (base_date - timedelta(days=365)).strftime("%Y-%m-%d"),
            'end_date': analysis_date,
            'period': '12 months',
            'description': '12-month historical analysis'
        },
        'technical': {
            'start_date': (base_date - timedelta(days=180)).strftime("%Y-%m-%d"),
            'end_date': analysis_date,
            'period': '6 months',
            'description': '6-month trend analysis'
        },
        'sentiment': {
            'start_date': (base_date - timedelta(days=90)).strftime("%Y-%m-%d"),
            'end_date': analysis_date,
            'period': '3 months',
            'description': '3-month sentiment analysis'
        },
        'news': {
            'start_date': (base_date - timedelta(days=90)).strftime("%Y-%m-%d"),
            'end_date': analysis_date,
            'period': '3 months',
            'description': '3-month news analysis'
        },
        'risk': {
            'start_date': (base_date - timedelta(days=365)).strftime("%Y-%m-%d"),
            'end_date': analysis_date,
            'period': '12 months',
            'description': '12-month risk assessment'
        }
    }
    
    return timeframes


def add_timeframe_to_existing_prompt(original_prompt: str, agent_role: str, analysis_date: str) -> str:
    """Add timeframe context to existing agent prompts without changing structure"""
    
    # Calculate timeframes based on analysis date
    timeframes = calculate_timeframes_from_analysis_date(analysis_date)
    
    # Get timeframe info for this agent role
    role_timeframe_mapping = {
        'market_analyst': 'technical',
        'fundamentals_analyst': 'fundamental', 
        'social_media_analyst': 'sentiment',
        'news_analyst': 'news',
        'risk_manager': 'risk',
        'research_manager': 'fundamental',
        'bull_researcher': 'technical',
        'bear_researcher': 'technical',
        'risky_debator': 'technical',
        'safe_debator': 'risk',
        'neutral_debator': 'technical',
        'trader': 'technical'
    }
    
    timeframe_key = role_timeframe_mapping.get(agent_role, 'technical')
    timeframe_info = timeframes[timeframe_key]
    
    # Add timeframe context to existing prompt
    timeframe_context = f"""

ANALYSIS TIMEFRAME: Please focus your analysis on the period from {timeframe_info['start_date']} to {timeframe_info['end_date']} ({timeframe_info['period']}).

This means:
- For data analysis: Use data from {timeframe_info['start_date']} to {timeframe_info['end_date']}
- For trend analysis: Focus on trends within this {timeframe_info['period']} period
- For comparisons: Compare current state to the beginning of this period ({timeframe_info['start_date']})
- For recommendations: Base your analysis on developments within this timeframe
"""
    
    enhanced_prompt = original_prompt + timeframe_context
    return enhanced_prompt

