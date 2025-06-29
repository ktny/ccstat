package updater

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"runtime"
	"time"
)

// GitHubRelease represents a GitHub release
type GitHubRelease struct {
	TagName string `json:"tag_name"`
	Name    string `json:"name"`
	Assets  []struct {
		Name               string `json:"name"`
		BrowserDownloadURL string `json:"browser_download_url"`
		Size               int64  `json:"size"`
	} `json:"assets"`
	Prerelease bool   `json:"prerelease"`
	Draft      bool   `json:"draft"`
	CreatedAt  string `json:"created_at"`
}

// Client handles GitHub API communication for updates
type Client struct {
	owner      string
	repo       string
	httpClient *http.Client
}

// NewClient creates a new GitHub API client for updates
func NewClient(owner, repo string) *Client {
	return &Client{
		owner: owner,
		repo:  repo,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// GetLatestRelease fetches the latest release from GitHub
func (c *Client) GetLatestRelease() (*GitHubRelease, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s/releases/latest", c.owner, c.repo)

	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch latest release: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("GitHub API returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	var release GitHubRelease
	if err := json.Unmarshal(body, &release); err != nil {
		return nil, fmt.Errorf("failed to parse release JSON: %w", err)
	}

	// Skip prerelease and draft releases
	if release.Prerelease || release.Draft {
		return nil, fmt.Errorf("latest release is prerelease or draft")
	}

	return &release, nil
}

// FindAssetForCurrentPlatform finds the appropriate binary asset for the current platform
func (c *Client) FindAssetForCurrentPlatform(release *GitHubRelease) (string, string, error) {
	osName := runtime.GOOS
	archName := runtime.GOARCH

	// Map Go OS names to expected binary names
	expectedPattern := fmt.Sprintf("ccstat-%s-%s", osName, archName)

	for _, asset := range release.Assets {
		if asset.Name == expectedPattern {
			return asset.Name, asset.BrowserDownloadURL, nil
		}
	}

	return "", "", fmt.Errorf("no binary found for %s/%s", osName, archName)
}

// DownloadFile downloads a file from the given URL
func (c *Client) DownloadFile(url string) ([]byte, error) {
	resp, err := c.httpClient.Get(url)
	if err != nil {
		return nil, fmt.Errorf("failed to download file: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("download failed with status %d", resp.StatusCode)
	}

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read download data: %w", err)
	}

	return data, nil
}
