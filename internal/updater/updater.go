package updater

import (
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
)

// Updater handles the update process
type Updater struct {
	client         *Client
	currentVersion string
	executablePath string
}

// NewUpdater creates a new updater instance
func NewUpdater(owner, repo, currentVersion string) (*Updater, error) {
	execPath, err := os.Executable()
	if err != nil {
		return nil, fmt.Errorf("failed to get executable path: %w", err)
	}

	// Resolve symlinks to get the actual executable path
	execPath, err = filepath.EvalSymlinks(execPath)
	if err != nil {
		return nil, fmt.Errorf("failed to resolve executable path: %w", err)
	}

	return &Updater{
		client:         NewClient(owner, repo),
		currentVersion: currentVersion,
		executablePath: execPath,
	}, nil
}

// CheckForUpdate checks if an update is available
func (u *Updater) CheckForUpdate() (*UpdateInfo, error) {
	release, err := u.client.GetLatestRelease()
	if err != nil {
		return nil, fmt.Errorf("failed to get latest release: %w", err)
	}

	available, current, latest, err := IsUpdateAvailable(u.currentVersion, release.TagName)
	if err != nil {
		return nil, fmt.Errorf("failed to compare versions: %w", err)
	}

	info := &UpdateInfo{
		Available:      available,
		CurrentVersion: current,
		LatestVersion:  latest,
		Release:        release,
	}

	if available {
		assetName, downloadURL, err := u.client.FindAssetForCurrentPlatform(release)
		if err != nil {
			return nil, fmt.Errorf("failed to find asset for platform: %w", err)
		}
		info.AssetName = assetName
		info.DownloadURL = downloadURL
	}

	return info, nil
}

// PerformUpdate downloads and installs the update
func (u *Updater) PerformUpdate() error {
	updateInfo, err := u.CheckForUpdate()
	if err != nil {
		return fmt.Errorf("failed to check for update: %w", err)
	}

	if !updateInfo.Available {
		return fmt.Errorf("no update available")
	}

	fmt.Printf("Downloading %s from %s...\n", updateInfo.AssetName, updateInfo.DownloadURL)

	// Download the new binary
	data, err := u.client.DownloadFile(updateInfo.DownloadURL)
	if err != nil {
		return fmt.Errorf("failed to download update: %w", err)
	}

	// Create a temporary file
	tempDir := os.TempDir()
	tempFile := filepath.Join(tempDir, fmt.Sprintf("ccstat-update-%d", os.Getpid()))

	// Write to temporary file
	if err := os.WriteFile(tempFile, data, 0755); err != nil {
		return fmt.Errorf("failed to write temporary file: %w", err)
	}
	defer func() {
		_ = os.Remove(tempFile) // Clean up temp file
	}()

	// Verify the downloaded file (basic check that it's executable)
	if err := u.verifyBinary(tempFile); err != nil {
		return fmt.Errorf("binary verification failed: %w", err)
	}

	// Create backup of current binary
	backupPath := u.executablePath + ".backup"
	if err := u.createBackup(backupPath); err != nil {
		return fmt.Errorf("failed to create backup: %w", err)
	}

	// Attempt to replace the binary
	if err := u.replaceBinary(tempFile); err != nil {
		// Try to restore backup on failure
		if restoreErr := u.restoreBackup(backupPath); restoreErr != nil {
			return fmt.Errorf("failed to replace binary and restore backup: %v (original error: %v)", restoreErr, err)
		}
		return fmt.Errorf("failed to replace binary (backup restored): %w", err)
	}

	// Clean up backup file
	_ = os.Remove(backupPath)

	fmt.Printf("Successfully updated to version %s\n", updateInfo.LatestVersion.String())
	return nil
}

// createBackup creates a backup of the current executable
func (u *Updater) createBackup(backupPath string) error {
	sourceFile, err := os.Open(u.executablePath)
	if err != nil {
		return fmt.Errorf("failed to open source file: %w", err)
	}
	defer sourceFile.Close()

	backupFile, err := os.Create(backupPath)
	if err != nil {
		return fmt.Errorf("failed to create backup file: %w", err)
	}
	defer backupFile.Close()

	if _, err := io.Copy(backupFile, sourceFile); err != nil {
		return fmt.Errorf("failed to copy to backup: %w", err)
	}

	// Copy permissions
	sourceInfo, err := os.Stat(u.executablePath)
	if err != nil {
		return fmt.Errorf("failed to get source file info: %w", err)
	}

	if err := os.Chmod(backupPath, sourceInfo.Mode()); err != nil {
		return fmt.Errorf("failed to set backup file permissions: %w", err)
	}

	return nil
}

// restoreBackup restores the backup file
func (u *Updater) restoreBackup(backupPath string) error {
	return os.Rename(backupPath, u.executablePath)
}

// replaceBinary replaces the current binary with the new one
func (u *Updater) replaceBinary(newBinaryPath string) error {
	// On Windows, we might need special handling due to file locking
	if runtime.GOOS == "windows" {
		return u.replaceBinaryWindows(newBinaryPath)
	}

	// On Unix-like systems, atomic replacement
	return os.Rename(newBinaryPath, u.executablePath)
}

// replaceBinaryWindows handles binary replacement on Windows
func (u *Updater) replaceBinaryWindows(newBinaryPath string) error {
	// On Windows, we can't replace a running executable
	// Move current executable to temp name, then move new one in place
	tempOldPath := u.executablePath + ".old"

	// Move current executable out of the way
	if err := os.Rename(u.executablePath, tempOldPath); err != nil {
		return fmt.Errorf("failed to move current executable: %w", err)
	}

	// Move new executable into place
	if err := os.Rename(newBinaryPath, u.executablePath); err != nil {
		// Try to restore original
		_ = os.Rename(tempOldPath, u.executablePath)
		return fmt.Errorf("failed to move new executable: %w", err)
	}

	// Clean up old executable
	_ = os.Remove(tempOldPath)

	return nil
}

// verifyBinary performs basic verification of the downloaded binary
func (u *Updater) verifyBinary(binaryPath string) error {
	// Check if file exists and is executable
	info, err := os.Stat(binaryPath)
	if err != nil {
		return fmt.Errorf("failed to stat binary: %w", err)
	}

	// Check if it's a regular file
	if !info.Mode().IsRegular() {
		return fmt.Errorf("downloaded file is not a regular file")
	}

	// Check file size (should be reasonable for a binary)
	if info.Size() < 1024 || info.Size() > 100*1024*1024 {
		return fmt.Errorf("binary size %d bytes seems invalid", info.Size())
	}

	return nil
}

// CalculateHash calculates SHA256 hash of a file
func (u *Updater) CalculateHash(filePath string) (string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		return "", err
	}

	return fmt.Sprintf("%x", hash.Sum(nil)), nil
}

// UpdateInfo contains information about available updates
type UpdateInfo struct {
	Available      bool
	CurrentVersion *Version
	LatestVersion  *Version
	Release        *GitHubRelease
	AssetName      string
	DownloadURL    string
}
