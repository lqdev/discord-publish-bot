# Azure Storage Setup Script for Discord Publish Bot
# This script configures your existing Azure Storage Account for Discord media hosting

param(
    [string]$StorageAccountName,
    [string]$StorageResourceGroup,
    [string]$BotResourceGroup,
    [string]$ContainerAppName,
    [string]$ContainerName = "discord-media"
)

Write-Host "🚀 Discord Publish Bot - Azure Storage Setup" -ForegroundColor Blue
Write-Host "==================================================" -ForegroundColor Blue

# Check if Azure CLI is installed and logged in
try {
    $null = az account show 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Please login to Azure CLI first: az login" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Azure CLI not found. Please install Azure CLI first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Azure CLI is installed and authenticated" -ForegroundColor Green

# Get current subscription
$subscription = (az account show --query "name" -o tsv)
Write-Host "📋 Current subscription: $subscription" -ForegroundColor Blue

# Get user input if parameters not provided
if (-not $StorageAccountName) {
    $StorageAccountName = Read-Host "📝 Enter your existing Storage Account name"
}

if (-not $StorageResourceGroup) {
    $StorageResourceGroup = Read-Host "📝 Enter the Resource Group containing your Storage Account"
}

if (-not $BotResourceGroup) {
    $BotResourceGroup = Read-Host "📝 Enter your Discord bot's Resource Group name"
}

if (-not $ContainerAppName) {
    $ContainerAppName = Read-Host "📝 Enter your Container App name"
}

$userContainer = Read-Host "📝 Enter container name for Discord media (default: $ContainerName)"
if ($userContainer) {
    $ContainerName = $userContainer
}

Write-Host ""
Write-Host "🔧 Configuration Summary:" -ForegroundColor Yellow
Write-Host "Storage Account: $StorageAccountName"
Write-Host "Storage Resource Group: $StorageResourceGroup"
Write-Host "Bot Resource Group: $BotResourceGroup"
Write-Host "Container App: $ContainerAppName"
Write-Host "Container Name: $ContainerName"
Write-Host ""

$confirm = Read-Host "Continue with this configuration? (y/N)"
if ($confirm -ne "y" -and $confirm -ne "Y") {
    Write-Host "Setup cancelled."
    exit 0
}

Write-Host ""
Write-Host "🔧 Setting up Azure Storage for Discord media hosting..." -ForegroundColor Blue

# Step 1: Create blob container if it doesn't exist
Write-Host "📁 Creating blob container: $ContainerName" -ForegroundColor Yellow
az storage container create `
    --name $ContainerName `
    --account-name $StorageAccountName `
    --resource-group $StorageResourceGroup `
    --public-access off `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Container created/verified: $ContainerName" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to create container" -ForegroundColor Red
    exit 1
}

# Step 2: Configure CORS for Discord integration
Write-Host "🌐 Configuring CORS for Discord integration" -ForegroundColor Yellow
az storage cors add `
    --services b `
    --methods GET POST PUT `
    --origins "https://discord.com" "https://*.discord.com" "https://cdn.discordapp.com" `
    --allowed-headers "*" `
    --exposed-headers "*" `
    --max-age 3600 `
    --account-name $StorageAccountName `
    --output none

Write-Host "✅ CORS configured for Discord integration" -ForegroundColor Green

# Step 3: Get Container App's managed identity
Write-Host "🔐 Getting Container App managed identity" -ForegroundColor Yellow
$principalId = (az containerapp identity show `
    --name $ContainerAppName `
    --resource-group $BotResourceGroup `
    --query principalId -o tsv)

if (-not $principalId) {
    Write-Host "⚠️ No managed identity found. Creating system-assigned managed identity..." -ForegroundColor Yellow
    az containerapp identity assign `
        --name $ContainerAppName `
        --resource-group $BotResourceGroup `
        --system-assigned `
        --output none
    
    # Get the new principal ID
    $principalId = (az containerapp identity show `
        --name $ContainerAppName `
        --resource-group $BotResourceGroup `
        --query principalId -o tsv)
}

Write-Host "✅ Managed Identity Principal ID: $principalId" -ForegroundColor Green

# Step 4: Grant Storage permissions to Container App
Write-Host "🔑 Granting Storage Blob Data Contributor access to Container App" -ForegroundColor Yellow

# Get storage account resource ID
$storageResourceId = (az storage account show `
    --name $StorageAccountName `
    --resource-group $StorageResourceGroup `
    --query id -o tsv)

# Grant role assignment
az role assignment create `
    --assignee $principalId `
    --role "Storage Blob Data Contributor" `
    --scope $storageResourceId `
    --output none

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Storage permissions granted to Container App" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to grant storage permissions" -ForegroundColor Red
    exit 1
}

