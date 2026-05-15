#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Define variables for easier maintenance
MANIFEST="org.csearch.CSearch.yml"
APP_ID="org.csearch.CSearch"
BUILD_DIR="build-dir"
REPO_DIR="repo"
OUTPUT_BUNDLE="CSearch.flatpak"

echo -e "${GREEN}Starting Flatpak build process...${NC}"

# Check for required dependencies
for cmd in flatpak flatpak-builder; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: '$cmd' is not installed or not in PATH.${NC}"
        exit 1
    fi
done

# Ensure manifest exists
if [ ! -f "$MANIFEST" ]; then
    echo -e "${RED}Error: Manifest file '$MANIFEST' not found in the current directory.${NC}"
    exit 1
fi

echo -e "${GREEN}Building the application with flatpak-builder...${NC}"
if ! flatpak-builder --repo="$REPO_DIR" --force-clean "$BUILD_DIR" "$MANIFEST"; then
    echo -e "${RED}Error: flatpak-builder failed! Check the output above for details.${NC}"
    exit 1
fi

echo -e "${GREEN}Exporting the build to a single-file bundle...${NC}"
if ! flatpak build-bundle "$REPO_DIR" "$OUTPUT_BUNDLE" "$APP_ID"; then
    echo -e "${RED}Error: Failed to create the flatpak bundle!${NC}"
    exit 1
fi

echo -e "${GREEN}Finished successfully! Bundle created at: $OUTPUT_BUNDLE${NC}"
