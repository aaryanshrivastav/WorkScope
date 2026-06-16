"""
Configuration management for LMIP deployment

Centralized configuration loading from environment variables with validation.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


@dataclass
class DeploymentConfig:
    """Central configuration for LMIP deployment"""
    
    # Databricks connection
    databricks_host: str
    databricks_token: Optional[str] = None
    databricks_warehouse_id: Optional[str] = None
    
    # Workspace paths
    workspace_root: str = "/Users/aaryan.shrivastav1403@gmail.com/LMIP"
    notebooks_dir: str = "notebooks"
    workflows_dir: str = "workflows"
    
    # Unity Catalog settings
    catalog: str = "workspace"
    bronze_schema: str = "bronze"
    silver_schema: str = "silver"
    intermediate_schema: str = "intermediate"
    gold_schema: str = "gold"
    reporting_schema: str = "reporting"
    metadata_schema: str = "metadata"
    audit_schema: str = "audit"
    quarantine_schema: str = "quarantine"
    publish_schema: str = "publish"
    
    # Deployment settings
    dry_run: bool = False
    update_existing: bool = False
    force_deploy: bool = False
    
    # Notification settings
    notification_email: str = "aaryan.shrivastav1403@gmail.com"
    
    # Compute settings
    default_cluster_id: Optional[str] = None
    use_serverless: bool = True
    
    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "DeploymentConfig":
        """
        Load configuration from environment variables.
        
        Args:
            env_file: Optional path to .env file (default: deployment/.env)
        
        Returns:
            DeploymentConfig instance
        """
        # Load .env file if it exists
        if env_file is None:
            env_file = Path(__file__).parent.parent / ".env"
        
        if env_file.exists():
            load_dotenv(env_file)
        
        return cls(
            databricks_host=os.getenv("DATABRICKS_HOST", ""),
            databricks_token=os.getenv("DATABRICKS_TOKEN"),
            databricks_warehouse_id=os.getenv("DATABRICKS_WAREHOUSE_ID"),
            workspace_root=os.getenv("WORKSPACE_ROOT", "/Users/aaryan.shrivastav1403@gmail.com/LMIP"),
            catalog=os.getenv("CATALOG", "workspace"),
            bronze_schema=os.getenv("BRONZE_SCHEMA", "bronze"),
            silver_schema=os.getenv("SILVER_SCHEMA", "silver"),
            intermediate_schema=os.getenv("INTERMEDIATE_SCHEMA", "intermediate"),
            gold_schema=os.getenv("GOLD_SCHEMA", "gold"),
            reporting_schema=os.getenv("REPORTING_SCHEMA", "reporting"),
            metadata_schema=os.getenv("METADATA_SCHEMA", "metadata"),
            audit_schema=os.getenv("AUDIT_SCHEMA", "audit"),
            quarantine_schema=os.getenv("QUARANTINE_SCHEMA", "quarantine"),
            publish_schema=os.getenv("PUBLISH_SCHEMA", "publish"),
            notification_email=os.getenv("NOTIFICATION_EMAIL", "aaryan.shrivastav1403@gmail.com"),
            default_cluster_id=os.getenv("DEFAULT_CLUSTER_ID"),
            use_serverless=os.getenv("USE_SERVERLESS", "true").lower() == "true",
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
            update_existing=os.getenv("UPDATE_EXISTING", "false").lower() == "true",
            force_deploy=os.getenv("FORCE_DEPLOY", "false").lower() == "true"
        )
    
    def get_full_path(self, relative_path: str) -> str:
        """Get full workspace path for a relative path"""
        return f"{self.workspace_root}/{relative_path}".replace("//", "/")
    
    def get_table_name(self, schema: str, table: str) -> str:
        """Get fully qualified table name"""
        return f"{self.catalog}.{schema}.{table}"
    
    def get_schema_name(self, schema: str) -> str:
        """Get fully qualified schema name"""
        return f"{self.catalog}.{schema}"
    
    def list_all_schemas(self) -> list[str]:
        """Get list of all LMIP schemas"""
        return [
            self.metadata_schema,
            self.bronze_schema,
            self.silver_schema,
            self.intermediate_schema,
            self.gold_schema,
            self.reporting_schema,
            self.audit_schema,
            self.publish_schema,
            self.quarantine_schema
        ]
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if valid, False otherwise
        """
        errors = []
        
        if not self.databricks_host:
            errors.append("DATABRICKS_HOST is required")
        
        if not self.workspace_root:
            errors.append("WORKSPACE_ROOT is required")
        
        if not self.catalog:
            errors.append("CATALOG is required")
        
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def print_summary(self):
        """Print configuration summary"""
        print("="*60)
        print("📋 DEPLOYMENT CONFIGURATION")
        print("="*60)
        print(f"Databricks Host:    {self.databricks_host}")
        print(f"Workspace Root:     {self.workspace_root}")
        print(f"Catalog:            {self.catalog}")
        print(f"Schemas:            {len(self.list_all_schemas())} schemas")
        print(f"                    ({', '.join(self.list_all_schemas())})")
        print(f"Notification Email: {self.notification_email}")
        print(f"Use Serverless:     {self.use_serverless}")
        print(f"Dry Run:            {self.dry_run}")
        print(f"Update Existing:    {self.update_existing}")
        print("="*60)


# Singleton instance
_config: Optional[DeploymentConfig] = None


def get_config(env_file: Optional[Path] = None) -> DeploymentConfig:
    """
    Get or create the global configuration instance.
    
    Args:
        env_file: Optional path to .env file
    
    Returns:
        DeploymentConfig instance
    """
    global _config
    if _config is None:
        _config = DeploymentConfig.from_env(env_file)
    return _config


def reset_config():
    """Reset the global configuration (useful for testing)"""
    global _config
    _config = None
