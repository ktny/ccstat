# Makefile for ccmonitor Go version

# Binary name and output directory
BINARY_NAME=ccmonitor
BIN_DIR=bin
OUTPUT=$(BIN_DIR)/$(BINARY_NAME)

# Go build flags
GO_BUILD_FLAGS=-ldflags="-s -w"

# Default target
.PHONY: build
build:
	@mkdir -p $(BIN_DIR)
	go build $(GO_BUILD_FLAGS) -o $(OUTPUT) ./cmd/ccmonitor

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf $(BIN_DIR)

# Run the application
.PHONY: run
run: build
	./$(OUTPUT)

# Run with specific arguments
.PHONY: run-days
run-days: build
	./$(OUTPUT) --days 2

.PHONY: run-hours
run-hours: build
	./$(OUTPUT) --hours 6

# Run tests
.PHONY: test
test:
	go test -v ./...

# Test coverage
.PHONY: test-coverage
test-coverage:
	go test -v -cover ./...

# Test build without installing
.PHONY: test-build
test-build:
	go run ./cmd/ccmonitor --help

# Install to $GOPATH/bin
.PHONY: install
install:
	go install ./cmd/ccmonitor

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build      - Build the binary to bin/ccmonitor"
	@echo "  clean      - Remove build artifacts"
	@echo "  run        - Build and run with default options"
	@echo "  run-days   - Build and run with --days 2"
	@echo "  run-hours  - Build and run with --hours 6"
	@echo "  test       - Run Go tests"
	@echo "  test-coverage - Run Go tests with coverage"
	@echo "  test-build - Test build by running with --help"
	@echo "  install    - Install to \$$GOPATH/bin"
	@echo "  help       - Show this help message"