"""
Complete LMIP Deployment Orchestrator

This script orchestrates the full deployment of the LMIP project:
0. Bootstrap infrastructure (schemas, tables, metadata) - ONE-TIME
1. Deploy workspace assets (notebooks, files) - REPEATABLE
2. Deploy Databricks Jobs - REPEATABLE
3. Validate the deployment - VERIFICATION

Usage:
    python deploy_all.py [--dry-run] [--update] [--skip-validation] [--skip-bootstrap]

Examples:
    # Full deployment (bootstrap + workspace + jobs + validation)
    python deploy_all.py
    
    # Deploy with updates to existing resources
    python deploy_all.py --update
    
    # Deploy without bootstrap (schemas/tables already exist)
    python deploy_all.py --skip-bootstrap
    
    # Dry run to preview changes
    python deploy_all.py --dry-run
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from config import get_config, DeploymentConfig
from deploy_workspace import WorkspaceDeployer
from deploy_jobs import JobDeployer
from validate_deployment import DeploymentValidator
from bootstrap import LMIPBootstrapper


console = Console()


class FullDeployer:
    """Orchestrate complete LMIP deployment"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        
    def print_banner(self):
        """Print deployment banner"""
        banner = """
[bold cyan]╔══════════════════════════════════════════════════════════╗
║                                                          ║
║           LMIP DEPLOYMENT ORCHESTRATOR                   ║
║                                                          ║
║  Labor Market Intelligence Platform - Full Deployment    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝[/bold cyan]
"""
        console.print(banner)
        self.config.print_summary()
    
    def bootstrap_infrastructure(self) -> bool:
        """Bootstrap LMIP infrastructure: schemas, tables, and metadata (ONE-TIME)"""
        console.print("\n" + "="*60)
        console.print("[bold magenta]🚀 STEP 0: Bootstrapping Infrastructure[/bold magenta]")
        console.print("="*60)
        console.print("[dim]This step creates Unity Catalog schemas, tables, and seeds metadata[/dim]\n")
        
        try:
            # Get project root
            project_root = Path(__file__).parent.parent
            
            # Create bootstrapper
            bootstrapper = LMIPBootstrapper(
                catalog=self.config.catalog,
                project_root=project_root,
                dry_run=self.config.dry_run
            )
            
            success = bootstrapper.bootstrap()
            
            if success:
                console.print("[green]✅ Infrastructure bootstrap completed successfully[/green]")
            else:
                console.print("[yellow]⚠️  Infrastructure bootstrap completed with warnings[/yellow]")
            
            return success
            
        except Exception as e:
            console.print(f"[red]❌ Infrastructure bootstrap failed: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
            return False
    
    def deploy_workspace(self) -> bool:
        """Deploy workspace assets (REPEATABLE)"""
        console.print("\n" + "="*60)
        console.print("[bold magenta]📁 STEP 1: Deploying Workspace Assets[/bold magenta]")
        console.print("="*60)
        console.print("[dim]This step uploads notebooks, SQL files, and helper scripts[/dim]\n")
        
        try:
            deployer = WorkspaceDeployer(self.config)
            
            # Get notebooks directory
            notebooks_dir = Path(__file__).parent.parent / "notebooks"
            if not notebooks_dir.exists():
                console.print(f"[red]❌ Notebooks directory not found: {notebooks_dir}[/red]")
                return False
            
            workspace_root = f"{self.config.workspace_root}/notebooks"
            result = deployer.deploy_directory(notebooks_dir, workspace_root)
            
            if result["summary"]["error"] > 0:
                console.print("[yellow]⚠️  Workspace deployment completed with errors[/yellow]")
                return False
            
            console.print("[green]✅ Workspace deployment completed successfully[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Workspace deployment failed: {e}[/red]")
            return False
    
    def deploy_jobs(self) -> bool:
        """Deploy Databricks Jobs (REPEATABLE)"""
        console.print("\n" + "="*60)
        console.print("[bold magenta]⚙️  STEP 2: Deploying Databricks Jobs[/bold magenta]")
        console.print("="*60)
        console.print("[dim]This step creates/updates workflow definitions[/dim]\n")
        
        try:
            deployer = JobDeployer(self.config)
            
            # Get workflows directory
            workflows_dir = Path(__file__).parent.parent / "workflows"
            if not workflows_dir.exists():
                console.print(f"[red]❌ Workflows directory not found: {workflows_dir}[/red]")
                return False
            
            result = deployer.deploy_all(workflows_dir)
            
            if result["summary"]["error"] > 0:
                console.print("[yellow]⚠️  Jobs deployment completed with errors[/yellow]")
                return False
            
            console.print("[green]✅ Jobs deployment completed successfully[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Jobs deployment failed: {e}[/red]")
            return False
    
    def validate_deployment(self) -> bool:
        """Validate the deployment (VERIFICATION)"""
        console.print("\n" + "="*60)
        console.print("[bold magenta]🔍 STEP 3: Validating Deployment[/bold magenta]")
        console.print("="*60)
        console.print("[dim]This step verifies schemas, tables, notebooks, and jobs[/dim]\n")
        
        try:
            validator = DeploymentValidator(self.config)
            result = validator.validate_all()
            
            if result["failed"] > 0:
                console.print("[yellow]⚠️  Validation completed with failures[/yellow]")
                return False
            
            console.print("[green]✅ Validation completed successfully[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Validation failed: {e}[/red]")
            return False
    
    def deploy_all(self, skip_validation: bool = False, skip_bootstrap: bool = False) -> bool:
        """Execute full deployment"""
        self.print_banner()
        
        # Track overall success
        all_success = True
        
        # Step 0: Bootstrap infrastructure (unless skipped)
        if not skip_bootstrap:
            if not self.bootstrap_infrastructure():
                all_success = False
                if not self.config.force_deploy:
                    console.print("\n[red]❌ Deployment aborted due to bootstrap failure[/red]")
                    console.print("[dim]Hint: Use --skip-bootstrap if schemas already exist[/dim]")
                    return False
        else:
            console.print("\n[yellow]⚠️  Skipping infrastructure bootstrap (--skip-bootstrap)[/yellow]")
            console.print("[dim]Assuming schemas, tables, and metadata already exist[/dim]")
        
        # Step 1: Deploy workspace assets
        if not self.deploy_workspace():
            all_success = False
            if not self.config.force_deploy:
                console.print("\n[red]❌ Deployment aborted due to workspace deployment failure[/red]")
                return False
        
        # Step 2: Deploy jobs
        if not self.deploy_jobs():
            all_success = False
            if not self.config.force_deploy:
                console.print("\n[red]❌ Deployment aborted due to jobs deployment failure[/red]")
                return False
        
        # Step 3: Validate (optional)
        if not skip_validation:
            if not self.validate_deployment():
                all_success = False
        
        # Final summary
        console.print("\n" + "="*60)
        console.print("[bold]🏁 DEPLOYMENT COMPLETE[/bold]")
        console.print("="*60)
        
        if all_success:
            console.print(Panel(
                "[bold green]🎉 All deployment steps completed successfully![/bold green]\n\n"
                "[bold]Next Steps:[/bold]\n"
                "  1. Configure and schedule: [cyan]LMIP_Daily_Ingestion[/cyan]\n"
                "  2. Run your first data ingestion job\n"
                "  3. Monitor pipeline runs in the audit tables\n"
                "  4. Check the publish schema for consumer-ready datasets\n\n"
                "[dim]Deployment Summary:[/dim]\n"
                "  • Infrastructure: Bootstrapped\n"
                "  • Workspace: Deployed\n"
                "  • Jobs: Created/Updated\n"
                "  • Validation: Passed",
                border_style="green"
            ))
        else:
            console.print(Panel(
                "[bold yellow]⚠️  Deployment completed with some issues.[/bold yellow]\n\n"
                "Review the logs above for details.\n\n"
                "[dim]Troubleshooting:[/dim]\n"
                "  • Check error messages in each step\n"
                "  • Run: python deployment/validate_deployment.py\n"
                "  • Review: LMIP/deployment/README.md",
                border_style="yellow"
            ))
        
        console.print("="*60)
        
        return all_success


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deploy complete LMIP project to Databricks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full deployment (bootstrap + workspace + jobs + validation)
  python deploy_all.py
  
  # Dry run to preview changes
  python deploy_all.py --dry-run
  
  # Deploy with updates to existing resources
  python deploy_all.py --update
  
  # Deploy without validation
  python deploy_all.py --skip-validation
  
  # Deploy without bootstrap (schemas/tables already exist)
  python deploy_all.py --skip-bootstrap
  
  # Force deploy even if errors occur
  python deploy_all.py --force

Deployment Phases:
  0. Bootstrap (ONE-TIME):  Create schemas, tables, seed metadata
  1. Workspace (REPEATABLE): Upload notebooks, SQL files, scripts
  2. Jobs (REPEATABLE):      Create/update Databricks Jobs
  3. Validation (VERIFY):    Check all components deployed correctly

Common Workflows:
  • First-time setup:     python deploy_all.py
  • Code update:          python deploy_all.py --skip-bootstrap --update
  • Full reset + deploy:  python reset_environment.py --full --confirm
                          python deploy_all.py
"""
    )
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without deploying")
    parser.add_argument("--update", action="store_true",
                       help="Update existing resources (notebooks, jobs)")
    parser.add_argument("--force", action="store_true",
                       help="Continue deployment even if errors occur")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip validation step after deployment")
    parser.add_argument("--skip-bootstrap", action="store_true",
                       help="Skip infrastructure bootstrap (schemas/tables already exist)")
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config()
    config.dry_run = args.dry_run or config.dry_run
    config.update_existing = args.update or config.update_existing
    config.force_deploy = args.force
    
    # Validate configuration
    if not config.validate():
        console.print("[red]❌ Invalid configuration. Please check your .env file.[/red]")
        return 1
    
    # Create deployer and run
    deployer = FullDeployer(config)
    success = deployer.deploy_all(
        skip_validation=args.skip_validation,
        skip_bootstrap=args.skip_bootstrap
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
