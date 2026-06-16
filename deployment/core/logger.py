"""
Deployment Logger

Rich console wrapper for consistent logging across deployment scripts.
"""

from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


class DeploymentLogger:
    """Consistent logging interface for deployment scripts"""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize deployment logger.
        
        Args:
            verbose: Enable verbose output
        """
        self.console = Console()
        self.verbose = verbose
    
    def banner(self, title: str, subtitle: Optional[str] = None):
        """Print a deployment banner"""
        lines = [
            "[bold cyan]╔══════════════════════════════════════════════════════════╗[/bold cyan]",
            "[bold cyan]║                                                          ║[/bold cyan]",
            f"[bold cyan]║  {title:^54}  ║[/bold cyan]",
        ]
        
        if subtitle:
            lines.extend([
                "[bold cyan]║                                                          ║[/bold cyan]",
                f"[bold cyan]║  {subtitle:^54}  ║[/bold cyan]",
            ])
        
        lines.extend([
            "[bold cyan]║                                                          ║[/bold cyan]",
            "[bold cyan]╚══════════════════════════════════════════════════════════╝[/bold cyan]",
        ])
        
        self.console.print("\n".join(lines))
    
    def section(self, title: str, subtitle: Optional[str] = None):
        """Print a section header"""
        self.console.print("\n" + "="*60)
        self.console.print(f"[bold magenta]{title}[/bold magenta]")
        if subtitle:
            self.console.print(f"[dim]{subtitle}[/dim]")
        self.console.print("="*60 + "\n")
    
    def success(self, message: str):
        """Print success message"""
        self.console.print(f"[green]✅ {message}[/green]")
    
    def error(self, message: str):
        """Print error message"""
        self.console.print(f"[red]❌ {message}[/red]")
    
    def warning(self, message: str):
        """Print warning message"""
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")
    
    def info(self, message: str):
        """Print info message"""
        self.console.print(f"[blue]ℹ️  {message}[/blue]")
    
    def debug(self, message: str):
        """Print debug message (only if verbose)"""
        if self.verbose:
            self.console.print(f"[dim]🔍 {message}[/dim]")
    
    def dry_run(self, message: str):
        """Print dry-run message"""
        self.console.print(f"[blue]🔍 {message}[/blue]")
    
    def item_success(self, item: str, message: str = ""):
        """Print success for an item"""
        msg = f"{item:50} - {message}" if message else f"{item:50}"
        self.console.print(f"[green]✓[/green] {msg}")
    
    def item_error(self, item: str, message: str):
        """Print error for an item"""
        self.console.print(f"[red]✗[/red] {item:50} - {message[:50]}")
    
    def item_warning(self, item: str, message: str):
        """Print warning for an item"""
        self.console.print(f"[yellow]⚠[/yellow] {item:50} - {message[:50]}")
    
    def item_skip(self, item: str, message: str = "Skipped"):
        """Print skip message for an item"""
        self.console.print(f"[dim]○[/dim] {item:50} - {message}")
    
    def summary(self, title: str, stats: Dict[str, int]):
        """
        Print summary statistics.
        
        Args:
            title: Summary title
            stats: Dict of stat_name -> count
        """
        self.console.print(f"\n[bold]{title}:[/bold]")
        for name, count in stats.items():
            self.console.print(f"  {name}: {count}")
    
    def table(
        self, 
        title: str, 
        columns: list[str], 
        rows: list[list[Any]],
        show_header: bool = True
    ):
        """
        Print a formatted table.
        
        Args:
            title: Table title
            columns: Column names
            rows: List of row data
            show_header: Show column headers
        """
        table = Table(title=title, show_header=show_header, header_style="bold cyan")
        
        for col in columns:
            table.add_column(col)
        
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        
        self.console.print(table)
    
    def panel(
        self, 
        message: str, 
        title: Optional[str] = None,
        style: str = "green"
    ):
        """
        Print a panel/box with message.
        
        Args:
            message: Panel content
            title: Optional title
            style: Border style (green, yellow, red, blue)
        """
        self.console.print(Panel(
            message,
            title=title,
            border_style=style
        ))
    
    def progress_context(self):
        """
        Create a progress context manager for long-running operations.
        
        Returns:
            Progress context manager
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True
        )
    
    def separator(self):
        """Print a separator line"""
        self.console.print("="*60)
    
    def blank_line(self):
        """Print a blank line"""
        self.console.print()
