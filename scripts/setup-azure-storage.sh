#!/bin/bash

# Azure Storage Setup Script for Discord Publish Bot
# This script configures your existing Azure Storage Account for Discord media hosting

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Discord Publish Bot - Azure Storage Setup${NC}"
echo "=================================================="

# Check if Azure CLI is installed and logged in
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI not found. Please install Azure CLI first.${NC}"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Please login to Azure CLI first: az login${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Azure CLI is installed and authenticated${NC}"

# Get current subscription
SUBSCRIPTION=$(az account show --query "name" -o tsv)
echo -e "${BLUE}📋 Current subscription: ${SUBSCRIPTION}${NC}"

# Get user input for storage account details
echo ""
read -p "📝 Enter your existing Storage Account name: " STORAGE_ACCOUNT_NAME
read -p "📝 Enter the Resource Group containing your Storage Account: " STORAGE_RESOURCE_GROUP
read -p "📝 Enter your Discord bot's Resource Group name: " BOT_RESOURCE_GROUP  
read -p "📝 Enter your Container App name: " CONTAINER_APP_NAME

# Set default container name
CONTAINER_NAME="discord-media"
read -p "📝 Enter container name for Discord media (default: $CONTAINER_NAME): " USER_CONTAINER
if [ ! -z "$USER_CONTAINER" ]; then
    CONTAINER_NAME="$USER_CONTAINER"
fi

echo ""
echo -e "${YELLOW}🔧 Configuration Summary:${NC}"
echo "Storage Account: $STORAGE_ACCOUNT_NAME"
echo "Storage Resource Group: $STORAGE_RESOURCE_GROUP"
echo "Bot Resource Group: $BOT_RESOURCE_GROUP"
echo "Container App: $CONTAINER_APP_NAME"
echo "Container Name: $CONTAINER_NAME"
echo ""

read -p "Continue with this configuration? (y/N): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Setup cancelled."
    exit 0
fi

echo ""
echo -e "${BLUE}🔧 Setting up Azure Storage for Discord media hosting...${NC}"

# Step 1: Create blob container if it doesn't exist
echo -e "${YELLOW}📁 Creating blob container: $CONTAINER_NAME${NC}"
az storage container create \
    --name "$CONTAINER_NAME" \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --resource-group "$STORAGE_RESOURCE_GROUP" \
    --public-access off \
    --output none

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container created/verified: $CONTAINER_NAME${NC}"
else
    echo -e "${RED}❌ Failed to create container${NC}"
    exit 1
fi

# Step 2: Configure CORS for Discord integration
echo -e "${YELLOW}🌐 Configuring CORS for Discord integration${NC}"
az storage cors add \
    --services b \
    --methods GET POST PUT \
    --origins "https://discord.com" "https://*.discord.com" "https://cdn.discordapp.com" \
    --allowed-headers "*" \
    --exposed-headers "*" \
    --max-age 3600 \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --output none

echo -e "${GREEN}✅ CORS configured for Discord integration${NC}"

