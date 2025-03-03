#!/bin/bash
# infrastructure/deploy.sh
# Main deployment script for fAIshion infrastructure (Student Edition)

# Load environment variables
source "$(dirname "$0")/variables.sh"

echo "=== Starting deployment of fAIshion infrastructure (Student Edition) ==="
echo "Environment: $FASHION_ENV"
echo "Resource Group: $RESOURCE_GROUP"
echo "Location: $LOCATION"

# Login to Azure (uncomment if not already logged in)
# az login

# Create Resource Group
echo "Creating Resource Group..."
az group create --name $RESOURCE_GROUP --location $LOCATION --tags app=fAIshion environment=$FASHION_ENV project=student

# Create SQL Server and Database
echo "Creating SQL Server and Database..."
az sql server create \
  --name $SQL_SERVER_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user $SQL_ADMIN_USER \
  --admin-password $SQL_ADMIN_PASSWORD \
  --tags app=fAIshion environment=$FASHION_ENV project=student

echo "Configuring SQL Server firewall..."
az sql server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER_NAME \
  --name "AllowAzureServices" \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Add your client IP to firewall rules for local development
CLIENT_IP=$(curl -s https://api.ipify.org)
echo "Adding your IP address ($CLIENT_IP) to firewall rules..."
az sql server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER_NAME \
  --name "ClientIPAddress" \
  --start-ip-address $CLIENT_IP \
  --end-ip-address $CLIENT_IP

echo "Creating SQL Database (Basic tier)..."
az sql db create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER_NAME \
  --name $SQL_DB_NAME \
  --service-objective Basic \
  --tags app=fAIshion environment=$FASHION_ENV project=student

# Create Storage Account for wardrobe images
echo "Creating Storage Account..."
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot \
  --tags app=fAIshion environment=$FASHION_ENV project=student

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
  --tags app=fAIshion environment=$FASHION_ENV project=student

# Create Text Analytics service for text processing (Free tier)
echo "Creating Text Analytics service (Free tier)..."
az cognitiveservices account create \
  --name $TEXT_ANALYTICS_NAME \
  --resource-group $RESOURCE_GROUP \
  --kind TextAnalytics \
  --sku F0 \
  --location $LOCATION \
  --tags app=fAIshion environment=$FASHION_ENV project=student

# Create App Insights for monitoring
echo "Creating Application Insights..."
az monitor app-insights component create \
  --app $APP_INSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --application-type web \
  --tags app=fAIshion environment=$FASHION_ENV project=student

# Create App Service Plan (Free tier)
echo "Creating App Service Plan (Free tier)..."
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --sku F1 \
  --is-linux \
  --tags app=fAIshion environment=$FASHION_ENV project=student

# Create Web App
echo "Creating Web App..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --runtime "DOTNETCORE|6.0" \
  --tags app=fAIshion environment=$FASHION_ENV project=student

# Configure App Settings
echo "Configuring App Settings..."

# Get connection strings and keys
SQL_SERVER_FQDN=$(az sql server show --resource-group $RESOURCE_GROUP --name $SQL_SERVER_NAME --query fullyQualifiedDomainName -o tsv)
CONNECTION_STRING="Server=tcp:$SQL_SERVER_FQDN,1433;Database=$SQL_DB_NAME;User ID=$SQL_ADMIN_USER;Password=$SQL_ADMIN_PASSWORD;Encrypt=true;Connection Timeout=30;"

VISION_KEY=$(az cognitiveservices account keys list --name $COMPUTER_VISION_NAME --resource-group $RESOURCE_GROUP --query "key1" -o tsv)
VISION_ENDPOINT=$(az cognitiveservices account show --name $COMPUTER_VISION_NAME --resource-group $RESOURCE_GROUP --query "properties.endpoint" -o tsv)

TEXT_KEY=$(az cognitiveservices account keys list --name $TEXT_ANALYTICS_NAME --resource-group $RESOURCE_GROUP --query "key1" -o tsv)
TEXT_ENDPOINT=$(az cognitiveservices account show --name $TEXT_ANALYTICS_NAME --resource-group $RESOURCE_GROUP --query "properties.endpoint" -o tsv)

STORAGE_CONNECTION=$(az storage account show-connection-string --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP --query connectionString -o tsv)
APP_INSIGHTS_KEY=$(az monitor app-insights component show --app $APP_INSIGHTS_NAME --resource-group $RESOURCE_GROUP --query instrumentationKey -o tsv)

# Set app settings
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings \
  "APPINSIGHTS_INSTRUMENTATIONKEY=$APP_INSIGHTS_KEY" \
  "ComputerVision:Endpoint=$VISION_ENDPOINT" \
  "ComputerVision:Key=$VISION_KEY" \
  "TextAnalytics:Endpoint=$TEXT_ENDPOINT" \
  "TextAnalytics:Key=$TEXT_KEY" \
  "StorageAccount:ConnectionString=$STORAGE_CONNECTION" \
  "StorageAccount:WardrobeContainer=$WARDROBE_CONTAINER" \
  "StorageAccount:OutfitsContainer=$OUTFITS_CONTAINER" \
  "WEBSITE_RUN_FROM_PACKAGE=1"

# Set connection strings
az webapp config connection-string set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --connection-string-type SQLAzure \
  --settings DefaultConnection="$CONNECTION_STRING"

# Enable managed identity
echo "Enabling Managed Identity..."
az webapp identity assign \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME

# Output the website URL
WEB_APP_URL=$(az webapp show --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME --query defaultHostName -o tsv)
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