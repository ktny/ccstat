# Makefile for ccstat Go version

# Binary name and output directory
BINARY_NAME=ccstat
BIN_DIR=bin
OUTPUT=$(BIN_DIR)/$(BINARY_NAME)

# Version information
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
COMMIT_HASH ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BUILD_DATE ?= $(shell date -u +"%Y-%m-%d %H:%M:%S UTC")

# Go build flags with version injection
GO_BUILD_FLAGS=-ldflags="-s -w -X 'main.versionString=$(VERSION)' -X 'main.commitHash=$(COMMIT_HASH)' -X 'main.buildDate=$(BUILD_DATE)'"

# Default target
.PHONY: build
build:
	@mkdir -p $(BIN_DIR)
	go build $(GO_BUILD_FLAGS) -o $(OUTPUT) ./cmd/ccstat

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
	go run ./cmd/ccstat --help

# Install to $GOPATH/bin
.PHONY: install
install:
	go install ./cmd/ccstat

# Show version information
.PHONY: version
version: build
	./$(OUTPUT) --version

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build      - Build the binary to bin/ccstat"
	@echo "  clean      - Remove build artifacts"
	@echo "  run        - Build and run with default options"
	@echo "  run-days   - Build and run with --days 2"
	@echo "  run-hours  - Build and run with --hours 6"
	@echo "  test       - Run Go tests"
	@echo "  test-coverage - Run Go tests with coverage"
	@echo "  test-build - Test build by running with --help"
	@echo "  install    - Install to \$$GOPATH/bin"
	@echo "  version    - Build and show version information"
	@echo "  help       - Show this help message"