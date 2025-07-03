package updater

import (
	"testing"
)

func TestParseVersion(t *testing.T) {
	tests := []struct {
		input       string
		expectError bool
		expected    *Version
	}{
		{
			input:       "1.2.3",
			expectError: false,
			expected:    &Version{Major: 1, Minor: 2, Patch: 3, Pre: ""},
		},
		{
			input:       "v1.2.3",
			expectError: false,
			expected:    &Version{Major: 1, Minor: 2, Patch: 3, Pre: ""},
		},
		{
			input:       "1.2.3-alpha.1",
			expectError: false,
			expected:    &Version{Major: 1, Minor: 2, Patch: 3, Pre: "alpha.1"},
		},
		{
			input:       "v0.1.0-beta.2",
			expectError: false,
			expected:    &Version{Major: 0, Minor: 1, Patch: 0, Pre: "beta.2"},
		},
		{
			input:       "invalid",
			expectError: true,
			expected:    nil,
		},
		{
			input:       "1.2",
			expectError: true,
			expected:    nil,
		},
		{
			input:       "1.2.3.4",
			expectError: true,
			expected:    nil,
		},
	}

	for _, test := range tests {
		t.Run(test.input, func(t *testing.T) {
			result, err := ParseVersion(test.input)

			if test.expectError {
				if err == nil {
					t.Errorf("Expected error for input %s, but got none", test.input)
				}
				return
			}

			if err != nil {
				t.Errorf("Unexpected error for input %s: %v", test.input, err)
				return
			}

			if result.Major != test.expected.Major ||
				result.Minor != test.expected.Minor ||
				result.Patch != test.expected.Patch ||
				result.Pre != test.expected.Pre {
				t.Errorf("For input %s, expected %+v, got %+v", test.input, test.expected, result)
			}
		})
	}
}

func TestVersionString(t *testing.T) {
	tests := []struct {
		version  *Version
		expected string
	}{
		{
			version:  &Version{Major: 1, Minor: 2, Patch: 3, Pre: ""},
			expected: "1.2.3",
		},
		{
			version:  &Version{Major: 1, Minor: 2, Patch: 3, Pre: "alpha.1"},
			expected: "1.2.3-alpha.1",
		},
		{
			version:  &Version{Major: 0, Minor: 1, Patch: 0, Pre: ""},
			expected: "0.1.0",
		},
	}

	for _, test := range tests {
		t.Run(test.expected, func(t *testing.T) {
			result := test.version.String()
			if result != test.expected {
				t.Errorf("Expected %s, got %s", test.expected, result)
			}
		})
	}
}

func TestIsNewerThan(t *testing.T) {
	tests := []struct {
		version1 string
		version2 string
		expected bool
		desc     string
	}{
		{"1.2.3", "1.2.2", true, "patch version newer"},
		{"1.2.3", "1.2.3", false, "same version"},
		{"1.2.3", "1.2.4", false, "patch version older"},
		{"1.3.0", "1.2.9", true, "minor version newer"},
		{"1.2.0", "1.3.0", false, "minor version older"},
		{"2.0.0", "1.9.9", true, "major version newer"},
		{"1.0.0", "2.0.0", false, "major version older"},
		{"1.2.3", "1.2.3-alpha.1", true, "release newer than prerelease"},
		{"1.2.3-alpha.1", "1.2.3", false, "prerelease older than release"},
		{"1.2.3-beta.1", "1.2.3-alpha.1", true, "later prerelease"},
		{"1.2.3-alpha.1", "1.2.3-beta.1", false, "earlier prerelease"},
	}

	for _, test := range tests {
		t.Run(test.desc, func(t *testing.T) {
			v1, err := ParseVersion(test.version1)
			if err != nil {
				t.Fatalf("Failed to parse version1 %s: %v", test.version1, err)
			}

			v2, err := ParseVersion(test.version2)
			if err != nil {
				t.Fatalf("Failed to parse version2 %s: %v", test.version2, err)
			}

			result := v1.IsNewerThan(v2)
			if result != test.expected {
				t.Errorf("For %s vs %s, expected %t, got %t", test.version1, test.version2, test.expected, result)
			}
		})
	}
}

func TestIsUpdateAvailable(t *testing.T) {
	tests := []struct {
		currentVersion string
		latestVersion  string
		expectedUpdate bool
		expectError    bool
		desc           string
	}{
		{"1.2.2", "1.2.3", true, false, "update available"},
		{"1.2.3", "1.2.3", false, false, "no update needed"},
		{"1.2.4", "1.2.3", false, false, "current newer than latest"},
		{"v1.2.2", "v1.2.3", true, false, "update available with v prefix"},
		{"invalid", "1.2.3", false, true, "invalid current version"},
		{"1.2.3", "invalid", false, true, "invalid latest version"},
	}

	for _, test := range tests {
		t.Run(test.desc, func(t *testing.T) {
			updateAvailable, current, latest, err := IsUpdateAvailable(test.currentVersion, test.latestVersion)

			if test.expectError {
				if err == nil {
					t.Errorf("Expected error for %s vs %s, but got none", test.currentVersion, test.latestVersion)
				}
				return
			}

			if err != nil {
				t.Errorf("Unexpected error for %s vs %s: %v", test.currentVersion, test.latestVersion, err)
				return
			}

			if updateAvailable != test.expectedUpdate {
				t.Errorf("For %s vs %s, expected update=%t, got %t", test.currentVersion, test.latestVersion, test.expectedUpdate, updateAvailable)
			}

			if current == nil || latest == nil {
				t.Errorf("Expected non-nil version objects")
			}
		})
	}
}
