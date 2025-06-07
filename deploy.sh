#!/bin/bash

# Deploy the Cloud Function
echo "Deploying Cloud Function..."
gcloud functions deploy process-with-langgraph \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=process_with_langgraph \
  --trigger-http \
  --timeout=540s \
  --memory=2048MB \
  --env-vars-file .env.yaml

# Check if deployment was successful
if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo "Function URL will be displayed above."
else
    echo "❌ Deployment failed!"
    exit 1
fi 