"""
Git client for VCS operations.
"""
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict
import os

logger = logging.getLogger(__name__)


class GitClient:
    """Git client for repository operations"""
    
    def __init__(self, clone_dir: Optional[str] = None):
        """
        Initialize Git client
        
        Args:
            clone_dir: Directory for cloning repositories (optional)
        """
        self.clone_dir = Path(clone_dir) if clone_dir else Path(tempfile.gettempdir()) / "vcs_repos"
        self.temp_dirs = []
    
    async def check_remote_head(self, url: str, credential = None) -> Optional[str]:
        """
        Check remote repository HEAD commit
        
        Args:
            url: Repository URL
            credential: VCS credential (with decrypted fields)
            
        Returns:
            Remote HEAD commit hash, or None if failed
        """
        try:
            env = os.environ.copy()
            
            # Setup authentication
            if credential:
                if credential.ssh_private_key:
                    # Create temporary SSH key file
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_rsa') as key_file:
                        # Ensure key ends with newline (required for SSH)
                        key_content = credential.ssh_private_key
                        if not key_content.endswith('\n'):
                            key_content += '\n'
                        key_file.write(key_content)
                        key_file.flush()  # Ensure key is written to disk
                        os.fsync(key_file.fileno())  # Force write to disk
                        key_path = key_file.name
                    
                    os.chmod(key_path, 0o600)
                    env['GIT_SSH_COMMAND'] = f'ssh -i {key_path} -o StrictHostKeyChecking=no -o IdentitiesOnly=yes'
                    self.temp_dirs.append(key_path)
                    logger.debug(f"Using SSH key from {key_path}")
                
                elif credential.token:
                    # Use token authentication (for HTTPS)
                    if url.startswith('https://'):
                        # Inject token into URL
                        url = url.replace('https://', f'https://{credential.token}@')
            elif url.startswith('git@') or url.startswith('ssh://'):
                # For SSH URLs without credentials, still disable host key checking
                env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
            
            # Check remote HEAD
            result = subprocess.run(
                ['git', 'ls-remote', url, 'HEAD'],
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                commit_hash = result.stdout.split()[0]
                logger.debug(f"Remote HEAD for {url}: {commit_hash}")
                return commit_hash
            else:
                logger.error(f"Failed to check remote HEAD: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout checking remote HEAD for {url}")
            return None
        except Exception as e:
            logger.error(f"Error checking remote HEAD: {e}")
            return None
        finally:
            # Cleanup temporary files
            self._cleanup()
    
    async def clone_or_pull(
        self,
        url: str,
        local_path: Path,
        branch: str = "main",
        credential = None
    ) -> bool:
        """
        Clone repository or pull latest changes
        
        Args:
            url: Repository URL
            local_path: Local directory path
            branch: Branch name
            credential: VCS credential (with decrypted fields)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            env = os.environ.copy()
            
            # Setup authentication
            if credential:
                if credential.ssh_private_key:
                    # Create temporary SSH key file
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_rsa') as key_file:
                        # Ensure key ends with newline (required for SSH)
                        key_content = credential.ssh_private_key
                        if not key_content.endswith('\n'):
                            key_content += '\n'
                        key_file.write(key_content)
                        key_file.flush()  # Ensure key is written to disk
                        os.fsync(key_file.fileno())  # Force write to disk
                        key_path = key_file.name
                    
                    os.chmod(key_path, 0o600)
                    env['GIT_SSH_COMMAND'] = f'ssh -i {key_path} -o StrictHostKeyChecking=no -o IdentitiesOnly=yes'
                    self.temp_dirs.append(key_path)
                    logger.debug(f"Using SSH key from {key_path}")
                
                elif credential.token:
                    if url.startswith('https://'):
                        url = url.replace('https://', f'https://{credential.token}@')
            elif url.startswith('git@') or url.startswith('ssh://'):
                # For SSH URLs without credentials, still disable host key checking
                env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
            
            if not local_path.exists():
                # Clone repository
                logger.info(f"Cloning {url} to {local_path}")
                result = subprocess.run(
                    ['git', 'clone', '--branch', branch, url, str(local_path)],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=300
                )
                
                if result.returncode != 0:
                    logger.error(f"Clone failed: {result.stderr}")
                    return False
                
                logger.info(f"Successfully cloned {url}")
                return True
            else:
                # Pull latest changes
                logger.info(f"Pulling latest changes for {local_path}")
                result = subprocess.run(
                    ['git', '-C', str(local_path), 'pull', 'origin', branch],
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=300
                )
                
                if result.returncode != 0:
                    logger.error(f"Pull failed: {result.stderr}")
                    return False
                
                logger.info(f"Successfully pulled latest changes")
                return True
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout during git operation for {url}")
            return False
        except Exception as e:
            logger.error(f"Error during git operation: {e}")
            return False
        finally:
            self._cleanup()
    
    def find_inspec_profiles(self, repo_path) -> list:
        """
        Find InSpec profiles in repository
        
        Args:
            repo_path: Repository local path (str or Path)
            
        Returns:
            List of profile info dicts with 'path' and 'name'
        """
        profiles = []
        try:
            # Convert to Path if string
            if isinstance(repo_path, str):
                repo_path = Path(repo_path)
            
            for inspec_file in repo_path.rglob('inspec.yml'):
                profile_dir = inspec_file.parent
                profiles.append({
                    "path": str(profile_dir),
                    "name": profile_dir.name
                })
                logger.debug(f"Found InSpec profile: {profile_dir}")
        except Exception as e:
            logger.error(f"Error finding InSpec profiles: {e}")
        
        return profiles
    
    def _cleanup(self):
        """Cleanup temporary files"""
        for temp_file in self.temp_dirs:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_file}: {e}")
        self.temp_dirs = []
