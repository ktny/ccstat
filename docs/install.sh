#!/bin/sh
# ccstat installer script
# https://github.com/ktny/ccstat
#
# Usage:
#   curl -fsSL https://ktny.github.io/ccstat/install.sh | sh
#   wget -qO- https://ktny.github.io/ccstat/install.sh | sh
#
# Options:
#   -v, --version VERSION    Install specific version (default: latest)
#   -p, --prefix PATH       Install to specific directory (default: auto-detect)
#   -h, --help              Show help

set -e

# Configuration
REPO_OWNER="ktny"
REPO_NAME="ccstat"
BINARY_NAME="ccstat"
GITHUB_API="https://api.github.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Helper functions
info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"
}

warn() {
    printf "${YELLOW}[WARN]${NC} %s\n" "$1"
}

error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1"
    exit 1
}

# Detect OS
detect_os() {
    OS="$(uname -s)"
    case "${OS}" in
        Linux*)     OS=linux;;
        Darwin*)    OS=darwin;;
        *)          error "Unsupported OS: ${OS}";;
    esac
    echo "${OS}"
}

# Detect architecture
detect_arch() {
    ARCH="$(uname -m)"
    case "${ARCH}" in
        x86_64|amd64)   ARCH=amd64;;
        aarch64|arm64)  ARCH=arm64;;
        *)              error "Unsupported architecture: ${ARCH}";;
    esac
    echo "${ARCH}"
}

# Get latest release version from GitHub
get_latest_version() {
    info "Fetching latest version..." >&2
    VERSION=$(curl -s "${GITHUB_API}/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    if [ -z "${VERSION}" ]; then
        error "Failed to fetch latest version"
    fi
    echo "${VERSION}"
}

# Determine install directory
get_install_dir() {
    # Check if user has sudo access
    if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        echo "/usr/local/bin"
    else
        # Use user's local bin directory
        LOCAL_BIN="${HOME}/.local/bin"
        mkdir -p "${LOCAL_BIN}"
        echo "${LOCAL_BIN}"
    fi
}

# Check if directory is in PATH
check_path() {
    DIR="$1"
    case ":${PATH}:" in
        *:"${DIR}":*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Download and install binary
install_binary() {
    OS="$1"
    ARCH="$2"
    VERSION="$3"
    INSTALL_DIR="$4"
    
    BINARY_NAME_FULL="${BINARY_NAME}-${OS}-${ARCH}"
    DOWNLOAD_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/download/${VERSION}/${BINARY_NAME_FULL}"
    
    info "Downloading ${BINARY_NAME} ${VERSION} for ${OS}/${ARCH}..."
    info "URL: ${DOWNLOAD_URL}"
    
    # Create temp directory
    TMP_DIR=$(mktemp -d)
    trap "rm -rf ${TMP_DIR}" EXIT
    
    # Download binary
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "${DOWNLOAD_URL}" -o "${TMP_DIR}/${BINARY_NAME}" || error "Failed to download ${BINARY_NAME}"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "${DOWNLOAD_URL}" -O "${TMP_DIR}/${BINARY_NAME}" || error "Failed to download ${BINARY_NAME}"
    else
        error "Neither curl nor wget found. Please install one of them."
    fi
    
    # Make executable
    chmod +x "${TMP_DIR}/${BINARY_NAME}"
    
    # Install binary
    info "Installing ${BINARY_NAME} to ${INSTALL_DIR}..."
    if [ "${INSTALL_DIR}" = "/usr/local/bin" ]; then
        sudo mv "${TMP_DIR}/${BINARY_NAME}" "${INSTALL_DIR}/" || error "Failed to install ${BINARY_NAME}"
    else
        mv "${TMP_DIR}/${BINARY_NAME}" "${INSTALL_DIR}/" || error "Failed to install ${BINARY_NAME}"
    fi
}

# Show usage
usage() {
    cat <<EOF
ccstat installer

Usage:
    curl -fsSL https://ktny.github.io/ccstat/install.sh | sh
    wget -qO- https://ktny.github.io/ccstat/install.sh | sh

Options:
    -v, --version VERSION    Install specific version (default: latest)
    -p, --prefix PATH       Install to specific directory (default: auto-detect)
    -h, --help              Show this help message

Examples:
    # Install latest version
    curl -fsSL https://ktny.github.io/ccstat/install.sh | sh
    
    # Install specific version
    curl -fsSL https://ktny.github.io/ccstat/install.sh | sh -s -- --version v0.1.0
    
    # Install to custom directory
    curl -fsSL https://ktny.github.io/ccstat/install.sh | sh -s -- --prefix \$HOME/bin

EOF
}

# Main installation process
main() {
    VERSION=""
    INSTALL_DIR=""
    
    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -p|--prefix)
                INSTALL_DIR="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    info "Installing ccstat..."
    
    # Detect OS and architecture
    OS=$(detect_os)
    ARCH=$(detect_arch)
    info "Detected: ${OS}/${ARCH}"
    
    # Get version if not specified
    if [ -z "${VERSION}" ]; then
        VERSION=$(get_latest_version)
    fi
    info "Version: ${VERSION}"
    
    # Get install directory if not specified
    if [ -z "${INSTALL_DIR}" ]; then
        INSTALL_DIR=$(get_install_dir)
    fi
    info "Install directory: ${INSTALL_DIR}"
    
    # Install binary
    install_binary "${OS}" "${ARCH}" "${VERSION}" "${INSTALL_DIR}"
    
    # Check if install directory is in PATH
    if ! check_path "${INSTALL_DIR}"; then
        warn "${INSTALL_DIR} is not in your PATH"
        warn "Add the following line to your shell profile:"
        warn "  export PATH=\"${INSTALL_DIR}:\$PATH\""
    fi
    
    # Verify installation
    if command -v "${BINARY_NAME}" >/dev/null 2>&1; then
        INSTALLED_VERSION=$("${BINARY_NAME}" --version 2>&1 | head -n1)
        success "ccstat installed successfully!"
        success "Version: ${INSTALLED_VERSION}"
        info "Run 'ccstat --help' to get started"
    else
        warn "ccstat was installed to ${INSTALL_DIR} but is not in your PATH"
        warn "Run '${INSTALL_DIR}/ccstat --help' to get started"
    fi
}

# Run main function
main "$@"