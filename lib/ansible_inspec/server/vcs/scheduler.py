"""
VCS polling scheduler for ansible-inspec server.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_MISSED
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class VCSPollingScheduler:
    """Scheduler for VCS repository polling"""
    
    def __init__(self, database_url: Optional[str] = None, timezone: str = "UTC"):
        """
        Initialize scheduler
        
        Args:
            database_url: Database URL (ignored - using memory store)
            timezone: Timezone for scheduler
        """
        # Use memory job store - VCS jobs are transient and can be recreated on restart
        jobstores = {
            'default': MemoryJobStore()
        }
        logger.info("Scheduler using in-memory jobstore (VCS jobs will be recreated on restart)")
        
        executors = {
            'default': ThreadPoolExecutor(10),  # Max 10 concurrent polls
        }
        
        job_defaults = {
            'coalesce': True,  # Combine missed executions
            'max_instances': 1,  # Prevent concurrent runs of same job
            'misfire_grace_time': 300  # 5 minutes grace for missed jobs
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=timezone
        )
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        self.scheduler.add_listener(
            self._job_missed_listener,
            EVENT_JOB_MISSED
        )
        
        self.running = False
    
    def start(self):
        """Start the scheduler"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            logger.info("VCS polling scheduler started")
    
    def shutdown(self, wait: bool = True):
        """Gracefully shutdown scheduler"""
        if self.running:
            logger.info("Shutting down scheduler...")
            self.scheduler.shutdown(wait=wait)
            self.running = False
            logger.info("Scheduler shut down")
    
    def add_vcs_poll_job(
        self,
        job_id: str,
        repository_url: str,
        credential_id: str,
        poll_interval_minutes: int = 15,
        func=None
    ):
        """
        Add VCS polling job
        
        Args:
            job_id: Unique job identifier
            repository_url: Git repository URL
            credential_id: VCS credential ID for authentication
            poll_interval_minutes: Polling interval in minutes
            func: Async function to call for polling
        """
        if func is None:
            logger.error("No polling function provided")
            return
        
        trigger = IntervalTrigger(minutes=poll_interval_minutes)
        
        try:
            self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                args=[repository_url, credential_id],
                replace_existing=True,
                name=f"VCS Poll: {repository_url}"
            )
            logger.info(f"Added VCS poll job: {job_id} for {repository_url} (interval: {poll_interval_minutes}m)")
        except Exception as e:
            logger.error(f"Failed to add VCS poll job: {e}")
    
    def remove_vcs_poll_job(self, job_id: str) -> bool:
        """
        Remove VCS polling job
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if removed, False if not found
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed VCS poll job: {job_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to remove VCS poll job {job_id}: {e}")
            return False
    
    def list_jobs(self) -> list:
        """
        List all scheduled jobs
        
        Returns:
            List of job information
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def _job_error_listener(self, event):
        """Handle job errors"""
        logger.error(
            f"Job {event.job_id} error: {event.exception}",
            exc_info=True
        )
    
    def _job_executed_listener(self, event):
        """Log successful job execution"""
        logger.debug(f"Job {event.job_id} executed successfully")
    
    def _job_missed_listener(self, event):
        """Log missed job executions"""
        logger.warning(f"Job {event.job_id} missed scheduled run")
