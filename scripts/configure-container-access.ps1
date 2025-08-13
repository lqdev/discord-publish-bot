#!/usr/bin/env pwsh
# Azure Storage Container Access Configuration Script
# This script helps you choose between public and private container access

param(
    [Parameter(Mandatory=$true)]
    [string]$StorageAccountName,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$false)]
    [string]$ContainerName = "discord-media",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("private", "public")]
    [string]$AccessLevel = "private"
)

Write-Host "🔐 Azure Storage Container Access Configuration" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Check if Azure CLI is installed and logged in
try {
    $account = az account show --query "name" -o tsv 2>$null
    if (-not $account) {
        Write-Error "Please run 'az login' first"
        exit 1
    }
    Write-Host "✅ Logged in to Azure as: $account" -ForegroundColor Green
} catch {
    Write-Error "Azure CLI not found. Please install Azure CLI first."
    exit 1
}

Write-Host ""
Write-Host "🎯 Configuration:" -ForegroundColor Blue
Write-Host "Storage Account: $StorageAccountName"
Write-Host "Resource Group: $ResourceGroupName"
Write-Host "Container: $ContainerName"
Write-Host "Access Level: $AccessLevel"
Write-Host ""

if ($AccessLevel -eq "public") {
    Write-Host "⚠️ WARNING: Public Access Mode" -ForegroundColor Yellow
    Write-Host "================================================" -ForegroundColor Yellow
    Write-Host "🔓 This will make ALL files in the container publicly accessible"
    Write-Host "🌐 Anyone with the URL can access files (no authentication required)"
    Write-Host "💡 Benefits: Simpler URLs, no SAS token expiration"
    Write-Host "⚠️ Risks: No access control, potential for abuse"
    Write-Host ""
    Write-Host "🔗 URL Format: https://$StorageAccountName.blob.core.windows.net/$ContainerName/images/photo.jpg" -ForegroundColor Gray
    Write-Host ""
    
    $confirm = Read-Host "Are you sure you want to enable public access? (type 'YES' to confirm)"
    if ($confirm -ne "YES") {
        Write-Host "❌ Public access setup cancelled."
        exit 0
    }
    
    Write-Host ""
    Write-Host "🔓 Setting container to public blob access..." -ForegroundColor Yellow
    
    # Set container to public blob access
    az storage container set-permission `
        --name $ContainerName `
        --public-access blob `
        --account-name $StorageAccountName `
        --resource-group $ResourceGroupName `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container set to public access" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to set public access" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "📋 Environment Configuration:" -ForegroundColor Blue
    Write-Host "Add this to your .env.production file:"
    Write-Host "AZURE_STORAGE_USE_SAS_TOKENS=false"
    Write-Host ""
    Write-Host "💡 Your Discord bot will now return direct URLs without SAS tokens" -ForegroundColor Green
    
} else {
    Write-Host "🔐 Private Access Mode (Recommended)" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "🔒 Files are private and require authentication"
    Write-Host "🎫 URLs include SAS tokens for time-limited access"
    Write-Host "🛡️ Benefits: Secure, auditable, granular control"
    Write-Host "⚙️ Complexity: Longer URLs, token management"
    Write-Host ""
    Write-Host "🔗 URL Format: https://$StorageAccountName.blob.core.windows.net/$ContainerName/images/photo.jpg?sv=2021-06-08&ss=b..." -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "🔒 Setting container to private access..." -ForegroundColor Blue
    
    # Set container to private access
    az storage container set-permission `
        --name $ContainerName `
        --public-access off `
        --account-name $StorageAccountName `
        --resource-group $ResourceGroupName `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Container set to private access" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to set private access" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "📋 Environment Configuration:" -ForegroundColor Blue
    Write-Host "Add this to your .env.production file:"
    Write-Host "AZURE_STORAGE_USE_SAS_TOKENS=true"
    Write-Host ""
    Write-Host "💡 Your Discord bot will generate SAS tokens for secure access" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Container access configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Blue
Write-Host "1. Update your .env.production file with the setting above"
Write-Host "2. Redeploy your Container App with the new configuration"
Write-Host "3. Test Discord attachment uploads"
Write-Host ""

# Show current container permissions
Write-Host "📊 Current Container Permissions:" -ForegroundColor Blue
$permissions = az storage container show-permission `
    --name $ContainerName `
    --account-name $StorageAccountName `
    --output tsv --query "publicAccess"

switch ($permissions) {
    "blob" { Write-Host "   Public blob access (anyone can read files)" -ForegroundColor Yellow }
    "container" { Write-Host "   Public container access (anyone can list and read files)" -ForegroundColor Yellow }
    "off" { Write-Host "   Private access (SAS tokens required)" -ForegroundColor Green }
    $null { Write-Host "   Private access (SAS tokens required)" -ForegroundColor Green }
    default { Write-Host "   Unknown access level: $permissions" -ForegroundColor Gray }
}

Write-Host ""
Write-Host "💡 Recommendation: Keep private access for Discord media to protect user content" -ForegroundColor Cyan
