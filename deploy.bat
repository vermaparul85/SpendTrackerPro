@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo SpendTracker Pro - Google Cloud Run Deploy
echo ==========================================

set SERVICE_NAME=spendtracker-pro
set REGION=us-central1

:: Check if gcloud is installed
where gcloud >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 'gcloud' CLI is not found in PATH.
    echo Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

:: Get GCP project
for /f "delims=" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT_ID=%%i

if "%PROJECT_ID%"=="" (
    set /p PROJECT_ID="Enter your Google Cloud Project ID: "
    gcloud config set project !PROJECT_ID!
)

echo Project ID: %PROJECT_ID%
echo Service:    %SERVICE_NAME%
echo Region:     %REGION%
echo.

echo [1/2] Enabling required GCP APIs...
call gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com --quiet

echo [2/2] Building and deploying to Cloud Run...
call gcloud run deploy %SERVICE_NAME% ^
    --source . ^
    --region %REGION% ^
    --platform managed ^
    --allow-unauthenticated ^
    --set-env-vars GCP_PROJECT=%PROJECT_ID%,DATASET_ID=spend_tracker

echo.
echo ==========================================
echo Deployment complete!
echo ==========================================
pause
