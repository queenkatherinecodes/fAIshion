#!/bin/bash
# infrastructure/deploy.sh
# Main deployment script for fAIshion infrastructure (Student Edition)

# Load environment variables
source "$(dirname "$0")/variables.sh"

# Override password with a strong one that meets Azure SQL complexity requirements
# Ensure it's at least 12 characters long with a mix of uppercase, lowercase, numbers, and special characters
SQL_ADMIN_PASSWORD="Fai\$hion2025Complex!Pwd"

echo "=== Starting deployment of fAIshion infrastructure (Student Edition) ==="
echo "Environment: $FASHION_ENV"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"

# Login to Azure (comment if not already logged in)
az login

# Install required extensions
echo "Installing required extensions..."
az extension add --name application-insights --yes

# Register required resource providers
echo "Registering required resource providers..."
az provider register --namespace Microsoft.Sql
az provider register --namespace Microsoft.Web
az provider register --namespace Microsoft.CognitiveServices

# Wait for provider registration to complete for SQL
echo "Waiting for provider registrations to complete..."
until [ "$(az provider show -n Microsoft.Sql --query "registrationState" -o tsv)" = "Registered" ]
do
  echo "Waiting for Microsoft.Sql registration to complete..."
  sleep 10
done
echo "Microsoft.Sql registration complete."

# Create Resource Group with tags
echo "Creating Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION \
  --tags "app=fAIshion" "environment=$FASHION_ENV" "project=student"

# First check if SQL server already exists
echo "Checking if SQL Server exists..."
SQL_SERVER_EXISTS=$(az sql server list --resource-group $RESOURCE_GROUP --query "[?name=='$SQL_SERVER_NAME']" -o tsv)

