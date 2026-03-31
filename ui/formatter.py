from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class UI:
    def __init__(self):
        self.console = Console()

    def print_banner(self):
        banner = """[bold red]
           .-"-.       ____                      _ _               _____ _     _  __ _   
         /|6 6|\\     / ___|___  _ __ ___  _ __ | (_) __ _ _ __   / ___/| |__ (_)/ _| |_ 
        {/(_0_)\\}   | |   / _ \\| '_ ` _ \\| '_ \\| | |/ _` | '_ \\  \\___ \\| '_ \\| | |_| __|
         _/ ^ \\_    | |__| (_) | | | | | | |_) | | | (_| | | | |  ___) | | | | |  _| |_ 
        (/ /^\\ \\)-'  \\____\\___/|_| |_| |_| .__/|_|_|\\__,_|_| |_| |____/|_| |_|_|_|  \\__|
         ""' '""                         |_|                                            
[/bold red][dim]An (unofficial) tool for Red Hat Operators lifecycle analysis on OpenShift.[/dim]
"""
        self.console.print(banner)

    def display_scan_results(self, results):
        self.console.print(f"\n[bold blue]Current OpenShift Version:[/bold blue] {current_version}\n")
        
        if not results:
            self.console.print("[yellow]Could not determine upgrades (unknown version or no future data).[/yellow]")
            return

        for target_version, operators in results.items():
            if not operators:
                self.console.print(f"[bold green]✓ To upgrade to OCP {target_version}:[/bold green] No operator needs a channel change.")
                continue
                
            table = Table(title=f"Operators requiring upgrade for OCP {target_version}", show_header=True, header_style="bold magenta")
            table.add_column("OPERATOR", style="cyan")
            table.add_column("CURRENT CHANNEL", style="red")
            table.add_column("SUPPORTED CHANNELS (TARGET)", style="green")
            
            for op in operators:
                recommended = ", ".join(op["recommended_channels"])
                table.add_row(op["operator"], op["current_channel"], recommended)
                
    def _format_compatibility(self, compat):
        if compat == "Sim" or compat == "Yes":
            return "[green]Yes[/green]"
        if compat == "Não" or compat == "No":
            return "[red]No[/red]"
        if compat == "N/A":
            return "[white]N/A[/white]"
        return compat

    def _format_status(self, status):
        is_eol = False
        if "Full Support" in status:
            formatted_status = f"[green]{status}[/green]"
        elif "Maintenance" in status:
            formatted_status = f"[yellow]{status}[/yellow]"
        elif "End of Life" in status or "End of life" in status or "Unsupported" in status:
            formatted_status = f"[red]{status}[/red]"
            is_eol = True
        elif "Extended Support" in status:
            formatted_status = f"[cyan]{status}[/cyan]"
        else:
            formatted_status = status
            
        return formatted_status, is_eol

    def display_scan_results(self, results):
        if not results:
            self.console.print("[yellow]No Red Hat operator found or analyzed.[/yellow]")
            return
            
        table = Table(title="Operator Compliance Diagnostics (ComplianShift)", show_header=True, header_style="bold magenta")
        table.add_column("NAME", style="cyan")
        table.add_column("SCOPE (NAMESPACE)", style="blue")
        table.add_column("INSTALLED VERSION", style="magenta")
        table.add_column("OCP COMPATIBLE", justify="center")
        table.add_column("SUPPORT STATUS")
        table.add_column("END OF LIFE (EOL)")
        
        has_eol = False
        for res in results:
            scope_str = res["scope"]
            if scope_str == "Namespace":
                scope_str = f"Namespace ({res['namespace']})"
                
            compat = self._format_compatibility(res["ocp_compatible"])
            status, is_eol = self._format_status(res["support_status"])
            
            if is_eol:
                has_eol = True
                
            table.add_row(
                res["name"],
                scope_str,
                res["version"],
                compat,
                status,
                res["end_date"]
            )
            
        self.console.print(table)
        self.console.print()

        if has_eol:
            alert_panel = Panel(
                "[bold red]Warning:[/bold red] One or more operators are End of Life (EOL) or out of the support window.\n"
                "We recommend planning the upgrade of these operators to a supported version as soon as possible to ensure security patches and official Red Hat support.",
                title="Compliance Alert",
                border_style="red"
            )
            self.console.print(alert_panel)
            self.console.print()

