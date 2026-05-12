import typer
from rich.console import Console
from rich.status import Status

from core.k8s_client import K8sClient
from core.scanner import Scanner
from ui.formatter import UI

app = typer.Typer(help="ComplianShift CLI - OpenShift Operators Compliance Diagnostics")


@app.command()
def scan(
    debug: bool = typer.Option(False, "--debug", help="Show detailed log messages"),
    cache_minutes: int = typer.Option(30, "--cache-minutes", help="Cache validity time in minutes"),
    force: bool = typer.Option(False, "--force", help="Ignore cache and force API and cluster fetch"),
    output: str = typer.Option(None, "--output", "-o", help="Export format: html or md"),
    path: str = typer.Option(".", "--path", "-p", help="Directory path for the exported file"),
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

        results = scanner.scan_operators(cache_minutes=cache_minutes, force=force, console=console, debug=debug)

        console.print("\n[bold green]Scan complete. Generating consolidated table...[/bold green]\n")
        ui.display_scan_results(results)

        if output:
            fmt = output.lower()
            if fmt not in ("html", "md"):
                console.print(f"[bold red]Invalid output format '{output}'. Use 'html' or 'md'.[/bold red]")
                raise typer.Exit(code=1)

            from ui.exporter import Exporter
            exporter = Exporter()
            filepath = exporter.export(results, fmt=fmt, output_dir=path)
            console.print(f"[bold green]✓ Report exported to:[/bold green] {filepath}")

    except Exception as e:
        console.print(f"[bold red]Error during scan:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
