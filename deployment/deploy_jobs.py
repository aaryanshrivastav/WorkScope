"""
Deploy Databricks Jobs from workflow JSON definitions

This module reads workflow JSON files and creates/updates Databricks Jobs.
Supports both JSON and YAML workflow definitions.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import os
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import JobSettings

from core import get_config, DeploymentConfig, DeploymentLogger, DatabricksClientWrapper

load_dotenv()


class JobDeployer:
    """Deploy workflow definitions to Databricks Jobs"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.w = WorkspaceClient(
            host=os.getenv("DATABRICKS_HOST"),
            token=os.getenv("DATABRICKS_TOKEN")
        )
        self.db = DatabricksClientWrapper()
        self.logger = DeploymentLogger()
        
    def get_workflow_files(self, workflow_dir: Path) -> List[Path]:
        """Find all workflow definition files (JSON and YAML)"""
        json_files = list(workflow_dir.glob("*.json"))
        yaml_files = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))
        
        # Filter out documentation files
        all_files = json_files + yaml_files
        return [f for f in all_files if not f.name.startswith("README")]
    
    def load_workflow_definition(self, filepath: Path) -> Dict:
        """Load and parse a workflow file (JSON or YAML)"""
        with open(filepath, 'r') as f:
            if filepath.suffix in ['.yml', '.yaml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def normalize_notebook_path(self, path: str) -> str:
        """Ensure notebook path is in correct format"""
        # Remove /Workspace prefix if present
        if path.startswith("/Workspace"):
            path = path.replace("/Workspace", "")
        # Ensure it starts with /
        if not path.startswith("/"):
            path = "/" + path
        return path
    
    def substitute_parameters(self, workflow: Dict) -> Dict:
        """Substitute configuration parameters in workflow definition"""
        workflow_str = json.dumps(workflow)
        
        # Replace common placeholders
        replacements = {
            "${catalog}": self.config.catalog,
            "${workspace_root}": self.config.workspace_root,
            "${notification_email}": self.config.notification_email,
        }
        
        for placeholder, value in replacements.items():
            workflow_str = workflow_str.replace(placeholder, value)
        
        return json.loads(workflow_str)
    
    def deploy_workflow(self, workflow_file: Path) -> Dict:
        """Deploy a single workflow definition to Databricks"""
        result = {
            "file": workflow_file.name,
            "status": "unknown",
            "job_id": None,
            "job_name": None,
            "error": None
        }
        
        try:
            # Load workflow definition
            workflow = self.load_workflow_definition(workflow_file)
            workflow = self.substitute_parameters(workflow)
            
            job_name = workflow.get("name", workflow_file.stem)
            result["job_name"] = job_name
            
            self.logger.info(f"\n📋 Processing: {job_name} ({workflow_file.name})")
            
            # Normalize notebook paths
            for task in workflow.get("tasks", []):
                if "notebook_task" in task:
                    original_path = task["notebook_task"]["notebook_path"]
                    normalized_path = self.normalize_notebook_path(original_path)
                    task["notebook_task"]["notebook_path"] = normalized_path
                    if normalized_path != original_path:
                        self.logger.info(f"  📝 Normalized path: {normalized_path}")
            
            # Check if job already exists using core utility
            existing_job_id = self.db.get_job_id(job_name)
            
            if existing_job_id and not self.config.update_existing:
                result["status"] = "skipped"
                result["job_id"] = existing_job_id
                self.logger.item_warning(f"Job already exists (ID: {existing_job_id}). Use --update to modify.")
                return result
            
            if self.config.dry_run:
                result["status"] = "dry_run"
                self.logger.info(f"  🔍 DRY RUN: Would {'update' if existing_job_id else 'create'} job")
                self.logger.info(f"  📊 Tasks: {len(workflow.get('tasks', []))}")
                return result
            
            # Create or update job
            if existing_job_id and self.config.update_existing:
                self.logger.warning(f"  🔄 Updating existing job (ID: {existing_job_id})...")
                self.w.jobs.reset(job_id=existing_job_id, new_settings=workflow)
                result["status"] = "updated"
                result["job_id"] = existing_job_id
                self.logger.item_success("Updated successfully")
            else:
                self.logger.info(f"  🚀 Creating new job...")
                created_job = self.w.jobs.create(**workflow)
                result["status"] = "created"
                result["job_id"] = created_job.job_id
                self.logger.item_success(f"Created successfully (ID: {created_job.job_id})")
            
        except FileNotFoundError:
            result["status"] = "error"
            result["error"] = f"File not found: {workflow_file}"
            self.logger.item_error(result['error'])
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            result["status"] = "error"
            result["error"] = f"Invalid format: {e}"
            self.logger.item_error(result['error'])
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.logger.item_error(result['error'])
        
        return result
    
    def deploy_all(self, workflow_dir: Path, specific_workflow: Optional[str] = None) -> Dict:
        """Deploy all workflows or a specific workflow"""
        workflow_files = self.get_workflow_files(workflow_dir)
        
        if specific_workflow:
            workflow_files = [f for f in workflow_files if f.name == specific_workflow]
            if not workflow_files:
                self.logger.error(f"Workflow file not found: {specific_workflow}")
                return {"summary": {"total": 0, "error": 1}}
        
        if not workflow_files:
            self.logger.error("No workflow files found in directory")
            return {"summary": {"total": 0}}
        
        self.logger.info(f"\n🔍 Found {len(workflow_files)} workflow file(s)")
        
        results = []
        for workflow_file in sorted(workflow_files):
            result = self.deploy_workflow(workflow_file)
            results.append(result)
        
        # Summary
        summary = {
            "total": len(results),
            "created": sum(1 for r in results if r["status"] == "created"),
            "updated": sum(1 for r in results if r["status"] == "updated"),
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
            "error": sum(1 for r in results if r["status"] == "error"),
            "dry_run": sum(1 for r in results if r["status"] == "dry_run")
        }
        
        # Print summary table
        self._print_summary(summary, results)
        
        return {"results": results, "summary": summary}
    
    def _print_summary(self, summary: Dict, results: List[Dict]):
        """Print deployment summary as a rich table"""
        self.logger.section("DEPLOYMENT SUMMARY")
        
        # Build table data
        headers = ["Workflow", "Status", "Job ID"]
        rows = []
        
        for result in results:
            status_emoji = {
                "created": "✅ Created",
                "updated": "🔄 Updated",
                "skipped": "⏭️  Skipped",
                "error": "❌ Error",
                "dry_run": "🔍 Dry Run"
            }.get(result["status"], "❓ Unknown")
            
            job_id = str(result["job_id"]) if result["job_id"] else "-"
            rows.append([result["job_name"] or result["file"], status_emoji, job_id])
        
        self.logger.table(headers, rows)
        
        self.logger.info(f"\nTotal workflows:  {summary['total']}")
        self.logger.item_success(f"Created:       {summary['created']}")
        self.logger.warning(f"🔄 Updated:       {summary['updated']}")
        self.logger.info(f"⏭️  Skipped:       {summary['skipped']}")
        self.logger.item_error(f"Errors:        {summary['error']}")
        if summary['dry_run'] > 0:
            self.logger.info(f"🔍 Dry run:       {summary['dry_run']}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deploy workflow definitions to Databricks Jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--update", action="store_true", 
                       help="Update existing jobs if they already exist")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without creating/updating jobs")
    parser.add_argument("--workflow", type=str,
                       help="Deploy only a specific workflow file (e.g., 'init.json')")
    parser.add_argument("--workflow-dir", type=str,
                       help="Directory containing workflow files (default: ../workflows)")
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config()
    config.dry_run = args.dry_run or config.dry_run
    config.update_existing = args.update or config.update_existing
    
    # Validate configuration
    if not config.validate():
        return 1
    
    # Get workflow directory
    if args.workflow_dir:
        workflow_dir = Path(args.workflow_dir).resolve()
    else:
        workflow_dir = Path(config.workspace_root) / config.workflows_dir
        # If running locally, look for workflows relative to script
        if not workflow_dir.exists():
            workflow_dir = Path(__file__).parent.parent / "workflows"
    
    if not workflow_dir.exists():
        logger = DeploymentLogger()
        logger.error(f"Workflow directory not found: {workflow_dir}")
        return 1
    
    logger = DeploymentLogger()
    logger.info(f"📁 Workflow directory: {workflow_dir}")
    
    # Print configuration
    config.print_summary()
    
    # Create deployer and run
    deployer = JobDeployer(config)
    result = deployer.deploy_all(workflow_dir, args.workflow)
    
    # Exit code based on results
    if result["summary"].get("error", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
