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

from core import get_config, DeploymentConfig, DeploymentLogger
from deploy_workspace import WorkspaceDeployer
from deploy_jobs import JobDeployer
from validate_deployment import DeploymentValidator
from bootstrap import LMIPBootstrapper


class FullDeployer:
    """Orchestrate complete LMIP deployment"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.logger = DeploymentLogger()
        
    def print_banner(self):
        """Print deployment banner"""
        self.logger.banner(
            "LMIP DEPLOYMENT ORCHESTRATOR\n\n"
            "Labor Market Intelligence Platform - Full Deployment"
        )
        self.config.print_summary()
    
    def bootstrap_infrastructure(self) -> bool:
        """Bootstrap LMIP infrastructure: schemas, tables, and metadata (ONE-TIME)"""
        self.logger.section("🚀 STEP 0: Bootstrapping Infrastructure")
        self.logger.info("This step creates Unity Catalog schemas, tables, and seeds metadata\n")
        
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
                self.logger.item_success("Infrastructure bootstrap completed successfully")
            else:
                self.logger.item_warning("Infrastructure bootstrap completed with warnings")
            
            return success
            
        except Exception as e:
            self.logger.item_error(f"Infrastructure bootstrap failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def deploy_workspace(self) -> bool:
        """Deploy workspace assets (REPEATABLE)"""
        self.logger.section("📁 STEP 1: Deploying Workspace Assets")
        self.logger.info("This step uploads notebooks, SQL files, and helper scripts\n")
        
        try:
            deployer = WorkspaceDeployer(self.config)
            
            # Get notebooks directory
            notebooks_dir = Path(__file__).parent.parent / "notebooks"
            if not notebooks_dir.exists():
                self.logger.error(f"Notebooks directory not found: {notebooks_dir}")
                return False
            
            workspace_root = f"{self.config.workspace_root}/notebooks"
            result = deployer.deploy_directory(notebooks_dir, workspace_root)
            
            if result["summary"]["error"] > 0:
                self.logger.item_warning("Workspace deployment completed with errors")
                return False
            
            self.logger.item_success("Workspace deployment completed successfully")
            return True
            
        except Exception as e:
            self.logger.item_error(f"Workspace deployment failed: {e}")
            return False
    
    def deploy_jobs(self) -> bool:
        """Deploy Databricks Jobs (REPEATABLE)"""
        self.logger.section("⚙️  STEP 2: Deploying Databricks Jobs")
        self.logger.info("This step creates/updates workflow definitions\n")
        
        try:
            deployer = JobDeployer(self.config)
            
            # Get workflows directory
            workflows_dir = Path(__file__).parent.parent / "workflows"
            if not workflows_dir.exists():
                self.logger.error(f"Workflows directory not found: {workflows_dir}")
                return False
            
            result = deployer.deploy_all(workflows_dir)
            
            if result["summary"]["error"] > 0:
                self.logger.item_warning("Jobs deployment completed with errors")
                return False
            
            self.logger.item_success("Jobs deployment completed successfully")
            return True
            
        except Exception as e:
            self.logger.item_error(f"Jobs deployment failed: {e}")
            return False
    
    def validate_deployment(self) -> bool:
        """Validate the deployment (VERIFICATION)"""
        self.logger.section("🔍 STEP 3: Validating Deployment")
        self.logger.info("This step verifies schemas, tables, notebooks, and jobs\n")
        
        try:
            validator = DeploymentValidator(self.config)
            result = validator.validate_all()
            
            if result["failed"] > 0:
                self.logger.item_warning("Validation completed with failures")
                return False
            
            self.logger.item_success("Validation completed successfully")
            return True
            
        except Exception as e:
            self.logger.item_error(f"Validation failed: {e}")
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
                    self.logger.error("\n❌ Deployment aborted due to bootstrap failure")
                    self.logger.info("Hint: Use --skip-bootstrap if schemas already exist")
                    return False
        else:
            self.logger.warning("\n⚠️  Skipping infrastructure bootstrap (--skip-bootstrap)")
            self.logger.info("Assuming schemas, tables, and metadata already exist")
        
        # Step 1: Deploy workspace assets
        if not self.deploy_workspace():
            all_success = False
            if not self.config.force_deploy:
                self.logger.error("\n❌ Deployment aborted due to workspace deployment failure")
                return False
        
        # Step 2: Deploy jobs
        if not self.deploy_jobs():
            all_success = False
            if not self.config.force_deploy:
                self.logger.error("\n❌ Deployment aborted due to jobs deployment failure")
                return False
        
        # Step 3: Validate (optional)
        if not skip_validation:
            if not self.validate_deployment():
                all_success = False
        
        # Final summary
        self.logger.section("DEPLOYMENT COMPLETE")
        
        if all_success:
            self.logger.panel(
                "🎉 All deployment steps completed successfully!\n\n"
                "Next Steps:\n"
                "  1. Configure and schedule: LMIP_Daily_Ingestion\n"
                "  2. Run your first data ingestion job\n"
                "  3. Monitor pipeline runs in the audit tables\n"
                "  4. Check the publish schema for consumer-ready datasets\n\n"
                "Deployment Summary:\n"
                "  • Infrastructure: Bootstrapped\n"
                "  • Workspace: Deployed\n"
                "  • Jobs: Created/Updated\n"
                "  • Validation: Passed",
                title="SUCCESS",
                style="green"
            )
        else:
            self.logger.panel(
                "⚠️  Deployment completed with some issues.\n\n"
                "Review the logs above for details.\n\n"
                "Troubleshooting:\n"
                "  • Check error messages in each step\n"
                "  • Run: python deployment/validate_deployment.py\n"
                "  • Review: LMIP/deployment/README.md",
                title="WARNING",
                style="yellow"
            )
        
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
    logger = DeploymentLogger()
    if not config.validate():
        logger.error("Invalid configuration. Please check your .env file.")
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
