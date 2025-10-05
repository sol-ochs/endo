#!/bin/bash

# Script to package the Lambda function for deployment
# Usage: ./scripts/package-lambda.sh

set -e

echo "Packaging Lambda function for deployment..."

# Define paths
PROJECT_ROOT=$(pwd)
BACKEND_DIR="user-management-api"
PACKAGE_DIR="lambda-package"
ZIP_FILE="lambda-package.zip"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Clean up previous package
if [ -d "$PACKAGE_DIR" ]; then
    echo "Cleaning up previous package..."
    rm -rf "$PACKAGE_DIR"
fi

if [ -f "$ZIP_FILE" ]; then
    rm -f "$ZIP_FILE"
fi

# Create packaging directory
mkdir -p "$PACKAGE_DIR"

echo "Installing dependencies using AWS Lambda Python 3.11 Docker image..."

# Copy backend code
cp -r "$BACKEND_DIR/app" "$PACKAGE_DIR/"
cp "$BACKEND_DIR/lambda_function.py" "$PACKAGE_DIR/"
cp "$BACKEND_DIR/__init__.py" "$PACKAGE_DIR/"
cp "$BACKEND_DIR/requirements.txt" "$PACKAGE_DIR/"

# Use Docker to install dependencies in Lambda-compatible environment
docker run --rm \
  --platform linux/amd64 \
  --entrypoint "" \
  -v "$PROJECT_ROOT/$PACKAGE_DIR":/var/task \
  public.ecr.aws/lambda/python:3.11 \
  pip install -r /var/task/requirements.txt -t /var/task --no-cache-dir

# Clean up unnecessary files to reduce package size
echo "Removing unnecessary files..."
cd "$PACKAGE_DIR"
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
rm -f requirements.txt

cd "$PROJECT_ROOT"

# Create zip package
echo "Creating deployment package..."
cd "$PACKAGE_DIR"
zip -r "../$ZIP_FILE" . -q
cd "$PROJECT_ROOT"

# Clean up temporary directory
rm -rf "$PACKAGE_DIR"

# Show package info
PACKAGE_SIZE=$(ls -lh "$ZIP_FILE" | awk '{print $5}')
echo "Lambda package created: $ZIP_FILE ($PACKAGE_SIZE)"
echo "Package location: $PROJECT_ROOT/$ZIP_FILE"

echo ""
echo "Next steps:"
echo "1. cd terraform"
echo "2. terraform plan"
echo "3. terraform apply"