#!/bin/bash
# Build shared Lambda layer for glucose data models and utilities

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR="$SCRIPT_DIR/build"
OUTPUT_ZIP="$SCRIPT_DIR/shared-layer.zip"

echo "Building shared Lambda layer..."

# Clean previous build
rm -rf "$BUILD_DIR"
rm -f "$OUTPUT_ZIP"

# Create layer directory structure
mkdir -p "$BUILD_DIR/python"

# Copy shared modules
cp -r "$SCRIPT_DIR"/*.py "$BUILD_DIR/python/"
cp -r "$SCRIPT_DIR"/adapters "$BUILD_DIR/python/"

# Create zip
cd "$BUILD_DIR"
zip -r "$OUTPUT_ZIP" python/

echo "Shared layer built: $OUTPUT_ZIP"
ls -lh "$OUTPUT_ZIP"