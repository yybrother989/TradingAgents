"""New CLI for independent agent execution."""

import typer
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from tradingagents.agents.base_agent import AgentCategory
from tradingagents.agents.registry import get_registry
from tradingagents.agents.runner import AgentRunner
from tradingagents.agents.agent_factory import initialize_agents
from tradingagents.default_config import DEFAULT_CONFIG

console = Console()
app = typer.Typer(name="trading-agents", help="TradingAgents CLI - Run agents independently")


def format_agent_category(category: AgentCategory) -> str:
    """Format agent category for display."""
    return category.value.replace("_", " ").title()


@app.command()
def list(
    llm_provider: str = typer.Option("openai", "--provider", "-p", help="LLM provider (openai, anthropic, google)"),
    quick_model: str = typer.Option("gpt-4o-mini", "--quick-model", help="Quick thinking model"),
    deep_model: str = typer.Option("gpt-4o-mini", "--deep-model", help="Deep thinking model"),
):
    """List all available agents."""
    # Initialize agents first so they're registered
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = llm_provider.lower()
    config["quick_think_llm"] = quick_model
    config["deep_think_llm"] = deep_model
    
    with console.status("[bold green]Initializing agents...") as status:
        initialize_agents(config=config, llm_provider=llm_provider, quick_llm_model=quick_model, deep_llm_model=deep_model)
    
    registry = get_registry()
    agents = registry.list_agents()
    
    if not agents:
        console.print("\n[red]No agents found. Please check initialization.[/red]\n")
        return
    
    console.print("\n[bold green]Available Agents[/bold green]\n")
    
    table = Table(show_header=True, header_style="bold magenta", box=None, show_lines=True)
    table.add_column("Agent Name", style="cyan", width=25, no_wrap=True)
    table.add_column("Type", style="yellow", width=12, no_wrap=True)
    table.add_column("Standalone", style="green", width=10, no_wrap=True)
    table.add_column("Description", style="white", no_wrap=False)
    
    for category in agents:
        agent = registry.get_agent(category)
        if agent:
            standalone = "✅ Yes" if agent.can_run_standalone() else "❌ No"
            table.add_row(
                format_agent_category(category),
                agent.agent_type.value.replace("_", " ").title(),
                standalone,
                agent.get_description()
            )
    
    console.print(table)
    
    # Show agent count
    console.print(f"\n[dim]Total: {len(agents)} agents available[/dim]")