if [ -z "$SQL_SERVER_EXISTS" ]; then
  # Create SQL Server and Database
  echo "Creating SQL Server and Database..."
  az sql server create \
    --name $SQL_SERVER_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user $SQL_ADMIN_USER \
    --admin-password "$SQL_ADMIN_PASSWORD"

  echo "Configuring SQL Server firewall..."
  az sql server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --server $SQL_SERVER_NAME \
    --name "AllowAzureServices" \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0 || true

  # Add your client IP to firewall rules for local development
  CLIENT_IP=$(curl -s https://api.ipify.org)
  echo "Adding your IP address ($CLIENT_IP) to firewall rules..."
  az sql server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --server $SQL_SERVER_NAME \
    --name "ClientIPAddress" \
    --start-ip-address $CLIENT_IP \
    --end-ip-address $CLIENT_IP || true

  echo "Creating SQL Database (Basic tier)..."
  az sql db create \
    --resource-group $RESOURCE_GROUP \
    --server $SQL_SERVER_NAME \
    --name $SQL_DB_NAME \
    --service-objective Basic || true

else
  echo "SQL Server already exists, skipping creation."
fi

# Create Storage Account for wardrobe images
echo "Creating Storage Account..."
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot \
  --tags "app=fAIshion" "environment=$FASHION_ENV" "project=student"

# Get Storage Account Key
STORAGE_KEY=$(az storage account keys list --resource-group $RESOURCE_GROUP --account-name $STORAGE_ACCOUNT_NAME --query "[0].value" -o tsv)

# Create containers
echo "Creating Blob Containers..."
az storage container create \
  --name $WARDROBE_CONTAINER \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --public-access blob

az storage container create \
  --name $OUTFITS_CONTAINER \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_KEY \
  --public-access blob

# Create Computer Vision service for image analysis (Free tier)
echo "Creating Computer Vision service (Free tier)..."
az cognitiveservices account create \
  --name $COMPUTER_VISION_NAME \
  --resource-group $RESOURCE_GROUP \
  --kind ComputerVision \
  --sku F0 \
  --location $LOCATION \
  --tags "app=fAIshion" "environment=$FASHION_ENV" "project=student"

# Check if Text Analytics account already exists
echo "Checking if Text Analytics service already exists..."
TEXT_SERVICE_EXISTS=$(az cognitiveservices account list --resource-group $RESOURCE_GROUP --query "[?name=='$TEXT_ANALYTICS_NAME']" -o tsv)

if [ -z "$TEXT_SERVICE_EXISTS" ]; then
  echo "Creating Text Analytics service (Free tier)..."
  # Skip the --public-network-access parameter entirely
  # Try eastus first, then try to delete and recreate if it fails
  az cognitiveservices account create \
    --name $TEXT_ANALYTICS_NAME \
    --resource-group $RESOURCE_GROUP \
    --kind TextAnalytics \
    --sku F0 \
    --location $LOCATION \
    --yes \
    --tags "app=fAIshion" "environment=$FASHION_ENV" "project=student" || \
  {
    echo "Text Analytics creation failed, trying different approach..."
    # Try to delete if it exists but in a different state
    az cognitiveservices account delete --name $TEXT_ANALYTICS_NAME --resource-group $RESOURCE_GROUP --yes 2>/dev/null || true
    
    # Try again with a different location
    az cognitiveservices account create \
      --name $TEXT_ANALYTICS_NAME \
      --resource-group $RESOURCE_GROUP \
      --kind TextAnalytics \
      --sku F0 \
      --location "westus" \
      --yes \
      --tags "app=fAIshion" "environment=$FASHION_ENV" "project=student" || \
    echo "Warning: Could not create Text Analytics service. Continuing with deployment..."
  }
else
  echo "Text Analytics service already exists, skipping creation."
fi

# Create App Insights for monitoring
echo "Creating Application Insights..."
az monitor app-insights component create \
  --app $APP_INSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --application-type web \
  --tags "app=fAIshion" "environment=$FASHION_ENV" "project=student"

# Try different regions for App Service Plan if quota issues
echo "Creating App Service Plan (Free tier)..."
# List of regions to try in order
REGIONS=("eastus" "westus" "westus2" "centralus" "southcentralus")

for REGION in "${REGIONS[@]}"; do
  echo "Trying to create App Service Plan in $REGION..."
  APP_PLAN_RESULT=$(az appservice plan create \
    --name $APP_SERVICE_PLAN \
    --resource-group $RESOURCE_GROUP \
    --sku F1 \
    --is-linux \
    --location $REGION \
    --tags "app=fAIshion" "environment=$FASHION_ENV" "project=student" 2>&1)
  
  if [[ $APP_PLAN_RESULT == *"quota of 0 instances"* ]]; then
    echo "Quota issue in $REGION, trying next region..."
    continue
  else
    echo "Successfully created App Service Plan in $REGION"
    # Update the location variable for web app creation
    APP_LOCATION=$REGION
    break
  fi
done

# If we couldn't create an App Service Plan in any region, exit
if [ -z "$APP_LOCATION" ]; then
  echo "ERROR: Could not create App Service Plan in any region due to quota limitations."
  echo "Please check your Azure for Students subscription limits or try a different subscription."
  exit 1
fi

# Create Web App
echo "Creating Web App..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --runtime "DOTNETCORE|6.0" \
  --tags "app=fAIshion" "environment=$FASHION_ENV" "project=student"

# Configure App Settings - Split into individual commands to avoid errors
echo "Configuring App Settings..."

# Get connection strings and keys
SQL_SERVER_FQDN=$(az sql server show --resource-group $RESOURCE_GROUP --name $SQL_SERVER_NAME --query fullyQualifiedDomainName -o tsv 2>/dev/null || echo "")
if [ ! -z "$SQL_SERVER_FQDN" ]; then
  SQL_CONNECTION="Server=tcp:$SQL_SERVER_FQDN,1433;Database=$SQL_DB_NAME;User ID=$SQL_ADMIN_USER;Password=$SQL_ADMIN_PASSWORD;Encrypt=true;Connection Timeout=30;"
  echo "SQL connection string generated."
else
  echo "Warning: Could not get SQL server information. Connection string will not be set."
fi

# Try to get Computer Vision info
VISION_KEY=$(az cognitiveservices account keys list --name $COMPUTER_VISION_NAME --resource-group $RESOURCE_GROUP --query key1 -o tsv 2>/dev/null || echo "")
VISION_ENDPOINT=$(az cognitiveservices account show --name $COMPUTER_VISION_NAME --resource-group $RESOURCE_GROUP --query properties.endpoint -o tsv 2>/dev/null || echo "")
if [ ! -z "$VISION_KEY" ]; then
  echo "Computer Vision keys retrieved."
else
  echo "Warning: Could not get Computer Vision keys."
fi

# Try to get Text Analytics info
TEXT_KEY=$(az cognitiveservices account keys list --name $TEXT_ANALYTICS_NAME --resource-group $RESOURCE_GROUP --query key1 -o tsv 2>/dev/null || echo "")
TEXT_ENDPOINT=$(az cognitiveservices account show --name $TEXT_ANALYTICS_NAME --resource-group $RESOURCE_GROUP --query properties.endpoint -o tsv 2>/dev/null || echo "")
if [ ! -z "$TEXT_KEY" ]; then
  echo "Text Analytics keys retrieved."
else
  echo "Warning: Could not get Text Analytics keys."
fi

# Try to get Storage and App Insights info
STORAGE_CONNECTION=$(az storage account show-connection-string --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP --query connectionString -o tsv 2>/dev/null || echo "")
APP_INSIGHTS_KEY=$(az monitor app-insights component show --app $APP_INSIGHTS_NAME --resource-group $RESOURCE_GROUP --query instrumentationKey -o tsv 2>/dev/null || echo "")

# Set app settings individually to avoid errors
echo "Setting individual app settings..."

if [ ! -z "$APP_INSIGHTS_KEY" ]; then
  az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings "APPINSIGHTS_INSTRUMENTATIONKEY=$APP_INSIGHTS_KEY" || true
fi

if [ ! -z "$VISION_ENDPOINT" ] && [ ! -z "$VISION_KEY" ]; then
  az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings "ComputerVision:Endpoint=$VISION_ENDPOINT" || true
  az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings "ComputerVision:Key=$VISION_KEY" || true
fi

if [ ! -z "$TEXT_ENDPOINT" ] && [ ! -z "$TEXT_KEY" ]; then
  az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings "TextAnalytics:Endpoint=$TEXT_ENDPOINT" || true
  az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings "TextAnalytics:Key=$TEXT_KEY" || true
fi

if [ ! -z "$STORAGE_CONNECTION" ]; then
  az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings "StorageAccount:ConnectionString=$STORAGE_CONNECTION" || true
  az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings "StorageAccount:WardrobeContainer=$WARDROBE_CONTAINER" || true
  az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings "StorageAccount:OutfitsContainer=$OUTFITS_CONTAINER" || true
fi

az webapp config appsettings set --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --settings "WEBSITE_RUN_FROM_PACKAGE=1" || true

# Set connection string if we have one
if [ ! -z "$SQL_CONNECTION" ]; then
  echo "Setting SQL connection string..."
  az webapp config connection-string set \
    --resource-group $RESOURCE_GROUP \
    --name $WEB_APP_NAME \
    --connection-string-type SQLAzure \
    --settings DefaultConnection="$SQL_CONNECTION" || echo "Warning: Failed to set connection string."
fi

# Enable managed identity
echo "Enabling Managed Identity..."
az webapp identity assign \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME || echo "Warning: Failed to assign managed identity."

# Output the website URL
WEB_APP_URL=$(az webapp show --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --query defaultHostName -o tsv 2>/dev/null || echo "unknown")
echo ""
echo "=== Deployment complete! ==="
echo "fAIshion API is now available at: https://$WEB_APP_URL"
echo ""
echo "Resource Summary:"
echo "- SQL Database (Basic tier): ${SQL_SERVER_NAME}/${SQL_DB_NAME}"
echo "- Web App (Free tier): ${WEB_APP_NAME}"
echo "- Storage Account: ${STORAGE_ACCOUNT_NAME}"
echo "- Computer Vision (Free tier): ${COMPUTER_VISION_NAME}" 
echo "- Text Analytics (Free tier): ${TEXT_ANALYTICS_NAME}"
echo ""
echo "Next steps:"
echo "1. Deploy your application code"
echo "2. Set up CI/CD pipeline"
echo "3. For best results with Azure for Students, remember to stop/delete resources when not in use"