package updater

import (
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

// Version represents a semantic version
type Version struct {
	Major int
	Minor int
	Patch int
	Pre   string // prerelease identifier (e.g., "alpha.1", "beta.2")
}

// ParseVersion parses a version string (e.g., "v1.2.3", "1.2.3-alpha.1")
func ParseVersion(versionStr string) (*Version, error) {
	// Remove 'v' prefix if present
	versionStr = strings.TrimPrefix(versionStr, "v")

	// Regular expression for semantic versioning
	re := regexp.MustCompile(`^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?$`)
	matches := re.FindStringSubmatch(versionStr)

	if matches == nil {
		return nil, fmt.Errorf("invalid version format: %s", versionStr)
	}

	major, err := strconv.Atoi(matches[1])
	if err != nil {
		return nil, fmt.Errorf("invalid major version: %s", matches[1])
	}

	minor, err := strconv.Atoi(matches[2])
	if err != nil {
		return nil, fmt.Errorf("invalid minor version: %s", matches[2])
	}

	patch, err := strconv.Atoi(matches[3])
	if err != nil {
		return nil, fmt.Errorf("invalid patch version: %s", matches[3])
	}

	pre := ""
	if len(matches) > 4 {
		pre = matches[4]
	}

	return &Version{
		Major: major,
		Minor: minor,
		Patch: patch,
		Pre:   pre,
	}, nil
}

// String returns the string representation of the version
func (v *Version) String() string {
	version := fmt.Sprintf("%d.%d.%d", v.Major, v.Minor, v.Patch)
	if v.Pre != "" {
		version += "-" + v.Pre
	}
	return version
}

// IsNewerThan returns true if this version is newer than the other version
func (v *Version) IsNewerThan(other *Version) bool {
	// Compare major version
	if v.Major != other.Major {
		return v.Major > other.Major
	}

	// Compare minor version
	if v.Minor != other.Minor {
		return v.Minor > other.Minor
	}

	// Compare patch version
	if v.Patch != other.Patch {
		return v.Patch > other.Patch
	}

	// Compare prerelease versions
	// If one has prerelease and other doesn't, the one without prerelease is newer
	if v.Pre == "" && other.Pre != "" {
		return true
	}
	if v.Pre != "" && other.Pre == "" {
		return false
	}

	// Both have prerelease or both don't - compare lexicographically
	return v.Pre > other.Pre
}

// IsUpdateAvailable checks if an update is available
func IsUpdateAvailable(currentVersion, latestVersion string) (bool, *Version, *Version, error) {
	current, err := ParseVersion(currentVersion)
	if err != nil {
		return false, nil, nil, fmt.Errorf("invalid current version: %w", err)
	}

	latest, err := ParseVersion(latestVersion)
	if err != nil {
		return false, nil, nil, fmt.Errorf("invalid latest version: %w", err)
	}

	return latest.IsNewerThan(current), current, latest, nil
}
