"""
REST API server for InSpec Execution Server

Copyright (C) 2026 ansible-inspec project contributors
Licensed under GPL-3.0

Provides REST API endpoints for InSpec profile execution with ansible-inspec.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from .models import JobTemplate, Job, WorkflowTemplate, JobStatus
from .executor import JobExecutor
from .storage import Storage


def create_app(data_dir: str = "./data") -> FastAPI:
    """
    Create and configure the FastAPI application
    
    Args:
        data_dir: Directory to store job data
        
    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="InSpec Execution Server",
        description="Web UI and REST API for ansible-inspec",
        version="1.0.0"
    )
    
    # Enable CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize storage and executor
    storage = Storage(data_dir)
    executor = JobExecutor(data_dir, storage=storage)
    
    @app.get('/')
    def index():
        """API root - redirects to docs"""
        return {
            "message": "InSpec Execution Server API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "api": "/api/v1/"
        }
    
    # Pydantic models for request/response
    class JobTemplateCreate(BaseModel):
        """Job Template creation schema for InSpec profiles and Ansible playbooks"""
        name: str
        description: str = ""
        job_type: str = "run"
        
        # InSpec-specific fields
        profile_path: str = ""
        reporter: str = "cli json"
        supermarket: bool = False
        
        # AAP-compatible fields
        playbook: Optional[str] = None
        project: Optional[str] = None
        inventory: Optional[str] = None
        credentials: List[str] = []
        
        # Execution options
        target: Optional[str] = None
        limit: Optional[str] = None
        tags: List[str] = []
        skip_tags: List[str] = []
        extra_vars: Dict[str, Any] = {}
        
        # Performance settings
        forks: int = 5
        timeout: int = 0
        verbosity: int = 0
        
        # Advanced options
        diff_mode: bool = False
        job_slice_count: int = 1
        allow_simultaneous: bool = False
        use_fact_cache: bool = False
        
        # Metadata
        created_by: Optional[str] = None
        organization: Optional[str] = None
    
    class JobLaunch(BaseModel):
        """Job launch parameters"""
        extra_vars: Dict[str, Any] = {}
        limit: Optional[str] = None
        tags: List[str] = []
        skip_tags: List[str] = []
        verbosity: Optional[int] = None
    
    # API Info
    @app.get('/api/v1/')
    def api_info():
        """API information endpoint"""
        return {
            'name': 'InSpec Execution Server',
            'version': '1.0.0',
            'description': 'Web UI and REST API for ansible-inspec',
            'endpoints': {
                'job_templates': '/api/v1/job_templates/',
                'jobs': '/api/v1/jobs/',
                'workflows': '/api/v1/workflow_templates/'
            }
        }
    
    # Job Templates endpoints
    @app.get('/api/v1/job_templates/')
    def list_job_templates():
        """List all job templates"""
        templates = storage.list_job_templates()
        return {
            'count': len(templates),
            'results': [t.to_dict() for t in templates]
        }
    
    @app.post('/api/v1/job_templates/', status_code=status.HTTP_201_CREATED)
    def create_job_template(template_data: JobTemplateCreate):
        """Create a new job template"""
        from pathlib import Path
        
        # Validate paths are absolute
        if template_data.profile_path and not Path(template_data.profile_path).is_absolute():
            raise HTTPException(status_code=400, detail='profile_path must be an absolute path')
        if template_data.playbook and not Path(template_data.playbook).is_absolute():
            raise HTTPException(status_code=400, detail='playbook must be an absolute path')
        if template_data.project and not Path(template_data.project).is_absolute():
            raise HTTPException(status_code=400, detail='project must be an absolute path')
        if template_data.inventory and not Path(template_data.inventory).is_absolute():
            raise HTTPException(status_code=400, detail='inventory must be an absolute path')
        
        template = JobTemplate.from_dict(template_data.dict())
        template.modified_at = datetime.now()
        storage.save_job_template(template)
        return template.to_dict()
    
    @app.get('/api/v1/job_templates/{template_id}/')
    def get_job_template(template_id: str):
        """Get a specific job template"""
        template = storage.get_job_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail='Job template not found')
        return template.to_dict()
    
    @app.put('/api/v1/job_templates/{template_id}/')
    @app.patch('/api/v1/job_templates/{template_id}/')
    def update_job_template(template_id: str, update_data: dict):
        """Update a job template"""
        from pathlib import Path
        
        template = storage.get_job_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail='Job template not found')
        
        # Validate paths are absolute if provided
        if 'profile_path' in update_data and update_data['profile_path']:
            if not Path(update_data['profile_path']).is_absolute():
                raise HTTPException(status_code=400, detail='profile_path must be an absolute path')
        if 'playbook' in update_data and update_data['playbook']:
            if not Path(update_data['playbook']).is_absolute():
                raise HTTPException(status_code=400, detail='playbook must be an absolute path')
        if 'project' in update_data and update_data['project']:
            if not Path(update_data['project']).is_absolute():
                raise HTTPException(status_code=400, detail='project must be an absolute path')
        if 'inventory' in update_data and update_data['inventory']:
            if not Path(update_data['inventory']).is_absolute():
                raise HTTPException(status_code=400, detail='inventory must be an absolute path')
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(template, key) and key != 'id':
                setattr(template, key, value)
        
        template.modified_at = datetime.now()
        storage.save_job_template(template)
        return template.to_dict()
    
    @app.delete('/api/v1/job_templates/{template_id}/', status_code=status.HTTP_204_NO_CONTENT)
    def delete_job_template(template_id: str):
        """Delete a job template"""
        if not storage.delete_job_template(template_id):
            raise HTTPException(status_code=404, detail='Job template not found')
        return None
    
    @app.post('/api/v1/job_templates/{template_id}/launch/', status_code=status.HTTP_201_CREATED)
    def launch_job_template(template_id: str, launch_data: JobLaunch = JobLaunch()):
        """Launch a job from a template"""
        template = storage.get_job_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail='Job template not found')
        
        # Create job
        job = Job(
            job_template_id=template.id,
            job_template_name=template.name,
            status=JobStatus.PENDING,
            extra_vars=launch_data.extra_vars
        )
        storage.save_job(job)
        
        # Launch job in background
        executor.launch_job(job, template)
        
        return job.to_dict()
    
    # Jobs endpoints
    @app.get('/api/v1/jobs/')
    def list_jobs(status_filter: Optional[str] = None, job_template: Optional[str] = None):
        """List all jobs"""
        jobs = storage.list_jobs()
        
        # Support filtering by status
        if status_filter:
            jobs = [j for j in jobs if j.status.value == status_filter]
        
        # Support filtering by template
        if job_template:
            jobs = [j for j in jobs if j.job_template_id == job_template]
        
        return {
            'count': len(jobs),
            'results': [j.to_dict() for j in jobs]
        }
    
    @app.get('/api/v1/jobs/{job_id}/')
    def get_job(job_id: str):
        """Get a specific job"""
        job = storage.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')
        return job.to_dict()
    
    @app.post('/api/v1/jobs/{job_id}/cancel/')
    def cancel_job(job_id: str):
        """Cancel a running job"""
        job = storage.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')
        
        if job.status == JobStatus.RUNNING:
            executor.cancel_job(job_id)
            job.status = JobStatus.CANCELED
            job.finished_at = datetime.now()
            storage.save_job(job)
            return job.to_dict()
        
        raise HTTPException(status_code=400, detail='Job is not running')
    
    @app.delete('/api/v1/jobs/{job_id}/')
    def delete_job(job_id: str):
        """Delete a job (only pending jobs can be deleted)"""
        job = storage.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')
        
        # Only allow deleting pending jobs to prevent data loss
        if job.status != JobStatus.PENDING:
            raise HTTPException(
                status_code=400, 
                detail=f'Cannot delete job with status {job.status.value}. Only pending jobs can be deleted.'
            )
        
        if storage.delete_job(job_id):
            return {'message': f'Job {job_id} deleted successfully'}
        else:
            raise HTTPException(status_code=500, detail='Failed to delete job')
    
    @app.get('/api/v1/jobs/{job_id}/stdout/')
    def get_job_stdout(job_id: str):
        """Get job stdout"""
        job = storage.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')
        return {'stdout': job.stdout}
    
    @app.get('/api/v1/jobs/{job_id}/logs/')
    def get_job_logs(job_id: str, lines: int = 100):
        """Get live job logs (stdout and stderr) from files"""
        from pathlib import Path
        
        job = storage.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail='Job not found')
        
        job_output_dir = Path(data_dir) / 'jobs' / job_id
        stdout_file = job_output_dir / 'stdout.txt'
        stderr_file = job_output_dir / 'stderr.txt'
        
        stdout_content = ''
        stderr_content = ''
        
        # Read stdout if file exists
        if stdout_file.exists():
            try:
                with open(stdout_file, 'r') as f:
                    content = f.read()
                    # Get last N lines if content is large
                    if lines > 0:
                        lines_list = content.splitlines()
                        stdout_content = '\n'.join(lines_list[-lines:])
                    else:
                        stdout_content = content
            except Exception as e:
                stdout_content = f'Error reading stdout: {str(e)}'
        
        # Read stderr if file exists
        if stderr_file.exists():
            try:
                with open(stderr_file, 'r') as f:
                    content = f.read()
                    if lines > 0:
                        lines_list = content.splitlines()
                        stderr_content = '\n'.join(lines_list[-lines:])
                    else:
                        stderr_content = content
            except Exception as e:
                stderr_content = f'Error reading stderr: {str(e)}'
        
        return {
            'job_id': job_id,
            'status': job.status.value,
            'stdout': stdout_content,
            'stderr': stderr_content,
            'has_output': bool(stdout_content or stderr_content)
        }
    
    # Workflow Templates endpoints
    @app.get('/api/v1/workflow_templates/')
    def list_workflow_templates():
        """List all workflow templates"""
        workflows = storage.list_workflow_templates()
        return {
            'count': len(workflows),
            'results': [w.to_dict() for w in workflows]
        }
    
    @app.post('/api/v1/workflow_templates/', status_code=status.HTTP_201_CREATED)
    def create_workflow_template(workflow_data: dict):
        """Create a new workflow template"""
        workflow = WorkflowTemplate.from_dict(workflow_data)
        workflow.modified_at = datetime.now()
        storage.save_workflow_template(workflow)
        return workflow.to_dict()
    
    @app.get('/api/v1/workflow_templates/{workflow_id}/')
    def get_workflow_template(workflow_id: str):
        """Get a specific workflow template"""
        workflow = storage.get_workflow_template(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail='Workflow template not found')
        return workflow.to_dict()
    
    @app.delete('/api/v1/workflow_templates/{workflow_id}/', status_code=status.HTTP_204_NO_CONTENT)
    def delete_workflow_template(workflow_id: str):
        """Delete a workflow template"""
        if not storage.delete_workflow_template(workflow_id):
            raise HTTPException(status_code=404, detail='Workflow template not found')
        return None
    
    # Statistics endpoint
    @app.get('/api/v1/statistics/')
    def get_statistics():
        """Get server statistics"""
        jobs = storage.list_jobs()
        templates = storage.list_job_templates()
        
        # Calculate statistics
        total_jobs = len(jobs)
        successful_jobs = len([j for j in jobs if j.status == JobStatus.SUCCESSFUL])
        failed_jobs = len([j for j in jobs if j.status == JobStatus.FAILED])
        running_jobs = len([j for j in jobs if j.status == JobStatus.RUNNING])
        
        return {
            'job_templates': len(templates),
            'total_jobs': total_jobs,
            'successful_jobs': successful_jobs,
            'failed_jobs': failed_jobs,
            'running_jobs': running_jobs,
            'success_rate': (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
        }
    
    return app


def run_server(host: str = '0.0.0.0', port: int = 8080, data_dir: str = "./data"):
    """
    Run the InSpec Execution Server
    
    Args:
        host: Host to bind to
        port: Port to bind to
        data_dir: Directory for data storage
    """
    import uvicorn
    
    app = create_app(data_dir)
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║           InSpec Execution Server                              ║
║                                                                ║
║  Web UI and REST API for ansible-inspec                        ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

Server starting at: http://{host}:{port}
API documentation: http://{host}:{port}/docs
Interactive API docs: http://{host}:{port}/redoc

Press Ctrl+C to stop the server
""")
    uvicorn.run(app, host=host, port=port, log_level="info")
