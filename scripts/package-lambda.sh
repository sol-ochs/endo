#!/bin/bash
set -e

echo "Packaging Lambda function..."

# Navigate to the API directory
cd "$(dirname "$0")/../user-management-api"

# Create lambda-package directory if it doesn't exist
mkdir -p lambda-package

# Create a temporary directory for the package
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Install dependencies to temp directory
echo "Installing dependencies..."
pip install -r requirements.txt -t "$TEMP_DIR" --platform manylinux2014_x86_64 --only-binary=:all:

# Copy application code
echo "Copying application code..."
cp -r app "$TEMP_DIR/"
cp lambda_function.py "$TEMP_DIR/"

# Create deployment package
echo "Creating deployment.zip..."
cd "$TEMP_DIR"
zip -r deployment.zip . -x "*.pyc" -x "*__pycache__*" -x "*.dist-info*"

# Move to lambda-package directory
mv deployment.zip "$(dirname "$0")/../user-management-api/lambda-package/"

# Cleanup
cd -
rm -rf "$TEMP_DIR"

echo "✓ Lambda package created: lambda-package/deployment.zip"
echo "Size: $(du -h lambda-package/deployment.zip | cut -f1)"
