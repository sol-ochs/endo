#!/bin/bash
set -e

echo "Packaging Lambda function..."

# Ensure cleanup on script exit (even if an error occurs)
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT
echo "Using temporary directory: $TEMP_DIR"

# Navigate to API directory
API_DIR="$(dirname "$0")/../user-management-api"
cd "$API_DIR"

# Install dependencies to temp directory
echo "Installing dependencies..."
source .venv/bin/activate
pip install \
-r requirements.txt \
-t "$TEMP_DIR" \
--platform manylinux2014_x86_64 \
--python-version 3.11 \
--only-binary=:all:
deactivate

# Copy application code to temp directory
echo "Copying application code..."
cp -r app "$TEMP_DIR/"
cp lambda_function.py "$TEMP_DIR/"

# Create deployment package
echo "Creating deployment.zip..."
pushd "$TEMP_DIR"
zip -r deployment.zip . -x "*.pyc" -x "*__pycache__*"
popd

# Create package directory if not exists
PACKAGE_DIR="$(pwd)/lambda-package"
mkdir -p "$PACKAGE_DIR"

# Transfer the completed zip file
mv "$TEMP_DIR/deployment.zip" "$PACKAGE_DIR/"

echo "Lambda package created: $PACKAGE_DIR/deployment.zip"
echo "Size: $(du -h "$PACKAGE_DIR/deployment.zip" | cut -f1)"