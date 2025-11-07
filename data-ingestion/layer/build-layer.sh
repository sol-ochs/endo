#!/bin/bash

# Build Lambda Layer for data-ingestion dependencies

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR="$SCRIPT_DIR/build"
OUTPUT_FILE="$SCRIPT_DIR/requests-layer.zip"

echo "Building Lambda Layer..."

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/python"

# Install dependencies
echo "Installing dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt" \
    -t "$BUILD_DIR/python" \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --python-version 3.11 \
    --upgrade

# Clean up unnecessary files to reduce size
echo "Cleaning up..."
cd "$BUILD_DIR"
find python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find python -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
find python -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
find python -name "*.pyc" -delete 2>/dev/null || true

# Create zip
echo "Creating zip..."
rm -f "$OUTPUT_FILE"
zip -r "$OUTPUT_FILE" python/ -q

SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo ""
echo "✅ Layer built: $OUTPUT_FILE"
echo "📊 Size: $SIZE"
