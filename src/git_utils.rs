use std::fs;
use std::path::Path;

pub fn get_repository_name(directory: &str) -> Option<String> {
    let git_path = Path::new(directory).join(".git");
    
    if !git_path.exists() {
        return None;
    }

    let config_file = if git_path.is_file() {
        // Handle git worktree case where .git is a file
        let git_content = fs::read_to_string(&git_path).ok()?;
        
        if git_content.starts_with("gitdir: ") {
            let actual_git_dir = Path::new(&git_content.trim()[8..]);
            
            // For worktree, check if commondir exists to find main git dir
            let commondir_file = actual_git_dir.join("commondir");
            if commondir_file.exists() {
                let common_path = fs::read_to_string(&commondir_file).ok()?;
                let main_git_dir = actual_git_dir.join(common_path.trim());
                main_git_dir.join("config")
            } else {
                actual_git_dir.join("config")
            }
        } else {
            return None;
        }
    } else {
        // Regular git repository
        git_path.join("config")
    };

    if !config_file.exists() {
        return None;
    }

    let content = fs::read_to_string(&config_file).ok()?;
    
    // Look for remote origin URL
    for line in content.lines() {
        if line.trim().starts_with("url = ") {
            let url = line.trim().strip_prefix("url = ")?.trim();
            
            // Extract repo name from various URL formats
            // SSH format: git@github.com:user/repo.git
            // HTTPS format: https://github.com/user/repo.git
            
            if let Some(repo_name) = extract_repo_name_from_url(url) {
                return Some(repo_name);
            }
        }
    }

    None
}

fn extract_repo_name_from_url(url: &str) -> Option<String> {
    // SSH format: git@github.com:user/repo.git
    if url.contains(':') && !url.starts_with("http") {
        if let Some(repo_part) = url.split(':').nth(1) {
            if let Some(repo_name) = repo_part.split('/').last() {
                return Some(repo_name.strip_suffix(".git").unwrap_or(repo_name).to_string());
            }
        }
    }
    
    // HTTPS format: https://github.com/user/repo.git
    if url.starts_with("http") {
        if let Some(repo_name) = url.split('/').last() {
            return Some(repo_name.strip_suffix(".git").unwrap_or(repo_name).to_string());
        }
    }
    
    None
}