# Step 5: Configure lifecycle management (optional)
Write-Host "♻️ Setting up lifecycle management for cost optimization" -ForegroundColor Yellow

# Create lifecycle policy
$lifecyclePolicy = @"
{
  "rules": [
    {
      "enabled": true,
      "name": "discord-media-lifecycle",
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["$ContainerName/"]
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
"@

$lifecyclePolicy | Out-File -FilePath "lifecycle-policy.json" -Encoding utf8

az storage account management-policy create `
    --account-name $StorageAccountName `
    --resource-group $StorageResourceGroup `
    --policy "@lifecycle-policy.json" `
    --output none

Remove-Item "lifecycle-policy.json"

Write-Host "✅ Lifecycle management configured" -ForegroundColor Green

# Step 6: Display environment variables needed
Write-Host ""
Write-Host "📋 Environment Variables for your .env.production file:" -ForegroundColor Blue
Write-Host "=================================================="
Write-Host "ENABLE_AZURE_STORAGE=true"
Write-Host "AZURE_STORAGE_ACCOUNT_NAME=$StorageAccountName"
Write-Host "AZURE_STORAGE_CONTAINER_NAME=$ContainerName"
Write-Host "AZURE_STORAGE_SAS_EXPIRY_HOURS=8760"
Write-Host ""
Write-Host "# Media type folder configuration (optional - defaults shown):"
Write-Host "AZURE_STORAGE_IMAGES_FOLDER=images"
Write-Host "AZURE_STORAGE_VIDEOS_FOLDER=videos"
Write-Host "AZURE_STORAGE_AUDIO_FOLDER=audio"
Write-Host "AZURE_STORAGE_DOCUMENTS_FOLDER=documents"
Write-Host "AZURE_STORAGE_OTHER_FOLDER=other"
Write-Host ""

# Step 7: Update Container App secrets (if azure-secrets-setup.ps1 exists)
if (Test-Path "./scripts/azure-secrets-setup.ps1") {
    Write-Host "🔐 Would you like to update your Container App secrets now?" -ForegroundColor Yellow
    $updateSecrets = Read-Host "Run azure-secrets-setup.ps1 script? (y/N)"
    
    if ($updateSecrets -eq "y" -or $updateSecrets -eq "Y") {
        Write-Host "Running azure-secrets-setup.ps1..." -ForegroundColor Blue
        
        # Create temporary .env.production with storage settings
        $envContent = @"
ENABLE_AZURE_STORAGE=true
AZURE_STORAGE_ACCOUNT_NAME=$StorageAccountName
AZURE_STORAGE_CONTAINER_NAME=$ContainerName
AZURE_STORAGE_SAS_EXPIRY_HOURS=8760

# Media type folder configuration (customize as needed)
AZURE_STORAGE_IMAGES_FOLDER=images
AZURE_STORAGE_VIDEOS_FOLDER=videos
AZURE_STORAGE_AUDIO_FOLDER=audio
AZURE_STORAGE_DOCUMENTS_FOLDER=documents
AZURE_STORAGE_OTHER_FOLDER=other
"@
        
        # Append to existing .env.production or create new
        if (Test-Path ".env.production") {
            Add-Content -Path ".env.production" -Value "`n# Azure Storage Configuration"
            Add-Content -Path ".env.production" -Value $envContent
        } else {
            Set-Content -Path ".env.production" -Value $envContent
        }
        
        & "./scripts/azure-secrets-setup.ps1" -ResourceGroupName $BotResourceGroup -ContainerAppName $ContainerAppName -EnvFile ".env.production"
    }
}

Write-Host ""
Write-Host "🎉 Azure Storage setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Blue
Write-Host "1. Add the environment variables to your .env.production file"
Write-Host "2. Run your secrets setup script to update Container App configuration"
Write-Host "3. Test the Discord bot with media uploads"
Write-Host "4. Monitor storage costs and usage in Azure portal"
Write-Host ""
Write-Host "💡 Storage Account Details:" -ForegroundColor Blue
$subscriptionId = (az account show --query id -o tsv)
Write-Host "• Account: $StorageAccountName"
Write-Host "• Container: $ContainerName"
Write-Host "• Location: https://portal.azure.com/#@/resource/subscriptions/$subscriptionId/resourceGroups/$StorageResourceGroup/providers/Microsoft.Storage/storageAccounts/$StorageAccountName"
Write-Host ""
Write-Host "✅ Your Discord bot can now store media permanently in Azure Blob Storage!" -ForegroundColor Green