# Step 3: Get Container App's managed identity
echo -e "${YELLOW}🔐 Getting Container App managed identity${NC}"
PRINCIPAL_ID=$(az containerapp identity show \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$BOT_RESOURCE_GROUP" \
    --query principalId -o tsv)

if [ -z "$PRINCIPAL_ID" ]; then
    echo -e "${YELLOW}⚠️ No managed identity found. Creating system-assigned managed identity...${NC}"
    az containerapp identity assign \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$BOT_RESOURCE_GROUP" \
        --system-assigned \
        --output none
    
    # Get the new principal ID
    PRINCIPAL_ID=$(az containerapp identity show \
        --name "$CONTAINER_APP_NAME" \
        --resource-group "$BOT_RESOURCE_GROUP" \
        --query principalId -o tsv)
fi

echo -e "${GREEN}✅ Managed Identity Principal ID: $PRINCIPAL_ID${NC}"

# Step 4: Grant Storage permissions to Container App
echo -e "${YELLOW}🔑 Granting Storage Blob Data Contributor access to Container App${NC}"

# Get storage account resource ID
STORAGE_RESOURCE_ID=$(az storage account show \
    --name "$STORAGE_ACCOUNT_NAME" \
    --resource-group "$STORAGE_RESOURCE_GROUP" \
    --query id -o tsv)

# Grant role assignment
az role assignment create \
    --assignee "$PRINCIPAL_ID" \
    --role "Storage Blob Data Contributor" \
    --scope "$STORAGE_RESOURCE_ID" \
    --output none

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Storage permissions granted to Container App${NC}"
else
    echo -e "${RED}❌ Failed to grant storage permissions${NC}"
    exit 1
fi

# Step 5: Configure lifecycle management (optional)
echo -e "${YELLOW}♻️ Setting up lifecycle management for cost optimization${NC}"

# Create lifecycle policy
cat > lifecycle-policy.json << EOF
{
  "rules": [
    {
      "enabled": true,
      "name": "discord-media-lifecycle",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["$CONTAINER_NAME/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": {
              "daysAfterModificationGreaterThan": 30
            },
            "tierToArchive": {
              "daysAfterModificationGreaterThan": 365
            }
          }
        }
      }
    }
  ]
}
EOF

az storage account management-policy create \
    --account-name "$STORAGE_ACCOUNT_NAME" \
    --resource-group "$STORAGE_RESOURCE_GROUP" \
    --policy @lifecycle-policy.json \
    --output none

rm lifecycle-policy.json

echo -e "${GREEN}✅ Lifecycle management configured${NC}"

# Step 6: Display environment variables needed
echo ""
echo -e "${BLUE}📋 Environment Variables for your .env.production file:${NC}"
echo "=================================================="
echo "ENABLE_AZURE_STORAGE=true"
echo "AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_ACCOUNT_NAME"
echo "AZURE_STORAGE_CONTAINER_NAME=$CONTAINER_NAME"
echo "AZURE_STORAGE_SAS_EXPIRY_HOURS=8760"
echo ""
echo "# Media type folder configuration (optional - defaults shown):"
echo "AZURE_STORAGE_IMAGES_FOLDER=images"
echo "AZURE_STORAGE_VIDEOS_FOLDER=videos"
echo "AZURE_STORAGE_AUDIO_FOLDER=audio"
echo "AZURE_STORAGE_DOCUMENTS_FOLDER=documents"
echo "AZURE_STORAGE_OTHER_FOLDER=other"
echo ""

# Step 7: Update Container App secrets (if azure-secrets-setup.ps1 exists)
if [ -f "./scripts/azure-secrets-setup.ps1" ]; then
    echo -e "${YELLOW}🔐 Would you like to update your Container App secrets now?${NC}"
    read -p "Run azure-secrets-setup.ps1 script? (y/N): " UPDATE_SECRETS
    
    if [ "$UPDATE_SECRETS" = "y" ] || [ "$UPDATE_SECRETS" = "Y" ]; then
        echo -e "${BLUE}Running azure-secrets-setup.ps1...${NC}"
        pwsh ./scripts/azure-secrets-setup.ps1 \
            -ResourceGroupName "$BOT_RESOURCE_GROUP" \
            -ContainerAppName "$CONTAINER_APP_NAME" \
            -EnvFile ".env.production"
    fi
fi

echo ""
echo -e "${GREEN}🎉 Azure Storage setup complete!${NC}"
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo "1. Add the environment variables to your .env.production file"
echo "2. Run your secrets setup script to update Container App configuration"
echo "3. Test the Discord bot with media uploads"
echo "4. Monitor storage costs and usage in Azure portal"
echo ""
echo -e "${BLUE}💡 Storage Account Details:${NC}"
echo "• Account: $STORAGE_ACCOUNT_NAME"
echo "• Container: $CONTAINER_NAME"
echo "• Location: https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$STORAGE_RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT_NAME"
echo ""
echo -e "${GREEN}✅ Your Discord bot can now store media permanently in Azure Blob Storage!${NC}"
