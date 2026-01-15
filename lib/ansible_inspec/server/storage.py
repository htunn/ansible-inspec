"""
Storage layer for InSpec Execution Server

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0

Provides persistent storage for job templates, jobs, and workflows.
"""

import json
from pathlib import Path
from typing import List, Optional

from .models import JobTemplate, Job, WorkflowTemplate


class Storage:
    """
    Simple file-based storage for server data
    In production, this would use a database like PostgreSQL
    """
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize storage
        
        Args:
            data_dir: Directory to store data files
        """
        self.data_dir = Path(data_dir)
        self.templates_dir = self.data_dir / "job_templates"
        self.jobs_dir = self.data_dir / "jobs"
        self.workflows_dir = self.data_dir / "workflow_templates"
        
        # Create directories
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
    
    # Job Template methods
    def save_job_template(self, template: JobTemplate) -> None:
        """Save a job template"""
        file_path = self.templates_dir / f"{template.id}.json"
        with open(file_path, 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
    
    def get_job_template(self, template_id: str) -> Optional[JobTemplate]:
        """Get a job template by ID"""
        file_path = self.templates_dir / f"{template_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, 'r') as f:
            data = json.load(f)
        return JobTemplate.from_dict(data)
    
    def list_job_templates(self) -> List[JobTemplate]:
        """List all job templates"""
        templates = []
        for file_path in self.templates_dir.glob("*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
            templates.append(JobTemplate.from_dict(data))
        return sorted(templates, key=lambda t: t.created_at, reverse=True)
    
    def delete_job_template(self, template_id: str) -> bool:
        """Delete a job template"""
        file_path = self.templates_dir / f"{template_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    # Job methods
    def save_job(self, job: Job) -> None:
        """Save a job"""
        file_path = self.jobs_dir / f"{job.id}.json"
        with open(file_path, 'w') as f:
            json.dump(job.to_dict(), f, indent=2)
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID"""
        file_path = self.jobs_dir / f"{job_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, 'r') as f:
            data = json.load(f)
        return Job.from_dict(data)
    
    def list_jobs(self) -> List[Job]:
        """List all jobs"""
        jobs = []
        for file_path in self.jobs_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                jobs.append(Job.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                # Skip invalid job files
                continue
        return sorted(jobs, key=lambda j: j.created_at, reverse=True)
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job by ID. Returns True if deleted, False if not found."""
        file_path = self.jobs_dir / f"{job_id}.json"
        if not file_path.exists():
            return False
        
        # Also delete job output directory if it exists
        job_output_dir = self.jobs_dir / job_id
        if job_output_dir.exists() and job_output_dir.is_dir():
            import shutil
            shutil.rmtree(job_output_dir)
        
        file_path.unlink()
        return True
    
    # Workflow Template methods
    def save_workflow_template(self, workflow: WorkflowTemplate) -> None:
        """Save a workflow template"""
        file_path = self.workflows_dir / f"{workflow.id}.json"
        with open(file_path, 'w') as f:
            json.dump(workflow.to_dict(), f, indent=2)
    
    def get_workflow_template(self, workflow_id: str) -> Optional[WorkflowTemplate]:
        """Get a workflow template by ID"""
        file_path = self.workflows_dir / f"{workflow_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, 'r') as f:
            data = json.load(f)
        return WorkflowTemplate.from_dict(data)
    
    def list_workflow_templates(self) -> List[WorkflowTemplate]:
        """List all workflow templates"""
        workflows = []
        for file_path in self.workflows_dir.glob("*.json"):
            with open(file_path, 'r') as f:
                data = json.load(f)
            workflows.append(WorkflowTemplate.from_dict(data))
        return sorted(workflows, key=lambda w: w.created_at, reverse=True)
    
    def delete_workflow_template(self, workflow_id: str) -> bool:
        """Delete a workflow template"""
        file_path = self.workflows_dir / f"{workflow_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
