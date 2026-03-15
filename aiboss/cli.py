import typer
import platform
import socket
from typing import Optional
from .client import AibossClient
from .config import get_agent_id, get_api_url, save_config
from .runner import AgentRunner
from rich.console import Console
from rich.table import Table
from typing import Optional, List

app = typer.Typer()
console = Console()

@app.command()
def enroll(
    code: str = typer.Argument(..., help="Enrollment code from the web dashboard"),
    url: str = typer.Option("http://localhost:3000", help="API URL of the AI Boss server"),
    name: Optional[str] = typer.Option(None, help="Name for this agent (defaults to hostname)"),
    capabilities: Optional[List[str]] = typer.Option(None, help="List of capabilities (default: *)")
):
    """Enroll a new agent. By default, it registers with '*' capability to receive all tasks."""
    if not name:
        name = socket.gethostname()
        
    console.print(f"Enrolling agent '{name}' to {url}...")
    
    # Save base config first so client can use it
    save_config(url, "", "")
    
    client = AibossClient(base_url=url)
    try:
        # If no capabilities provided, default to wildcard *
        if not capabilities:
            capabilities = ["*"]
        
        result = client.enroll(code, name, capabilities)
        
        agent_id = result.get("agent_id")
        if agent_id:
            console.print(f"[green]Successfully enrolled! Agent ID: {agent_id}[/green]")
            console.print(f"API Key: {result.get('api_key')[:8]}...")
        else:
            console.print("[red]Enrollment failed: No Agent ID returned.[/red]")
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

@app.command()
def start():
    """Start the agent to process tasks."""
    agent_id = get_agent_id()
    if not agent_id:
        console.print("[red]Agent not configured. Run 'aiboss enroll' first.[/red]")
        raise typer.Exit(code=1)

    console.print(f"Starting agent {agent_id}...")
    runner = AgentRunner()
    runner.run()

@app.command()
def status():
    """Check agent status and earnings."""
    agent_id = get_agent_id()
    api_url = get_api_url()
    
    if not agent_id:
        console.print("[yellow]Agent not configured.[/yellow]")
        return

    table = Table(title="Agent Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Agent ID", agent_id)
    table.add_row("API URL", api_url)
    
    client = AibossClient()
    
    # Check connectivity via Sync
    try:
        sync_res = client.sync(status="idle")
        if sync_res:
             table.add_row("Connection", "[green]Online[/green]")
        else:
             table.add_row("Connection", "[red]Offline[/red]")
    except Exception as e:
        table.add_row("Connection", f"[red]Error: {e}[/red]")

    # Check earnings
    paycheck = client.get_paycheck()
    if paycheck:
        table.add_row("Name", paycheck.get("agent_name", "N/A"))
        table.add_row("Total Earnings", str(paycheck.get("total_earnings", 0)))
        table.add_row("Rank", str(paycheck.get("rank", "N/A")))
    
    console.print(table)

if __name__ == "__main__":
    app()
