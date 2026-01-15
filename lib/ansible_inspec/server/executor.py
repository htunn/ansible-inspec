"""
Job executor for running InSpec profiles

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0
"""

import subprocess
import threading
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from .models import Job, JobTemplate, JobStatus, JobType


class JobExecutor:
    """
    Executes InSpec profiles as jobs
    Manages job execution in background threads
    """
    
    def __init__(self, data_dir: str = "./data", storage=None):
        """
        Initialize job executor
        
        Args:
            data_dir: Directory to store job outputs and logs
            storage: Storage instance for saving job updates
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.running_jobs: Dict[str, threading.Thread] = {}
        self.storage = storage
        
    def launch_job(self, job: Job, template: JobTemplate) -> None:
        """
        Launch a job in the background
        
        Args:
            job: Job instance to execute
            template: JobTemplate to execute
        """
        thread = threading.Thread(
            target=self._execute_job,
            args=(job, template),
            daemon=True
        )
        self.running_jobs[job.id] = thread
        thread.start()
        
    def _execute_job(self, job: Job, template: JobTemplate) -> None:
        """
        Execute a job (runs in background thread)
        
        Args:
            job: Job instance
            template: JobTemplate to execute
        """
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        # Save job status update
        if self.storage:
            self.storage.save_job(job)
        
        # Build command
        cmd = self._build_command(template, job)
        
        # Build environment variables
        env = self._build_env(template, job)
        
        # Create output directory for this job
        job_output_dir = self.data_dir / "jobs" / job.id
        job_output_dir.mkdir(parents=True, exist_ok=True)
        
        stdout_file = job_output_dir / "stdout.txt"
        stderr_file = job_output_dir / "stderr.txt"
        json_output = job_output_dir / "report.json"
        
        try:
            # Execute the command with environment variables
            with open(stdout_file, 'w') as stdout_f, open(stderr_file, 'w') as stderr_f:
                process = subprocess.Popen(
                    cmd,
                    stdout=stdout_f,
                    stderr=stderr_f,
                    env=env,
                    text=True
                )
                
                # Wait for completion
                return_code = process.wait()
                
            # Read outputs
            with open(stdout_file, 'r') as f:
                job.stdout = f.read()
            with open(stderr_file, 'r') as f:
                job.stderr = f.read()
                
            # Parse JSON report if it exists
            if json_output.exists():
                with open(json_output, 'r') as f:
                    job.result_summary = json.load(f)
            
            # Set job status based on return code
            if return_code == 0:
                job.status = JobStatus.SUCCESSFUL
            else:
                job.status = JobStatus.FAILED
                
        except Exception as e:
            job.status = JobStatus.FAILED
            job.stderr += f"\n\nExecution error: {str(e)}"
            
        finally:
            job.finished_at = datetime.now()
            
            # Save final job status
            if self.storage:
                self.storage.save_job(job)
            
            # Remove from running jobs
            self.running_jobs.pop(job.id, None)
            
    def _build_command(self, template: JobTemplate, job: Job) -> list:
        """
        Build the ansible-inspec command from template
        Supports both InSpec profiles and Ansible playbooks
        
        Args:
            template: JobTemplate
            job: Job instance
            
        Returns:
            Command as list of strings
        """
        # Determine if this is a playbook or InSpec profile execution
        if template.playbook and template.playbook.strip():
            # Ansible playbook execution
            cmd = ["ansible-playbook", template.playbook]
            
            if template.inventory:
                cmd.extend(["-i", template.inventory])
                
            if template.limit or job.extra_vars.get('limit'):
                limit = job.extra_vars.get('limit', template.limit)
                cmd.extend(["--limit", limit])
                
            # Add tags
            if template.tags or job.extra_vars.get('tags'):
                tags = job.extra_vars.get('tags', template.tags)
                if tags:
                    cmd.extend(["--tags", ",".join(tags) if isinstance(tags, list) else tags])
                    
            # Add skip-tags
            if template.skip_tags or job.extra_vars.get('skip_tags'):
                skip_tags = job.extra_vars.get('skip_tags', template.skip_tags)
                if skip_tags:
                    cmd.extend(["--skip-tags", ",".join(skip_tags) if isinstance(skip_tags, list) else skip_tags])
                    
            # Add forks
            forks = job.extra_vars.get('forks', template.forks)
            if forks != 5:  # Only add if non-default
                cmd.extend(["--forks", str(forks)])
                
            # Add timeout
            if template.timeout > 0:
                cmd.extend(["--timeout", str(template.timeout)])
                
            # Add diff mode
            if template.diff_mode:
                cmd.append("--diff")
                
            # Add check mode
            if template.job_type == JobType.CHECK:
                cmd.append("--check")
                
        elif template.profile_path and template.profile_path.strip():
            # InSpec profile execution
            cmd = ["ansible-inspec", "exec", template.profile_path]
            
            if template.inventory:
                cmd.extend(["-i", template.inventory])
                
        elif template.project and template.project.strip():
            # InSpec profile execution from project
            cmd = ["ansible-inspec", "exec", template.project]
            
            if template.inventory:
                cmd.extend(["-i", template.inventory])
                
        else:
            # No valid execution source specified
            raise ValueError(
                "Job template must specify either 'playbook' (for Ansible playbooks) "
                "or 'profile_path'/'project' (for InSpec profiles)"
            )
        
        # Continue building command for InSpec profiles
        if template.profile_path or template.project:
            if template.target:
                cmd.extend(["-t", template.target])
                
            if template.supermarket:
                cmd.append("--supermarket")
                
            if template.reporter:
                # Add JSON reporter for programmatic access
                job_output_dir = self.data_dir / "jobs" / job.id
                json_path = job_output_dir / "report.json"
                reporter_arg = f"{template.reporter} json:{json_path}"
                cmd.extend(["-r", reporter_arg])
                
            if template.limit:
                cmd.extend(["--limit", template.limit])
        
        # Common options for both playbook and InSpec modes
        # Add verbosity (default to 1 if not specified for better output)
        verbosity = job.extra_vars.get('verbosity', template.verbosity or 1)
        if verbosity > 0:
            cmd.append("-" + "v" * verbosity)
            
        # Add extra vars (only for ansible-playbook mode)
        if template.playbook and template.playbook.strip():
            # Merge template and job-specific extra vars
            merged_vars = {**template.extra_vars, **job.extra_vars}
            # Remove special keys that were already processed
            merged_vars.pop('limit', None)
            merged_vars.pop('tags', None)
            merged_vars.pop('skip_tags', None)
            merged_vars.pop('verbosity', None)
            merged_vars.pop('forks', None)
            merged_vars.pop('env_vars', None)  # env_vars go to environment, not -e
            
            if merged_vars:
                import json
                cmd.extend(["-e", json.dumps(merged_vars)])
            
        return cmd
    
    def _build_env(self, template: JobTemplate, job: Job) -> dict:
        """
        Build environment variables for job execution
        
        Args:
            template: JobTemplate
            job: Job instance
            
        Returns:
            Environment dictionary
        """
        import os
        
        # Start with current environment
        env = os.environ.copy()
        
        # Add template environment variables
        if template.extra_vars and 'env_vars' in template.extra_vars:
            env_vars = template.extra_vars['env_vars']
            if isinstance(env_vars, dict):
                for key, value in env_vars.items():
                    env[str(key)] = str(value)
        
        # Add job-specific environment variables (override template vars)
        if job.extra_vars and 'env_vars' in job.extra_vars:
            env_vars = job.extra_vars['env_vars']
            if isinstance(env_vars, dict):
                for key, value in env_vars.items():
                    env[str(key)] = str(value)
        
        return env
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job
        
        Args:
            job_id: Job ID to cancel
            
        Returns:
            True if job was running and canceled
        """
        if job_id in self.running_jobs:
            # Note: In a production system, we'd need more sophisticated
            # process management to actually terminate the subprocess
            # For now, we just remove it from tracking
            self.running_jobs.pop(job_id, None)
            return True
        return False
