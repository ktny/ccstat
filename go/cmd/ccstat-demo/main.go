package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"os"
	"path/filepath"
	"time"
)

// Project represents a demo project with activity patterns
type Project struct {
	Name      string
	Path      string
	BaseHour  int     // Base hour for activity concentration
	Intensity float64 // Overall activity intensity (0.0 - 1.0)
}

// Event represents a single Claude session event
type Event struct {
	Timestamp    string                 `json:"timestamp"`
	SessionID    string                 `json:"sessionId"`
	Cwd          string                 `json:"cwd"`
	Message      map[string]interface{} `json:"message"`
	Usage        map[string]interface{} `json:"usage,omitempty"`
	IsTruncated  bool                   `json:"isTruncated"`
	IsEndOfChain bool                   `json:"isEndOfChain"`
	MessageID    string                 `json:"messageId"`
}

var demoProjects = []Project{
	{"demo-awesome-api", "/home/demo/projects/demo-awesome-api", 9, 0.8},
	{"demo-frontend-v2", "/home/demo/projects/demo-frontend-v2", 10, 0.7},
	{"demo-data-pipeline", "/home/demo/projects/demo-data-pipeline", 14, 0.9},
	{"demo-mobile-app", "/home/demo/projects/demo-mobile-app", 11, 0.6},
	{"demo-microservice-auth", "/home/demo/projects/demo-microservice-auth", 15, 0.75},
	{"demo-ml-experiments", "/home/demo/projects/demo-ml-experiments", 16, 0.85},
	{"demo-devops-toolkit", "/home/demo/projects/demo-devops-toolkit", 13, 0.5},
}

func main() {
	// Create demo directory
	demoDir := filepath.Join(os.Getenv("HOME"), ".claude", "projects", "demo")
	if err := os.MkdirAll(demoDir, 0755); err != nil {
		log.Fatalf("Failed to create demo directory: %v", err)
	}

	// Generate demo data for today
	now := time.Now()
	startTime := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location())

	for _, project := range demoProjects {
		if err := generateProjectData(demoDir, project, startTime); err != nil {
			log.Printf("Failed to generate data for %s: %v", project.Name, err)
		}
	}

	fmt.Println("Demo data generated successfully!")
	fmt.Printf("Data location: %s\n", demoDir)
	fmt.Println("\nNow run: ccstat")
}

func generateProjectData(baseDir string, project Project, startTime time.Time) error {
	sessionID := generateSessionID()
	filename := filepath.Join(baseDir, fmt.Sprintf("demo-%s.jsonl", project.Name))

	file, err := os.Create(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	// Generate events throughout the day with realistic patterns
	currentTime := startTime
	messageCount := 0

	for hour := 0; hour < 24; hour++ {
		// Calculate activity level for this hour
		activityLevel := calculateActivityLevel(hour, project.BaseHour, project.Intensity)

		// Skip hours with very low activity
		if activityLevel < 0.1 {
			currentTime = currentTime.Add(time.Hour)
			continue
		}

		// Number of events in this hour based on activity level
		eventCount := int(activityLevel * 30) // Max 30 events per hour

		for i := 0; i < eventCount; i++ {
			// Add some randomness to timing within the hour
			minutes := rand.Intn(60)
			seconds := rand.Intn(60)
			eventTime := currentTime.Add(time.Duration(minutes)*time.Minute + time.Duration(seconds)*time.Second)

			// Alternate between user and assistant messages
			if messageCount%2 == 0 {
				event := createUserEvent(sessionID, project.Path, eventTime)
				if err := writeEvent(file, event); err != nil {
					return err
				}
			} else {
				event := createAssistantEvent(sessionID, project.Path, eventTime)
				if err := writeEvent(file, event); err != nil {
					return err
				}
			}
			messageCount++

			// Add small gaps between messages (1-5 minutes)
			gap := time.Duration(rand.Intn(5)+1) * time.Minute
			currentTime = eventTime.Add(gap)
		}

		currentTime = startTime.Add(time.Duration(hour+1) * time.Hour)
	}

	return nil
}

func calculateActivityLevel(hour, baseHour int, intensity float64) float64 {
	// Create a bell curve centered around baseHour
	distance := float64(abs(hour - baseHour))

	// Main activity period (±2 hours from base)
	if distance <= 2 {
		return intensity * (1.0 - distance*0.15)
	}

	// Secondary activity periods (morning and afternoon)
	if (hour >= 9 && hour <= 11) || (hour >= 14 && hour <= 17) {
		return intensity * (0.5 + 0.3*rand.Float64())
	}

	// Low activity during off-hours
	if hour < 8 || hour > 20 {
		return intensity * 0.1 * rand.Float64()
	}

	// Moderate activity during working hours
	return intensity * (0.3 + 0.2*rand.Float64())
}

func createUserEvent(sessionID, cwd string, timestamp time.Time) Event {
	messages := []string{
		"Can you help me refactor this function?",
		"I need to implement a new feature for user authentication",
		"How can I optimize this database query?",
		"Please review this code and suggest improvements",
		"I'm getting an error with this API endpoint",
		"Can you explain how this algorithm works?",
		"Help me write tests for this component",
		"I need to fix this bug in production",
	}

	return Event{
		Timestamp: timestamp.Format(time.RFC3339),
		SessionID: sessionID,
		Cwd:       cwd,
		Message: map[string]interface{}{
			"role": "user",
			"content": []map[string]interface{}{
				{
					"type": "text",
					"text": messages[rand.Intn(len(messages))],
				},
			},
		},
		IsTruncated:  false,
		IsEndOfChain: false,
		MessageID:    generateMessageID(),
	}
}

func createAssistantEvent(sessionID, cwd string, timestamp time.Time) Event {
	// Random token counts for realistic visualization
	inputTokens := rand.Intn(500) + 100
	outputTokens := rand.Intn(2000) + 500

	responses := []string{
		"I'll help you refactor that function. Here's an improved version...",
		"Let me implement a secure authentication feature for you...",
		"I can optimize that query. Here's a more efficient approach...",
		"I've reviewed your code and have several suggestions...",
		"I see the issue with your API endpoint. Let me fix that...",
		"This algorithm uses dynamic programming. Let me explain...",
		"I'll write comprehensive tests for your component...",
		"I've identified the bug. Here's the solution...",
	}

	return Event{
		Timestamp: timestamp.Format(time.RFC3339),
		SessionID: sessionID,
		Cwd:       cwd,
		Message: map[string]interface{}{
			"role": "assistant",
			"content": []map[string]interface{}{
				{
					"type": "text",
					"text": responses[rand.Intn(len(responses))],
				},
			},
		},
		Usage: map[string]interface{}{
			"input_tokens":  inputTokens,
			"output_tokens": outputTokens,
		},
		IsTruncated:  false,
		IsEndOfChain: rand.Float32() < 0.3, // 30% chance to end chain
		MessageID:    generateMessageID(),
	}
}

func writeEvent(file *os.File, event Event) error {
	data, err := json.Marshal(event)
	if err != nil {
		return err
	}
	_, err = file.Write(append(data, '\n'))
	return err
}

func generateSessionID() string {
	return fmt.Sprintf("session-%d", time.Now().Unix())
}

func generateMessageID() string {
	return fmt.Sprintf("msg-%d-%d", time.Now().UnixNano(), rand.Intn(10000))
}

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}
