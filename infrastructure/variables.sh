#!/bin/bash
# infrastructure/variables.sh
# Resource naming convention for fAIshion - AI-powered wardrobe recommendation app
# Configured for Azure for Students with minimal cost

# Main resource identifiers
export FASHION_APP_NAME="faishion"
export FASHION_ENV="dev"  # Change to 'staging' or 'prod' for other environments

# Resource group
export RESOURCE_GROUP="${FASHION_APP_NAME}-${FASHION_ENV}-rg"
export LOCATION="eastus"  # Primary Azure region

# SQL Database (Basic tier - ~$5/month)
export SQL_SERVER_NAME="${FASHION_APP_NAME}-${FASHION_ENV}-sql"
export SQL_DB_NAME="${FASHION_APP_NAME}Db"
export SQL_ADMIN_USER="faishionadmin"
export SQL_ADMIN_PASSWORD="admin12345"

# App Service (Free F1 tier)
export APP_SERVICE_PLAN="${FASHION_APP_NAME}-${FASHION_ENV}-plan"
export WEB_APP_NAME="${FASHION_APP_NAME}-${FASHION_ENV}-app"

# Storage Account for wardrobe images (minimal cost for student projects)
export STORAGE_ACCOUNT_NAME="${FASHION_APP_NAME}${FASHION_ENV}storage"
export WARDROBE_CONTAINER="wardrobe"
export OUTFITS_CONTAINER="outfits"

# AI Services (Free F0 tier)
export COMPUTER_VISION_NAME="${FASHION_APP_NAME}-${FASHION_ENV}-vision"
export TEXT_ANALYTICS_NAME="${FASHION_APP_NAME}-${FASHION_ENV}-text"

# Logging and monitoring (free tier)
export APP_INSIGHTS_NAME="${FASHION_APP_NAME}-${FASHION_ENV}-insights"

# Tags for resource management
export RESOURCE_TAGS="app=fAIshion environment=${FASHION_ENV} project=student"