@app.command()
def run(
    ticker: str = typer.Option(..., "--ticker", "-t", help="Stock ticker symbol"),
    date: str = typer.Option(None, "--date", "-d", help="Analysis date (YYYY-MM-DD). Defaults to today"),
    agents: Optional[str] = typer.Option(
        None,
        "--agents",
        "-a",
        help="Comma-separated list of agents to run (e.g., 'market_analyst,news_analyst'). Use 'all' for all agents"
    ),
    llm_provider: str = typer.Option("openai", "--provider", "-p", help="LLM provider (openai, anthropic, google)"),
    quick_model: str = typer.Option("gpt-4o-mini", "--quick-model", help="Quick thinking model"),
    deep_model: str = typer.Option("gpt-4o-mini", "--deep-model", help="Deep thinking model"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory for reports"),
):
    """Run selected agents independently."""
    
    # Set default date
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    
    console.print(f"\n[bold green]Running TradingAgents Analysis[/bold green]")
    console.print(f"Ticker: [cyan]{ticker}[/cyan]")
    console.print(f"Date: [cyan]{date}[/cyan]\n")
    
    # Initialize agents
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = llm_provider.lower()
    config["quick_think_llm"] = quick_model
    config["deep_think_llm"] = deep_model
    
    with console.status("[bold green]Initializing agents...") as status:
        initialize_agents(config=config, llm_provider=llm_provider, quick_llm_model=quick_model, deep_llm_model=deep_model)
    
    registry = get_registry()
    runner = AgentRunner(registry)
    
    # Parse agent selection
    if agents is None:
        # Interactive selection
        selected_categories = _interactive_agent_selection(registry)
    elif agents.lower() == "all":
        selected_categories = registry.list_agents()
    else:
        # Parse comma-separated list
        selected_categories = _parse_agent_list(agents)
    
    if not selected_categories:
        console.print("[red]No agents selected. Exiting.[/red]")
        return
    
    console.print(f"\n[bold]Selected Agents:[/bold] {', '.join(format_agent_category(c) for c in selected_categories)}\n")
    
    # Create execution plan
    plan = runner.create_execution_plan(selected_categories)
    
    console.print(f"[dim]Execution order: {len(plan.execution_order)} levels[/dim]\n")
    
    # Execute agents
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Executing agents...", total=len(selected_categories))
        
        results = runner.execute_agents(selected_categories, ticker, date, config)
        
        progress.update(task, completed=len(selected_categories))
    
    # Display results
    console.print("\n[bold green]Execution Results[/bold green]\n")
    
    results_table = Table(show_header=True, header_style="bold magenta")
    results_table.add_column("Agent", style="cyan", width=25)
    results_table.add_column("Status", style="green", width=15)
    results_table.add_column("Time", style="yellow", width=10)
    results_table.add_column("Report Preview", style="white", width=50)
    
    for category in selected_categories:
        result = results.get(category)
        if result:
            status = "✅ Success" if result.success else f"❌ Failed: {result.error[:30]}"
            preview = result.report[:100] + "..." if len(result.report) > 100 else result.report
            results_table.add_row(
                format_agent_category(category),
                status,
                f"{result.execution_time:.2f}s",
                preview
            )
        else:
            results_table.add_row(
                format_agent_category(category),
                "❌ Not Found",
                "0.00s",
                ""
            )
    
    console.print(results_table)
    
    # Save reports if output directory specified
    if output_dir:
        _save_reports(results, ticker, date, output_dir)
        console.print(f"\n[green]Reports saved to: {output_dir}[/green]")


def _parse_agent_list(agent_string: str) -> List[AgentCategory]:
    """Parse comma-separated agent list."""
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
    
    categories = []
    for agent_name in agent_string.split(","):
        agent_name = agent_name.strip().lower()
        category = agent_map.get(agent_name)
        if category:
            categories.append(category)
        else:
            console.print(f"[yellow]Warning: Unknown agent '{agent_name}', skipping[/yellow]")
    
    return categories


def _interactive_agent_selection(registry) -> List[AgentCategory]:
    """Interactive agent selection."""
    from questionary import checkbox
    
    agents = registry.list_agents()
    choices = [format_agent_category(cat) for cat in agents]
    
    selected = checkbox(
        "Select agents to run:",
        choices=choices,
        default=choices[:4]  # Default to first 4 (analysts)
    ).ask()
    
    # Map back to categories
    category_map = {format_agent_category(cat): cat for cat in agents}
    return [category_map[name] for name in selected if name in category_map]


def _save_reports(results, ticker: str, date: str, output_dir: str):
    """Save agent reports to files."""
    from pathlib import Path
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for category, result in results.items():
        if result.success and result.report:
            filename = output_path / f"{category.value}_{ticker}_{date}.md"
            with open(filename, "w") as f:
                f.write(f"# {result.agent_name} Report\n\n")
                f.write(f"**Ticker:** {ticker}\n")
                f.write(f"**Date:** {date}\n")
                f.write(f"**Execution Time:** {result.execution_time:.2f}s\n\n")
                f.write(result.report)


@app.command()
def info(
    agent: str = typer.Argument(..., help="Agent name (e.g., 'market_analyst')")
):
    """Get information about a specific agent."""
    registry = get_registry()
    
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
    
    category = agent_map.get(agent.lower())
    if not category:
        console.print(f"[red]Unknown agent: {agent}[/red]")
        return
    
    agent_obj = registry.get_agent(category)
    if not agent_obj:
        console.print(f"[red]Agent {agent} not found[/red]")
        return
    
    console.print(f"\n[bold green]Agent Information[/bold green]\n")
    console.print(f"Name: {agent_obj.agent_name}")
    console.print(f"Category: {format_agent_category(category)}")
    console.print(f"Type: {agent_obj.agent_type.value}")
    console.print(f"Description: {agent_obj.get_description()}")
    console.print(f"Can run standalone: {'Yes' if agent_obj.can_run_standalone() else 'No'}")
    
    required = agent_obj.get_required_context()
    if required:
        console.print(f"Required context: {', '.join(required)}")
    else:
        console.print("Required context: None (can run independently)")


if __name__ == "__main__":
    app()

