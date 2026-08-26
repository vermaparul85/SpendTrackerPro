#!/usr/bin/env bash
set -e

# ==========================================================
# SpendTracker Pro - Google Cloud Run Deployment Script
# ==========================================================

SERVICE_NAME="spendtracker-pro"
REGION="us-central1"

echo "=========================================="
echo "🚀 Deploying SpendTracker Pro to Cloud Run"
echo "=========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: 'gcloud' CLI is not found."
    echo "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
    echo "⚠️ No default project set in gcloud."
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi

echo "📌 Project ID: $PROJECT_ID"
echo "📌 Service:    $SERVICE_NAME"
echo "📌 Region:     $REGION"
echo ""

# Enable required APIs
echo "🔧 Ensuring required GCP APIs are enabled..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com --quiet

# Deploy source directly via Cloud Build to Cloud Run
echo "📦 Building & Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "GCP_PROJECT=$PROJECT_ID,DATASET_ID=spend_tracker"

echo ""
echo "✅ Deployment complete! Check the service URL above."
