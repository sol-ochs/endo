#!/bin/bash

set -e  # Exit on error

echo "Deploying Endo UI to AWS..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Get API URL from Terraform first (needed for build)
echo "Getting AWS resource info from Terraform..."
cd terraform
S3_BUCKET=$(terraform output -raw s3_bucket_name)

# CloudFront distribution may not exist on first deploy
if CLOUDFRONT_DIST_ID=$(terraform output -raw cloudfront_distribution_id 2>&1); then
  echo "✓ Found CloudFront distribution ID"
else
  echo "⚠ Warning: Could not retrieve CloudFront distribution ID. Skipping cache invalidation."
  echo "  This is expected on first deploy, but may indicate a Terraform issue on subsequent deploys."
  CLOUDFRONT_DIST_ID=""
fi

API_URL=$(terraform output -raw api_url)
cd ..

if [ -z "$API_URL" ]; then
  echo "Error: Could not get API URL from Terraform"
  exit 1
fi

# Build the React app with API URL injected
echo "Building React app with API_URL=$API_URL..."
cd ui
REACT_APP_API_URL="$API_URL" npm run build
cd ..

if [ -z "$S3_BUCKET" ]; then
  echo "Error: Could not get S3 bucket name from Terraform"
  exit 1
fi

echo "Uploading files to S3 bucket: $S3_BUCKET..."

# Sync build files to S3
aws s3 sync ui/build/ "s3://$S3_BUCKET/" \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html" \
  --exclude "asset-manifest.json" \
  --exclude "service-worker.js"

# Upload index.html with no-cache to ensure updates are seen immediately
aws s3 cp ui/build/index.html "s3://$S3_BUCKET/index.html" \
  --cache-control "no-cache, no-store, must-revalidate" \
  --metadata-directive REPLACE

# Upload other root files if they exist
if [ -f ui/build/asset-manifest.json ]; then
  aws s3 cp ui/build/asset-manifest.json "s3://$S3_BUCKET/asset-manifest.json" \
    --cache-control "no-cache" \
    --metadata-directive REPLACE
fi

if [ -f ui/build/service-worker.js ]; then
  aws s3 cp ui/build/service-worker.js "s3://$S3_BUCKET/service-worker.js" \
    --cache-control "no-cache" \
    --metadata-directive REPLACE
fi

# Invalidate CloudFront cache if distribution exists
if [ -n "$CLOUDFRONT_DIST_ID" ]; then
  echo "Invalidating CloudFront cache..."
  aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DIST_ID" \
    --paths "/*" > /dev/null
  echo "CloudFront cache invalidated"
fi

echo ""
echo "Deployment complete"
echo ""
echo "Build info:"
echo "   - API URL: $API_URL"
echo "   - S3 Bucket: $S3_BUCKET"
if [ -n "$CLOUDFRONT_DIST_ID" ]; then
  echo "   - CloudFront ID: $CLOUDFRONT_DIST_ID"
fi
echo ""
echo "Your app will be available at:"
cd terraform
terraform output cloudfront_url
cd ..
