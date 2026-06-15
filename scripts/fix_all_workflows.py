"""
Batch Update Script: Fix Pipeline Logging & Notifications in All Workflows

This script:
1. Adds/fixes Log_Pipeline_Execution tasks with standardized parameters
2. Adds Notify_On_Failure tasks to all workflows
3. Ensures all tasks use correct paths and run_if clauses

Usage:
    python fix_all_workflows.py --dir workflows [--dry-run]
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
import argparse


def create_log_task(workflow_name: str, depends_on_tasks: List[str]) -> Dict[str, Any]:
    """Create standardized Log_Pipeline_Execution task"""
    return {
        "task_key": "Log_Pipeline_Execution",
        "depends_on": [{"task_key": task} for task in depends_on_tasks],
        "run_if": "ALL_DONE",
        "notebook_task": {
            "notebook_path": "/Workspace/Users/aaryan.shrivastav1403@gmail.com/LMIP/notebooks/audit/log_pipeline_run",
            "source": "WORKSPACE",
            "base_parameters": {
                "pipeline_name": workflow_name,
                "run_id": "{{run_id}}",
                "status": "{{tasks." + depends_on_tasks[0] + ".state}}",
                "start_time": "{{start_time}}",
                "rows_read": "0",
                "rows_written": "0",
                "catalog": "workspace",
                "schema": "audit"
            }
        },
        "timeout_seconds": 600,
        "max_retries": 2,
        "email_notifications": {},
        "environment_key": "Default"
    }


def create_notification_task(workflow_name: str, depends_on_tasks: List[str]) -> Dict[str, Any]:
    """Create standardized Notify_On_Failure task"""
    return {
        "task_key": "Notify_On_Failure",
        "depends_on": [{"task_key": task} for task in depends_on_tasks],
        "run_if": "AT_LEAST_ONE_FAILED",
        "notebook_task": {
            "notebook_path": "/Workspace/Users/aaryan.shrivastav1403@gmail.com/LMIP/notebooks/audit/audit_notification_dispatch",
            "source": "WORKSPACE",
            "base_parameters": {
                "notification_type": "critical_alert",
                "alert_severity": "HIGH",
                "alert_title": f"{workflow_name} Pipeline Failed",
                "alert_message": f"Pipeline {workflow_name} (Run ID: {{{{run_id}}}}) encountered failures. Check audit logs and investigate immediately.",
                "alert_context": "{\\\"workflow_name\\\": \\\"" + workflow_name + "\\\", \\\"run_id\\\": \\\"{{run_id}}\\\", \\\"run_page_url\\\": \\\"{{run_page_url}}\\\"}",
                "recipient_list": "aaryan.shrivastav1403@gmail.com,data-ops-team@company.com",
                "channel": "email"
            }
        },
        "timeout_seconds": 600,
        "max_retries": 2,
        "email_notifications": {},
        "environment_key": "Default"
    }


def get_leaf_tasks(workflow: Dict[str, Any]) -> List[str]:
    """Identify leaf tasks (tasks with no dependents)"""
    tasks = workflow.get("tasks", [])
    all_tasks = {task["task_key"] for task in tasks}
    
    # Collect all tasks that others depend on
    dependency_set = set()
    for task in tasks:
        for dep in task.get("depends_on", []):
            dependency_set.add(dep["task_key"])
    
    # Leaf tasks = tasks that no one depends on
    leaf_tasks = all_tasks - dependency_set
    
    # Filter out Log/Notify tasks
    leaf_tasks = [t for t in leaf_tasks if not t.startswith("Log_") and not t.startswith("Notify_")]
    
    return list(leaf_tasks)


def fix_workflow(workflow_path: Path, dry_run: bool = False) -> Dict[str, Any]:
    """Fix a single workflow file"""
    print(f"\n{'='*80}")
    print(f"Processing: {workflow_path.name}")
    print(f"{'='*80}")
    
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    workflow_name = workflow.get("name", "Unknown")
    tasks = workflow.get("tasks", [])
    
    changes = {
        "file": workflow_path.name,
        "workflow_name": workflow_name,
        "log_task_fixed": False,
        "log_task_added": False,
        "notification_task_added": False,
        "errors": []
    }
    
    # Find existing Log and Notify tasks
    log_task_idx = None
    notif_task_idx = None
    
    for idx, task in enumerate(tasks):
        if "Log" in task["task_key"] and "audit" in task.get("notebook_task", {}).get("notebook_path", ""):
            log_task_idx = idx
        if "Notify" in task["task_key"] or "notification" in task["task_key"].lower():
            notif_task_idx = idx
    
    # Identify leaf tasks for dependency
    leaf_tasks = get_leaf_tasks(workflow)
    
    if not leaf_tasks:
        changes["errors"].append("No leaf tasks identified - manual review needed")
        print(f"⚠️  WARNING: Could not identify leaf tasks")
        return changes
    
    print(f"Leaf tasks identified: {', '.join(leaf_tasks)}")
    
    # Fix or add Log task
    if log_task_idx is not None:
        print(f"✓ Found existing Log task at index {log_task_idx}")
        
        # Check if path is correct
        current_path = tasks[log_task_idx].get("notebook_task", {}).get("notebook_path", "")
        if "log_pipeline_runs" in current_path:  # Wrong path (plural)
            print(f"  ⚠️  Fixing incorrect path: {current_path}")
            tasks[log_task_idx]["notebook_task"]["notebook_path"] = current_path.replace("log_pipeline_runs", "log_pipeline_run")
            changes["log_task_fixed"] = True
        
        # Ensure all required parameters
        params = tasks[log_task_idx].get("notebook_task", {}).get("base_parameters", {})
        required_params = ["pipeline_name", "run_id", "status", "start_time", "rows_read", "rows_written", "catalog", "schema"]
        
        missing_params = [p for p in required_params if p not in params]
        if missing_params:
            print(f"  ⚠️  Adding missing parameters: {', '.join(missing_params)}")
            
            # Add default values for missing params
            if "pipeline_name" not in params:
                params["pipeline_name"] = workflow_name
            if "run_id" not in params:
                params["run_id"] = "{{run_id}}"
            if "status" not in params:
                params["status"] = "{{tasks." + leaf_tasks[0] + ".state}}"
            if "start_time" not in params:
                params["start_time"] = "{{start_time}}"
            if "rows_read" not in params:
                params["rows_read"] = "0"
            if "rows_written" not in params:
                params["rows_written"] = "0"
            if "catalog" not in params:
                params["catalog"] = "workspace"
            if "schema" not in params:
                params["schema"] = "audit"
            
            tasks[log_task_idx]["notebook_task"]["base_parameters"] = params
            changes["log_task_fixed"] = True
        
        # Ensure run_if is ALL_DONE
        if tasks[log_task_idx].get("run_if") != "ALL_DONE":
            print(f"  ⚠️  Fixing run_if: {tasks[log_task_idx].get('run_if')} → ALL_DONE")
            tasks[log_task_idx]["run_if"] = "ALL_DONE"
            changes["log_task_fixed"] = True
    
    else:
        print(f"✗ No Log task found - adding new one")
        log_task = create_log_task(workflow_name, leaf_tasks)
        tasks.append(log_task)
        changes["log_task_added"] = True
    
    # Add Notify task if missing
    if notif_task_idx is None:
        print(f"✗ No Notify task found - adding new one")
        notif_task = create_notification_task(workflow_name, leaf_tasks)
        tasks.append(notif_task)
        changes["notification_task_added"] = True
    else:
        print(f"✓ Notification task already exists at index {notif_task_idx}")
    
    # Update workflow
    workflow["tasks"] = tasks
    
    # Write back
    if not dry_run:
        with open(workflow_path, 'w') as f:
            json.dump(workflow, f, indent=2)
        print(f"✅ Updated {workflow_path.name}")
    else:
        print(f"🔍 [DRY RUN] Would update {workflow_path.name}")
    
    return changes


def main():
    parser = argparse.ArgumentParser(description="Fix pipeline logging in all LMIP workflows")
    parser.add_argument("--dir", default=".", help="Workflows directory (default: current directory)")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing files")
    args = parser.parse_args()
    
    workflows_dir = Path(args.dir)
    
    if not workflows_dir.exists():
        print(f"❌ Directory not found: {workflows_dir}")
        return
    
    # Find all workflow JSON files
    workflow_files = list(workflows_dir.glob("*.json"))
    workflow_files = [f for f in workflow_files if not f.name.endswith(".backup")]
    
    if not workflow_files:
        print(f"❌ No workflow JSON files found in {workflows_dir}")
        return
    
    print(f"\n{'='*80}")
    print(f"LMIP WORKFLOW LOGGING FIX - {'DRY RUN' if args.dry_run else 'LIVE UPDATE'}")
    print(f"{'='*80}")
    print(f"Found {len(workflow_files)} workflow files")
    
    all_changes = []
    
    for workflow_file in sorted(workflow_files):
        try:
            changes = fix_workflow(workflow_file, dry_run=args.dry_run)
            all_changes.append(changes)
        except Exception as e:
            print(f"❌ Error processing {workflow_file.name}: {e}")
            all_changes.append({
                "file": workflow_file.name,
                "errors": [str(e)]
            })
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    
    log_fixed = sum(1 for c in all_changes if c.get("log_task_fixed"))
    log_added = sum(1 for c in all_changes if c.get("log_task_added"))
    notif_added = sum(1 for c in all_changes if c.get("notification_task_added"))
    errors = sum(1 for c in all_changes if c.get("errors"))
    
    print(f"✓ Log tasks fixed: {log_fixed}")
    print(f"✓ Log tasks added: {log_added}")
    print(f"✓ Notification tasks added: {notif_added}")
    print(f"⚠️  Errors: {errors}")
    
    if errors > 0:
        print(f"\n⚠️  Workflows with errors:")
        for change in all_changes:
            if change.get("errors"):
                print(f"  - {change['file']}: {', '.join(change['errors'])}")
    
    print(f"\n{'='*80}")
    if args.dry_run:
        print(f"🔍 DRY RUN COMPLETE - No files were modified")
        print(f"Run without --dry-run to apply changes")
    else:
        print(f"✅ ALL WORKFLOWS UPDATED")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
