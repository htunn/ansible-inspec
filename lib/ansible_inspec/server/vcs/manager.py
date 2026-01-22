"""
VCS Manager for orchestrating Git repository synchronization.

This module coordinates Git operations, profile discovery, and job template
creation from synchronized repositories.
"""

import logging
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import yaml

from ansible_inspec.server.vcs.git_client import GitClient
from ansible_inspec.server.models import JobTemplate, VCSCredential
from ansible_inspec.server.storage.base import StorageBackend
from ansible_inspec.server.encryption import EncryptionService
from ansible_inspec.server.monitoring import record_vcs_sync
from ansible_inspec.server.db.prisma_client import get_db

logger = logging.getLogger(__name__)


class VCSManager:
    """
    VCS Manager for Git repository synchronization.
    
    Coordinates repository polling, profile discovery, and template creation.
    """

    def __init__(
        self,
        storage: StorageBackend,
        encryption: EncryptionService,
        work_dir: str = "/tmp/ansible-inspec-repos",
    ):
        """
        Initialize VCS Manager.
        
        Args:
            storage: Storage backend for saving templates
            encryption: Encryption service for credentials
            work_dir: Working directory for Git checkouts
        """
        self.storage = storage
        self.encryption = encryption
        self.work_dir = Path(work_dir)
        os.makedirs(work_dir, exist_ok=True)
        logger.info(f"VCS Manager initialized with work_dir: {work_dir}")

    async def sync_repository(self, repo_name: str) -> dict:
        """
        Synchronize a repository and process InSpec profiles.
        
        Args:
            repo_name: Repository name
            
        Returns:
            Dict with sync results
        """
        start_time = datetime.now()
        status = "success"
        error_message = None
        profiles_found = 0
        templates_created = 0
        sync_history_id = None
        current_hash = None
        
        try:
            async with get_db() as db:
                # Get repository configuration
                repo = await db.vcsrepository.find_unique(
                    where={"name": repo_name},
                    include={"credential": True}
                )
                
                if not repo:
                    raise ValueError(f"Repository not found: {repo_name}")
                
                # Create sync history record
                sync_record = await db.vcssynchistory.create(
                    data={
                        "repositoryId": repo.id,
                        "syncStartedAt": start_time,
                        "status": "running",
                        "triggerType": "manual"
                    }
                )
                sync_history_id = sync_record.id
                
                # Update sync status
                await db.vcsrepository.update(
                    where={"name": repo_name},
                    data={"syncStatus": "syncing"}
                )
                
                # Check for changes
                git_client = GitClient(clone_dir=self.work_dir)
                changed = await self._check_repository_changes(repo, git_client)
                
                if not changed and repo.lastSyncAt:
                    logger.info(f"No changes in repository: {repo_name}")
                    
                    # Update sync history
                    if sync_history_id:
                        await db.vcssynchistory.update(
                            where={"id": sync_history_id},
                            data={
                                "syncCompletedAt": datetime.now(),
                                "status": "success",
                                "commitHash": repo.lastCommitHash
                            }
                        )
                    
                    await db.vcsrepository.update(
                        where={"name": repo_name},
                        data={
                            "syncStatus": "idle",
                            "lastSyncAt": datetime.now(),
                        }
                    )
                    return {
                        "status": "unchanged",
                        "profiles_found": 0,
                        "templates_created": 0,
                    }
                
                # Clone or pull repository
                repo_path = await self._clone_or_pull_repository(repo, git_client)
                
                # Find and process InSpec profiles
                profiles = await self._find_inspec_profiles(repo_path, repo.profilePath)
                profiles_found = len(profiles)
                logger.info(f"Found {profiles_found} InSpec profiles in {repo_name}")
                
                # Create or update job templates
                if repo.autoImport:
                    for profile in profiles:
                        if await self._upsert_job_template(profile, repo, repo_path):
                            templates_created += 1
                    logger.info(f"Created/updated {templates_created} job templates")
                
                # Get current commit hash
                import git
                git_repo = git.Repo(repo_path)
                current_hash = git_repo.head.commit.hexsha
                
                # Update sync history with results
                if sync_history_id:
                    await db.vcssynchistory.update(
                        where={"id": sync_history_id},
                        data={
                            "syncCompletedAt": datetime.now(),
                            "status": "success",
                            "commitHash": current_hash,
                            "profilesDiscovered": profiles_found,
                            "templatesCreated": templates_created
                        }
                    )
                
                # Update repository sync info
                await db.vcsrepository.update(
                    where={"name": repo_name},
                    data={
                        "syncStatus": "success",
                        "lastSyncAt": datetime.now(),
                        "lastCommitHash": current_hash,
                        "syncError": None,
                    }
                )
                
        except Exception as e:
            status = "failed"
            error_message = str(e)
            logger.error(f"Repository sync failed for {repo_name}: {e}")
            
            # Update repository with error
            async with get_db() as db:
                # Update sync history with error
                if sync_history_id:
                    await db.vcssynchistory.update(
                        where={"id": sync_history_id},
                        data={
                            "syncCompletedAt": datetime.now(),
                            "status": "failed",
                            "errors": error_message,
                            "commitHash": current_hash
                        }
                    )
                
                await db.vcsrepository.update(
                    where={"name": repo_name},
                    data={
                        "syncStatus": "failed",
                        "syncError": error_message,
                        "lastSyncAt": datetime.now(),
                    }
                )
        
        # Record metrics
        duration = (datetime.now() - start_time).total_seconds()
        record_vcs_sync(repository=repo_name, status=status, duration=duration)
        
        return {
            "status": status,
            "profiles_found": profiles_found,
            "templates_created": templates_created,
            "error": error_message,
            "duration": duration,
        }

    async def _check_repository_changes(self, repo, git_client: GitClient) -> bool:
        """
        Check if repository has new commits.
        
        Args:
            repo: VCSRepository database model
            git_client: Git client instance
            
        Returns:
            True if changes detected, False otherwise
        """
        try:
            # Get credential if needed
            credential = None
            if repo.credential:
                credential_data = VCSCredential(
                    id=repo.credential.id,
                    name=repo.credential.name,
                    vcs_type=repo.credential.vcsType,
                    username=repo.credential.username,
                    password=repo.credential.password,
                    ssh_private_key=repo.credential.sshPrivateKey,
                    token=repo.credential.token,
                    repository_url=repo.credential.repositoryUrl,
                    encrypted=True,
                )
                # Decrypt credentials
                credential_data.decrypt_credentials(self.encryption)
                credential = credential_data
            
            # Check remote HEAD
            remote_hash = await git_client.check_remote_head(
                repo.url,
                credential=credential
            )
            
            # Compare with last known hash
            if repo.lastCommitHash and repo.lastCommitHash == remote_hash:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to check repository changes: {e}")
            return True  # Assume changed on error

    async def _clone_or_pull_repository(self, repo, git_client: GitClient) -> str:
        """
        Clone or pull repository.
        
        Args:
            repo: VCSRepository database model
            git_client: Git client instance
            
        Returns:
            Path to local repository
        """
        # Get credential if needed
        credential = None
        if repo.credential:
            credential_data = VCSCredential(
                id=repo.credential.id,
                name=repo.credential.name,
                vcs_type=repo.credential.vcsType,
                username=repo.credential.username,
                password=repo.credential.password,
                ssh_private_key=repo.credential.sshPrivateKey,
                token=repo.credential.token,
                repository_url=repo.credential.repositoryUrl,
                encrypted=True,
            )
            credential_data.decrypt_credentials(self.encryption)
            credential = credential_data
        
        # Clone or pull
        local_path = self.work_dir / repo.name
        success = await git_client.clone_or_pull(
            repo.url,
            local_path=local_path,
            branch=repo.branch,
            credential=credential
        )
        
        if not success:
            raise Exception(f"Failed to clone/pull repository: {repo.url}")
        
        return str(local_path)

    async def _find_inspec_profiles(self, repo_path: str, profile_path: str) -> List[dict]:
        """
        Find InSpec profiles in repository.
        
        Args:
            repo_path: Path to repository
            profile_path: Relative path to profiles directory
            
        Returns:
            List of profile info dicts
        """
        git_client = GitClient(clone_dir=self.work_dir)
        profiles = git_client.find_inspec_profiles(repo_path)
        
        # Filter by profile_path if specified
        if profile_path and profile_path != ".":
            full_profile_path = os.path.join(repo_path, profile_path)
            profiles = [
                p for p in profiles
                if p["path"].startswith(full_profile_path)
            ]
        
        return profiles

    async def _upsert_job_template(self, profile: dict, repo, repo_path: str) -> bool:
        """
        Create or update job template from InSpec profile.
        
        Args:
            profile: Profile info dict from find_inspec_profiles
            repo: VCSRepository database model
            repo_path: Path to cloned repository
            
        Returns:
            True if template was created/updated
        """
        try:
            # Read inspec.yml
            inspec_yml_path = os.path.join(profile["path"], "inspec.yml")
            with open(inspec_yml_path, 'r') as f:
                inspec_data = yaml.safe_load(f)
            
            # Generate template name from profile
            profile_name = inspec_data.get("name", os.path.basename(profile["path"]))
            template_name = f"{repo.name}/{profile_name}"
            
            # Check if template exists
            async with get_db() as db:
                existing = await db.jobtemplate.find_unique(
                    where={"name": template_name}
                )
                
                # Create template data
                template_data = {
                    "name": template_name,
                    "description": inspec_data.get("title", inspec_data.get("summary", "")),
                    "profile": profile["path"],
                    "vcsRepoId": repo.id,
                    "vcsPath": os.path.relpath(profile["path"], repo_path),
                    "vcsSync": True,
                }
                
                if existing:
                    # Update existing template
                    await db.jobtemplate.update(
                        where={"id": existing.id},
                        data=template_data
                    )
                    logger.debug(f"Updated job template: {template_name}")
                else:
                    # Create new template
                    await db.jobtemplate.create(data=template_data)
                    logger.debug(f"Created job template: {template_name}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to create/update template for profile {profile['path']}: {e}")
            return False

    async def list_sync_jobs(self) -> List[dict]:
        """
        List all VCS sync jobs and their status.
        
        Returns:
            List of repository sync status dicts
        """
        async with get_db() as db:
            repos = await db.vcsrepository.find_many(
                order={"lastSyncAt": "desc"}
            )
            
            return [
                {
                    "name": r.name,
                    "url": r.url,
                    "branch": r.branch,
                    "sync_status": r.syncStatus,
                    "last_sync_at": r.lastSyncAt.isoformat() if r.lastSyncAt else None,
                    "last_commit_hash": r.lastCommitHash,
                    "sync_error": r.syncError,
                    "poll_interval": r.pollInterval,
                }
                for r in repos
            ]

    async def trigger_manual_sync(self, repo_name: str) -> dict:
        """
        Manually trigger repository synchronization.
        
        Args:
            repo_name: Repository name
            
        Returns:
            Sync result dict
        """
        logger.info(f"Manual sync triggered for repository: {repo_name}")
        return await self.sync_repository(repo_name)
