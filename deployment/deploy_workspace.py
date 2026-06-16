"""
Deploy workspace assets (notebooks, files, directories)

This module handles deployment of notebooks, Python files, SQL files,
and other workspace assets to Databricks.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ImportFormat, Language

from core import get_config, DeploymentConfig, DeploymentLogger

load_dotenv()


class WorkspaceDeployer:
    """Deploy workspace assets to Databricks"""
    
    # File extension to language mapping
    LANGUAGE_MAP = {
        '.py': Language.PYTHON,
        '.sql': Language.SQL,
        '.scala': Language.SCALA,
        '.r': Language.R,
        '.ipynb': Language.PYTHON,  # Notebooks
    }
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.w = WorkspaceClient(
            host=os.getenv("DATABRICKS_HOST"),
            token=os.getenv("DATABRICKS_TOKEN")
        )
        self.logger = DeploymentLogger()
        
    def get_language(self, filepath: Path) -> Optional[Language]:
        """Determine language from file extension"""
        return self.LANGUAGE_MAP.get(filepath.suffix.lower())
    
    def should_deploy(self, filepath: Path) -> bool:
        """Check if file should be deployed"""
        # Skip hidden files, deployment files, and certain extensions
        skip_patterns = [
            '.git', '__pycache__', '.pyc', '.env', 
            '.md', '.txt', '.json', '.yml', '.yaml',
            'deployment/', '.gitkeep'
        ]
        
        path_str = str(filepath)
        for pattern in skip_patterns:
            if pattern in path_str:
                return False
        
        # Only deploy files with recognized extensions
        return self.get_language(filepath) is not None
    
    def ensure_directory(self, workspace_path: str):
        """Ensure directory exists in workspace"""
        try:
            self.w.workspace.mkdirs(workspace_path)
        except Exception as e:
            self.logger.item_warning(f"Could not create directory {workspace_path}: {e}")
    
    def deploy_file(self, local_path: Path, workspace_path: str) -> Dict:
        """Deploy a single file to workspace"""
        result = {
            "local_path": str(local_path),
            "workspace_path": workspace_path,
            "status": "unknown",
            "error": None
        }
        
        try:
            # Read file content
            with open(local_path, 'rb') as f:
                content = f.read()
            
            # Determine format
            is_notebook = local_path.suffix == '.ipynb'
            import_format = ImportFormat.AUTO
            language = self.get_language(local_path)
            
            if self.config.dry_run:
                result["status"] = "dry_run"
                self.logger.info(f"  🔍 Would deploy: {workspace_path}")
                return result
            
            # Import file to workspace
            self.w.workspace.import_(
                path=workspace_path,
                format=import_format,
                language=language,
                content=content,
                overwrite=self.config.update_existing
            )
            
            result["status"] = "deployed"
            self.logger.item_success(f"Deployed: {workspace_path}")
            
        except FileNotFoundError:
            result["status"] = "error"
            result["error"] = f"Local file not found: {local_path}"
            self.logger.item_error(result['error'])
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            self.logger.item_error(f"Error deploying {workspace_path}: {e}")
        
        return result
    
    def deploy_directory(self, local_dir: Path, workspace_root: str) -> Dict:
        """Deploy all files in a directory to workspace"""
        self.logger.info(f"\n📁 Deploying directory: {local_dir}")
        
        results = []
        
        # Walk through directory
        for root, dirs, files in os.walk(local_dir):
            root_path = Path(root)
            
            # Calculate relative path from local_dir
            relative_path = root_path.relative_to(local_dir)
            workspace_dir = f"{workspace_root}/{relative_path}".replace("//", "/")
            
            # Ensure workspace directory exists
            if not self.config.dry_run:
                self.ensure_directory(workspace_dir)
            
            # Deploy each file
            for filename in files:
                local_file = root_path / filename
                
                if not self.should_deploy(local_file):
                    self.logger.info(f"  ⏭️  Skipping: {local_file.name}")
                    continue
                
                workspace_file = f"{workspace_dir}/{filename}".replace("//", "/")
                result = self.deploy_file(local_file, workspace_file)
                results.append(result)
        
        return self._summarize_results(results)
    
    def deploy_notebooks(self, notebooks_dir: Optional[Path] = None) -> Dict:
        """Deploy all notebooks from notebooks directory"""
        if notebooks_dir is None:
            # Use config to find notebooks directory
            notebooks_dir = Path(self.config.workspace_root) / self.config.notebooks_dir
            # If running locally, look relative to script
            if not notebooks_dir.exists():
                notebooks_dir = Path(__file__).parent.parent / "notebooks"
        
        if not notebooks_dir.exists():
            self.logger.error(f"Notebooks directory not found: {notebooks_dir}")
            return {"summary": {"total": 0, "error": 1}}
        
        workspace_root = f"{self.config.workspace_root}/notebooks"
        return self.deploy_directory(notebooks_dir, workspace_root)
    
    def _summarize_results(self, results: List[Dict]) -> Dict:
        """Summarize deployment results"""
        summary = {
            "total": len(results),
            "deployed": sum(1 for r in results if r["status"] == "deployed"),
            "skipped": sum(1 for r in results if r["status"] == "skipped"),
            "error": sum(1 for r in results if r["status"] == "error"),
            "dry_run": sum(1 for r in results if r["status"] == "dry_run")
        }
        
        # Print summary
        self.logger.section("DEPLOYMENT SUMMARY")
        self.logger.info(f"Total files:      {summary['total']}")
        self.logger.item_success(f"Deployed:      {summary['deployed']}")
        self.logger.info(f"⏭️  Skipped:       {summary['skipped']}")
        self.logger.item_error(f"Errors:        {summary['error']}")
        if summary['dry_run'] > 0:
            self.logger.info(f"🔍 Dry run:       {summary['dry_run']}")
        
        return {"results": results, "summary": summary}


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deploy workspace assets to Databricks",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--update", action="store_true",
                       help="Overwrite existing files")
    parser.add_argument("--dry-run", action="store_true",
                       help="Preview changes without deploying")
    parser.add_argument("--source-dir", type=str,
                       help="Source directory to deploy (default: ../notebooks)")
    parser.add_argument("--target-path", type=str,
                       help="Target workspace path (default: from config)")
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config()
    config.dry_run = args.dry_run or config.dry_run
    config.update_existing = args.update or config.update_existing
    
    # Validate configuration
    if not config.validate():
        return 1
    
    # Print configuration
    config.print_summary()
    
    # Create deployer
    deployer = WorkspaceDeployer(config)
    logger = DeploymentLogger()
    
    # Get source directory
    if args.source_dir:
        source_dir = Path(args.source_dir).resolve()
    else:
        source_dir = Path(__file__).parent.parent / "notebooks"
    
    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return 1
    
    # Get target path
    target_path = args.target_path or f"{config.workspace_root}/notebooks"
    
    logger.info(f"📁 Source directory: {source_dir}")
    logger.info(f"🎯 Target path:     {target_path}")
    
    # Deploy
    result = deployer.deploy_directory(source_dir, target_path)
    
    # Exit code based on results
    if result["summary"].get("error", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
