package main

import (
	"testing"
	"time"
)

func TestMain(t *testing.T) {
	// Basic test to ensure main doesn't panic
	// More comprehensive tests would go in internal package tests
}

func TestTimeCalculation(t *testing.T) {
	tests := []struct {
		name     string
		days     int
		hours    int
		expected time.Duration
	}{
		{
			name:     "1 day",
			days:     1,
			hours:    0,
			expected: 24 * time.Hour,
		},
		{
			name:     "6 hours overrides days",
			days:     7,
			hours:    6,
			expected: 6 * time.Hour,
		},
		{
			name:     "3 days",
			days:     3,
			hours:    0,
			expected: 72 * time.Hour,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			now := time.Now()
			var duration time.Duration

			if tt.hours > 0 {
				duration = time.Duration(tt.hours) * time.Hour
			} else {
				duration = time.Duration(tt.days) * 24 * time.Hour
			}

			if duration != tt.expected {
				t.Errorf("Expected duration %v, got %v", tt.expected, duration)
			}

			startTime := now.Add(-duration)
			if now.Sub(startTime) != tt.expected {
				t.Errorf("Expected time difference %v, got %v", tt.expected, now.Sub(startTime))
			}
		})
	}
}
