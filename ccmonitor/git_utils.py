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
    git_path = Path(directory) / ".git"
    if not git_path.exists():
        return None

    try:
        # Handle git worktree case where .git is a file
        if git_path.is_file():
            # Read gitdir path from .git file
            with git_path.open("r") as f:
                git_content = f.read().strip()
            
            # Extract gitdir path (format: "gitdir: /path/to/actual/git/dir")
            if git_content.startswith("gitdir: "):
                actual_git_dir = Path(git_content[8:])  # Remove "gitdir: " prefix
                
                # For worktree, check if commondir exists to find main git dir
                commondir_file = actual_git_dir / "commondir"
                if commondir_file.exists():
                    with commondir_file.open("r") as f:
                        common_path = f.read().strip()
                    # Resolve relative path from worktree git dir
                    main_git_dir = actual_git_dir / common_path
                    config_file = main_git_dir / "config"
                else:
                    config_file = actual_git_dir / "config"
            else:
                return None
        else:
            # Regular git repository
            config_file = git_path / "config"

        if not config_file.exists():
            return None

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
