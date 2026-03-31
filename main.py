import typer
from rich.console import Console
from rich.status import Status

from core.k8s_client import K8sClient
from core.upgrade_checker import UpgradeChecker
from core.scanner import Scanner
from ui.formatter import UI

app = typer.Typer(help="ComplianShift CLI - OpenShift Operators Compliance Diagnostics")

@app.command(name="check-upgrade")
def check_upgrade():
    """
    Check which operators need an upgrade for upcoming OpenShift versions.
    """
    console = Console()
    ui = UI()
    
    ui.print_banner()
    console.print("[bold blue]Starting Operator Upgrade Check...[/bold blue]\n")
    
    with Status("[bold green]Querying OpenShift Cluster...", console=console):
        try:
            k8s = K8sClient()
            current_ocp_version = k8s.get_ocp_version()
            subscriptions = k8s.get_redhat_subscriptions()
        except Exception as e:
            console.print(f"[bold red]Execution error:[/bold red] {e}")
            raise typer.Exit(code=1)
            
    console.print(f"[green]✓ Current OpenShift version:[/green] {current_ocp_version}")
    console.print(f"[green]✓ Found {len(subscriptions)} Red Hat subscriptions in the cluster.[/green]\n")
    
    with Status("[bold green]Analyzing lifecycle data...", console=console):
        try:
            checker = UpgradeChecker()
            results = checker.check_upgrades(current_ocp_version, subscriptions)
        except Exception as e:
            console.print(f"[bold red]Analysis error:[/bold red] {e}")
            raise typer.Exit(code=1)
            
    ui.display_upgrade_results(current_ocp_version, results)

# Typer allows invoking commands without explicit name if we use the callback
@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """
    ComplianShift CLI - OpenShift Operators Compliance Diagnostics
    """
    # If no subcommand was passed (e.g.: ran just `python main.py`), execute the scan
    if ctx.invoked_subcommand is None:
        scan()

@app.command(name="scan")
def scan(
    debug: bool = typer.Option(False, "--debug", help="Show detailed log messages"),
    cache_minutes: int = typer.Option(30, "--cache-minutes", help="Cache validity time in minutes"),
    force: bool = typer.Option(False, "--force", help="Ignore cache and force API and cluster fetch")
):
    """
    Download v2 API JSON and check supportability and compatibility of installed operators.
    """
    console = Console()
    ui = UI()
    
    ui.print_banner()
    console.print("[bold blue]Starting Operator Supportability Scan...[/bold blue]\n")
    
    try:
        k8s = K8sClient()
        scanner = Scanner(k8s_client=k8s)
        
        with Status("[bold green]Downloading lifecycle data (API v2)...", console=console):
            scanner.download_lifecycle_data(cache_minutes=cache_minutes, force=force, console=console, debug=debug)
            
        console.print("[green]✓ Lifecycle data ready.[/green]\n")
        
                # scan_operators already prints progress for each operator
        results = scanner.scan_operators(cache_minutes=cache_minutes, force=force, console=console, debug=debug)
        
        console.print("\n[bold green]Scan complete. Generating consolidated table...[/bold green]\n")
        ui.display_scan_results(results)
        
    except Exception as e:
        console.print(f"[bold red]Error during scan:[/bold red] {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
