"""Adapter to make graph-based agents compatible with standalone execution."""

from typing import Dict, Any, Optional, List
from tradingagents.agents.base_agent import BaseAgent, AgentCategory, AgentType, AgentResult
import time


class GraphAgentAdapter(BaseAgent):
    """Adapter that wraps graph-based agents for standalone execution."""
    
    def __init__(
        self,
        graph_node_func,
        agent_name: str,
        agent_category: AgentCategory,
        agent_type: AgentType,
        llm,
        config: Optional[Dict[str, Any]] = None,
        memory=None
    ):
        """Initialize adapter.
        
        Args:
            graph_node_func: The original graph node function
            agent_name: Name of the agent
            agent_category: Category of the agent
            agent_type: Type of agent
            llm: Language model instance
            config: Optional configuration
            memory: Optional memory instance
        """
        super().__init__(agent_name, agent_category, agent_type, llm, config, memory)
        self.graph_node_func = graph_node_func
    
    def execute(
        self,
        ticker: str,
        date: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """Execute graph node with minimal state."""
        start_time = time.time()
        
        try:
            # Create minimal state for graph node with date prominently featured
            state = {
                "company_of_interest": ticker,
                "trade_date": date,  # Analysis date - agents should use this for context
                "messages": [("human", f"Analyze {ticker} as of {date}")],
                # Initialize empty state components
                "investment_debate_state": {
                    "history": "",
                    "current_response": "",
                    "count": 0,
                    "bull_history": "",
                    "bear_history": "",
                },
                "risk_debate_state": {
                    "history": "",
                    "current_risky_response": "",
                    "current_safe_response": "",
                    "current_neutral_response": "",
                    "count": 0,
                },
                "market_report": "",
                "fundamentals_report": "",
                "sentiment_report": "",
                "news_report": "",
                "investment_plan": "",
                "trader_investment_plan": "",
                "final_trade_decision": "",
            }
            
            # Add context if provided (from other agents)
            # Truncate long reports to prevent context length errors
            max_report_length = 2000  # Roughly 500 tokens per report
            
            if context:
                # Map context keys to state keys
                context_mapping = {
                    "market_report": "market_report",
                    "sentiment_report": "sentiment_report",
                    "news_report": "news_report",
                    "fundamentals_report": "fundamentals_report",
                    "investment_plan": "investment_plan",
                    "trader_investment_plan": "trader_investment_plan",
                }
                for key, value in context.items():
                    state_key = context_mapping.get(key, key)
                    if isinstance(value, str):
                        # Truncate long reports to prevent token overflow
                        if len(value) > max_report_length:
                            state[state_key] = value[:max_report_length] + "\n\n[Report truncated - see full report in final output]"
                        else:
                            state[state_key] = value
                    else:
                        state[state_key] = value
            
            # Execute the graph node function
            # Handle both regular nodes and partial functions (like trader)
            if hasattr(self.graph_node_func, 'keywords'):
                # It's a functools.partial, call with name parameter
                result = self.graph_node_func(state, name=self.agent_name)
            else:
                result = self.graph_node_func(state)
            
            # Check if agent made tool calls that need to be executed
            # This is needed for non-MCP analysts (News, Social, Fundamentals)
            # In the graph workflow, ToolNode executes tools, but in standalone mode we need to do it
            messages = result.get("messages", [])
            max_iterations = 3  # Prevent infinite loops
            iteration = 0
            
            while messages and iteration < max_iterations:
                last_message = messages[-1]
                
                # Check if last message has tool calls
                has_tool_calls = False
                tool_calls_list = []
                
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    has_tool_calls = True
                    tool_calls_list = last_message.tool_calls
                elif isinstance(last_message, dict) and 'tool_calls' in last_message:
                    has_tool_calls = True
                    tool_calls_list = last_message.get('tool_calls', [])
                
                if not has_tool_calls or not tool_calls_list:
                    break  # No tool calls, we're done
                
                iteration += 1
                
                # Execute tool calls and get results
                from langchain_core.messages import ToolMessage, HumanMessage
                from tradingagents.agents.utils.agent_utils import (
                    get_news, get_global_news, get_fundamentals,
                    get_balance_sheet, get_cashflow, get_income_statement
                )
                
                # Map tool names to functions
                tool_map = {
                    "get_news": get_news,
                    "get_global_news": get_global_news,
                    "get_fundamentals": get_fundamentals,
                    "get_balance_sheet": get_balance_sheet,
                    "get_cashflow": get_cashflow,
                    "get_income_statement": get_income_statement,
                }
                
                tool_messages = []
                for tool_call in tool_calls_list:
                    # Handle both dict and object tool calls
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get('name', '')
                        tool_args = tool_call.get('args', {})
                        tool_id = tool_call.get('id', f"call_{tool_name}")
                    else:
                        tool_name = getattr(tool_call, 'name', '')
                        tool_args = getattr(tool_call, 'args', {}) or {}
                        tool_id = getattr(tool_call, 'id', f"call_{tool_name}")
                    
                    if tool_name in tool_map:
                        try:
                            # Execute the tool - LangChain tools use .invoke()
                            tool_func = tool_map[tool_name]
                            
                            # Prepare arguments
                            if tool_name == "get_global_news":
                                # Special handling for get_global_news
                                final_args = {"curr_date": date, "look_back_days": 7, "limit": 10}
                            elif tool_name == "get_news":
                                # get_news needs ticker, start_date, end_date
                                from datetime import datetime, timedelta
                                analysis_dt = datetime.strptime(date, "%Y-%m-%d")
                                end_date = date
                                start_date = (analysis_dt - timedelta(days=7)).strftime("%Y-%m-%d")
                                final_args = {
                                    "ticker": tool_args.get("ticker", ticker) if isinstance(tool_args, dict) else ticker,
                                    "start_date": tool_args.get("start_date", start_date) if isinstance(tool_args, dict) else start_date,
                                    "end_date": tool_args.get("end_date", end_date) if isinstance(tool_args, dict) else end_date,
                                }
                            else:
                                # Other tools - merge with ticker if needed
                                if isinstance(tool_args, dict):
                                    final_args = tool_args.copy()
                                    if ticker and "ticker" not in final_args:
                                        final_args["ticker"] = ticker
                                else:
                                    final_args = {"ticker": ticker} if ticker else {}
                            
                            # Invoke LangChain tool using .invoke() method
                            tool_result = tool_func.invoke(final_args)
                            
                            # Create tool message
                            tool_msg = ToolMessage(
                                content=str(tool_result) if tool_result else "No data returned",
                                tool_call_id=tool_id
                            )
                            tool_messages.append(tool_msg)
                        except Exception as e:
                            import traceback
                            error_msg = f"Error calling {tool_name}: {str(e)}\n{traceback.format_exc()}"
                            tool_msg = ToolMessage(
                                content=error_msg,
                                tool_call_id=tool_id
                            )
                            tool_messages.append(tool_msg)
                    else:
                        # Unknown tool
                        tool_msg = ToolMessage(
                            content=f"Tool {tool_name} not found in tool_map",
                            tool_call_id=tool_id if 'tool_id' in locals() else f"call_{tool_name}"
                        )
                        tool_messages.append(tool_msg)
                
                # If we got tool results, call the agent again with tool results
                if tool_messages:
                    # Update state with tool messages
                    # Use proper message format for LangChain
                    from langchain_core.messages import HumanMessage, AIMessage
                    
                    # Build message history properly
                    if isinstance(state["messages"], list):
                        if len(state["messages"]) > 0 and isinstance(state["messages"][0], tuple):
                            # Convert tuple format to message objects
                            new_messages = [HumanMessage(content=state["messages"][0][1])] if state["messages"] else []
                        else:
                            new_messages = list(state["messages"])
                    else:
                        new_messages = []
                    
                    # Add the tool call message and tool results
                    new_messages.append(last_message)
                    new_messages.extend(tool_messages)
                    state["messages"] = new_messages
                    
                    # Call agent again with tool results
                    if hasattr(self.graph_node_func, 'keywords'):
                        result = self.graph_node_func(state, name=self.agent_name)
                    else:
                        result = self.graph_node_func(state)
                    
                    # Update messages for next iteration
                    messages = result.get("messages", [])
                else:
                    break  # No tool messages, exit loop
            
            execution_time = time.time() - start_time
            
            # Extract report based on agent category
            report = self._extract_report(result)
            
            return AgentResult(
                agent_name=self.agent_name,
                agent_category=self.agent_category,
                report=report,
                metadata={
                    "state": result,
                    "messages_count": len(result.get("messages", []))
                },
                execution_time=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return AgentResult(
                agent_name=self.agent_name,
                agent_category=self.agent_category,
                report="",
                metadata={},
                execution_time=execution_time,
                success=False,
                error=str(e)
            )
    
    def _extract_report(self, result: Dict[str, Any]) -> str:
        """Extract report from graph node result based on category."""
        # Map categories to their report keys
        report_mapping = {
            AgentCategory.MARKET_ANALYST: "market_report",
            AgentCategory.SOCIAL_ANALYST: "sentiment_report",
            AgentCategory.NEWS_ANALYST: "news_report",
            AgentCategory.FUNDAMENTALS_ANALYST: "fundamentals_report",
            AgentCategory.BULL_RESEARCHER: lambda r: r.get("investment_debate_state", {}).get("bull_history", ""),
            AgentCategory.BEAR_RESEARCHER: lambda r: r.get("investment_debate_state", {}).get("bear_history", ""),
            AgentCategory.RESEARCH_MANAGER: lambda r: r.get("investment_debate_state", {}).get("judge_decision", ""),
            AgentCategory.TRADER: "trader_investment_plan",
            AgentCategory.RISKY_ANALYST: lambda r: r.get("risk_debate_state", {}).get("risky_history", ""),
            AgentCategory.NEUTRAL_ANALYST: lambda r: r.get("risk_debate_state", {}).get("neutral_history", ""),
            AgentCategory.CONSERVATIVE_ANALYST: lambda r: r.get("risk_debate_state", {}).get("safe_history", ""),
            AgentCategory.RISK_MANAGER: lambda r: r.get("risk_debate_state", {}).get("judge_decision", ""),
        }
        
        extractor = report_mapping.get(self.agent_category)
        if extractor is None:
            return ""
        
        if callable(extractor):
            return extractor(result) or ""
        else:
            return result.get(extractor, "")
    
    def get_required_context(self) -> List[str]:
        """Get required context keys based on agent category."""
        # Define context dependencies for each agent type
        context_requirements = {
            AgentCategory.MARKET_ANALYST: [],
            AgentCategory.SOCIAL_ANALYST: [],
            AgentCategory.NEWS_ANALYST: [],
            AgentCategory.FUNDAMENTALS_ANALYST: [],
            AgentCategory.BULL_RESEARCHER: ["market_report", "sentiment_report", "news_report", "fundamentals_report"],
            AgentCategory.BEAR_RESEARCHER: ["market_report", "sentiment_report", "news_report", "fundamentals_report"],
            AgentCategory.RESEARCH_MANAGER: ["investment_debate_state"],
            AgentCategory.TRADER: ["investment_plan"],
            AgentCategory.RISKY_ANALYST: ["trader_investment_plan", "market_report", "news_report"],
            AgentCategory.NEUTRAL_ANALYST: ["trader_investment_plan", "market_report", "news_report"],
            AgentCategory.CONSERVATIVE_ANALYST: ["trader_investment_plan", "market_report", "news_report"],
            AgentCategory.RISK_MANAGER: ["risk_debate_state"],
        }
        
        return context_requirements.get(self.agent_category, [])

