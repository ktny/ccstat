"""Git utility functions for extracting repository information."""

import re
from pathlib import Path


def get_repository_name(directory: str) -> str | None:
    """Extract repository name from git config.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Repository name if found, None otherwise
    """
    git_dir = Path(directory) / ".git"
    if not git_dir.exists():
        return None
    
    config_file = git_dir / "config"
    if not config_file.exists():
        return None
    
    try:
        with config_file.open("r") as f:
            content = f.read()
            
        # Look for remote origin URL
        # Pattern matches lines like: url = git@github.com:user/repo.git
        # or: url = https://github.com/user/repo.git
        url_pattern = r'url\s*=\s*(.+)'
        url_match = re.search(url_pattern, content)
        
        if url_match:
            url = url_match.group(1).strip()
            
            # Extract repo name from various URL formats
            # SSH format: git@github.com:user/repo.git
            ssh_pattern = r'[^:/]+/([^/]+?)(?:\.git)?$'
            # HTTPS format: https://github.com/user/repo.git
            https_pattern = r'/([^/]+?)(?:\.git)?$'
            
            repo_match = re.search(ssh_pattern, url) or re.search(https_pattern, url)
            if repo_match:
                return repo_match.group(1)
                
    except Exception:
        pass
    
    return None