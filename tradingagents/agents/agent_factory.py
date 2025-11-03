"""Factory for creating agents and registering them."""

from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from tradingagents.agents.base_agent import AgentCategory, AgentType
from tradingagents.agents.graph_agent_adapter import GraphAgentAdapter
from tradingagents.agents.registry import get_registry
from tradingagents.agents import *
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.default_config import DEFAULT_CONFIG


def initialize_agents(
    config: Optional[Dict[str, Any]] = None,
    llm_provider: Optional[str] = None,
    quick_llm_model: Optional[str] = None,
    deep_llm_model: Optional[str] = None
) -> None:
    """
    Initialize all agents and register them in the registry.
    
    Args:
        config: Configuration dictionary
        llm_provider: LLM provider ("openai", "anthropic", "google")
        quick_llm_model: Model name for quick thinking agents
        deep_llm_model: Model name for deep thinking agents
    """
    config = config or DEFAULT_CONFIG.copy()
    provider = llm_provider or config.get("llm_provider", "openai").lower()
    quick_model = quick_llm_model or config.get("quick_think_llm", "gpt-4o-mini")
    deep_model = deep_llm_model or config.get("deep_think_llm", "gpt-4o-mini")
    
    # Initialize LLMs
    if provider == "openai" or provider == "ollama" or provider == "openrouter":
        quick_llm = ChatOpenAI(model=quick_model, base_url=config.get("backend_url", "https://api.openai.com/v1"))
        deep_llm = ChatOpenAI(model=deep_model, base_url=config.get("backend_url", "https://api.openai.com/v1"))
    elif provider == "anthropic":
        quick_llm = ChatAnthropic(model=quick_model, base_url=config.get("backend_url"))
        deep_llm = ChatAnthropic(model=deep_model, base_url=config.get("backend_url"))
    elif provider == "google":
        quick_llm = ChatGoogleGenerativeAI(model=quick_model)
        deep_llm = ChatGoogleGenerativeAI(model=deep_model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
    
    # Initialize memories
    bull_memory = FinancialSituationMemory("bull_memory", config)
    bear_memory = FinancialSituationMemory("bear_memory", config)
    trader_memory = FinancialSituationMemory("trader_memory", config)
    invest_judge_memory = FinancialSituationMemory("invest_judge_memory", config)
    risk_manager_memory = FinancialSituationMemory("risk_manager_memory", config)
    
    registry = get_registry()
    
    # Register analyst agents
    if True:  # Always register analysts
        market_node = create_market_analyst(quick_llm)
        adapter = GraphAgentAdapter(
            graph_node_func=market_node,
            agent_name="Market Analyst",
            agent_category=AgentCategory.MARKET_ANALYST,
            agent_type=AgentType.ANALYST,
            llm=quick_llm,
            config=config
        )
        registry.register_graph_adapter(adapter, AgentCategory.MARKET_ANALYST)
        
        social_node = create_social_media_analyst(quick_llm)
        adapter = GraphAgentAdapter(
            graph_node_func=social_node,
            agent_name="Social Media Analyst",
            agent_category=AgentCategory.SOCIAL_ANALYST,
            agent_type=AgentType.ANALYST,
            llm=quick_llm,
            config=config
        )
        registry.register_graph_adapter(adapter, AgentCategory.SOCIAL_ANALYST)
        
        news_node = create_news_analyst(quick_llm)
        adapter = GraphAgentAdapter(
            graph_node_func=news_node,
            agent_name="News Analyst",
            agent_category=AgentCategory.NEWS_ANALYST,
            agent_type=AgentType.ANALYST,
            llm=quick_llm,
            config=config
        )
        registry.register_graph_adapter(adapter, AgentCategory.NEWS_ANALYST)
        
        fundamentals_node = create_fundamentals_analyst(quick_llm)
        adapter = GraphAgentAdapter(
            graph_node_func=fundamentals_node,
            agent_name="Fundamentals Analyst",
            agent_category=AgentCategory.FUNDAMENTALS_ANALYST,
            agent_type=AgentType.ANALYST,
            llm=quick_llm,
            config=config
        )
        registry.register_graph_adapter(adapter, AgentCategory.FUNDAMENTALS_ANALYST)
    
    # Register researcher agents
    bull_node = create_bull_researcher(quick_llm, bull_memory)
    adapter = GraphAgentAdapter(
        graph_node_func=bull_node,
        agent_name="Bull Researcher",
        agent_category=AgentCategory.BULL_RESEARCHER,
        agent_type=AgentType.RESEARCHER,
        llm=quick_llm,
        config=config,
        memory=bull_memory
    )
    registry.register_graph_adapter(adapter, AgentCategory.BULL_RESEARCHER)
    
    bear_node = create_bear_researcher(quick_llm, bear_memory)
    adapter = GraphAgentAdapter(
        graph_node_func=bear_node,
        agent_name="Bear Researcher",
        agent_category=AgentCategory.BEAR_RESEARCHER,
        agent_type=AgentType.RESEARCHER,
        llm=quick_llm,
        config=config,
        memory=bear_memory
    )
    registry.register_graph_adapter(adapter, AgentCategory.BEAR_RESEARCHER)
    
    research_manager_node = create_research_manager(deep_llm, invest_judge_memory)
    adapter = GraphAgentAdapter(
        graph_node_func=research_manager_node,
        agent_name="Research Manager",
        agent_category=AgentCategory.RESEARCH_MANAGER,
        agent_type=AgentType.MANAGER,
        llm=deep_llm,
        config=config,
        memory=invest_judge_memory
    )
    registry.register_graph_adapter(adapter, AgentCategory.RESEARCH_MANAGER)
    
    # Register trader
    trader_node = create_trader(quick_llm, trader_memory)
    adapter = GraphAgentAdapter(
        graph_node_func=trader_node,
        agent_name="Trader",
        agent_category=AgentCategory.TRADER,
        agent_type=AgentType.TRADER,
        llm=quick_llm,
        config=config,
        memory=trader_memory
    )
    registry.register_graph_adapter(adapter, AgentCategory.TRADER)
    
    # Register risk managers
    risky_node = create_risky_debator(quick_llm)
    adapter = GraphAgentAdapter(
        graph_node_func=risky_node,
        agent_name="Risky Analyst",
        agent_category=AgentCategory.RISKY_ANALYST,
        agent_type=AgentType.RISK_MANAGER,
        llm=quick_llm,
        config=config
    )
    registry.register_graph_adapter(adapter, AgentCategory.RISKY_ANALYST)
    
    neutral_node = create_neutral_debator(quick_llm)
    adapter = GraphAgentAdapter(
        graph_node_func=neutral_node,
        agent_name="Neutral Analyst",
        agent_category=AgentCategory.NEUTRAL_ANALYST,
        agent_type=AgentType.RISK_MANAGER,
        llm=quick_llm,
        config=config
    )
    registry.register_graph_adapter(adapter, AgentCategory.NEUTRAL_ANALYST)
    
    conservative_node = create_safe_debator(quick_llm)
    adapter = GraphAgentAdapter(
        graph_node_func=conservative_node,
        agent_name="Conservative Analyst",
        agent_category=AgentCategory.CONSERVATIVE_ANALYST,
        agent_type=AgentType.RISK_MANAGER,
        llm=quick_llm,
        config=config
    )
    registry.register_graph_adapter(adapter, AgentCategory.CONSERVATIVE_ANALYST)
    
    risk_manager_node = create_risk_manager(deep_llm, risk_manager_memory)
    adapter = GraphAgentAdapter(
        graph_node_func=risk_manager_node,
        agent_name="Risk Manager",
        agent_category=AgentCategory.RISK_MANAGER,
        agent_type=AgentType.MANAGER,
        llm=deep_llm,
        config=config,
        memory=risk_manager_memory
    )
    registry.register_graph_adapter(adapter, AgentCategory.RISK_MANAGER)

