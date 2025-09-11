# Azure Container Apps - Secure Secrets Setup Script
# This script helps you securely configure secrets for Discord Publish Bot
# It can read from .env files or prompt for manual input

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$ContainerAppName,
    
    [Parameter(Mandatory=$false)]
    [string]$EnvironmentName = "example-environment",
    
    [Parameter(Mandatory=$false)]
    [string]$EnvFile = ".env.production"
)

Write-Host "🔒 Discord Publish Bot - Azure Secrets Configuration" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

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

# Function to read .env file
function Read-EnvFile {
    param([string]$FilePath)
    
    if (-not (Test-Path $FilePath)) {
        Write-Warning "Environment file not found: $FilePath"
        return @{}
    }
    
    Write-Host "📁 Reading environment file: $FilePath" -ForegroundColor Green
    $envVars = @{}
    
    Get-Content $FilePath | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
            $parts = $line.Split('=', 2)
            if ($parts.Length -eq 2) {
                $key = $parts[0].Trim()
                $value = $parts[1].Trim()
                
                # Handle inline comments - remove everything after # (but preserve # in values if quoted)
                if ($value.Contains('#') -and -not ($value.StartsWith('"') -or $value.StartsWith("'"))) {
                    $commentIndex = $value.IndexOf('#')
                    $value = $value.Substring(0, $commentIndex).Trim()
                }
                
                # Remove surrounding quotes
                $value = $value.Trim('"').Trim("'")
                
                if ($value -and $value -ne "your_" -and -not $value.Contains("_here")) {
                    $envVars[$key] = $value
                }
            }
        }
    }
    
    return $envVars
}

# Function to securely prompt for secrets
function Get-SecureSecret {
    param([string]$SecretName, [string]$Description, [string]$CurrentValue = "")
    
    Write-Host "`n🔑 $SecretName" -ForegroundColor Magenta
    Write-Host "   $Description" -ForegroundColor Gray
    
    if ($CurrentValue) {
        $maskedValue = $CurrentValue.Substring(0, [Math]::Min(8, $CurrentValue.Length)) + "***"
        $response = Read-Host "Current value: $maskedValue. Press Enter to keep, or type new value"
        if ([string]::IsNullOrWhiteSpace($response)) {
            return $CurrentValue
        }
        return $response
    } else {
        $secret = Read-Host "Enter value (input will be hidden)" -AsSecureString
        $plainSecret = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret))
        
        if ([string]::IsNullOrWhiteSpace($plainSecret)) {
            Write-Warning "Skipping empty secret: $SecretName"
            return $null
        }
        
        return $plainSecret
    }
}

Write-Host "`n📝 Loading secrets from environment file or manual input" -ForegroundColor Yellow

# Try to read from environment file first
$envVars = Read-EnvFile $EnvFile

# Discord Secrets
Write-Host "`n🤖 DISCORD CONFIGURATION" -ForegroundColor Blue
Write-Host "Get these from: https://discord.com/developers/applications" -ForegroundColor Gray

$discordToken = Get-SecureSecret "DISCORD_BOT_TOKEN" "Your bot's secret token (starts with 'Bot ')" $envVars["DISCORD_BOT_TOKEN"]
$discordAppId = Get-SecureSecret "DISCORD_APPLICATION_ID" "Your application's ID (numeric)" $envVars["DISCORD_APPLICATION_ID"]
$discordPublicKey = Get-SecureSecret "DISCORD_PUBLIC_KEY" "Your application's public key (for webhook verification)" $envVars["DISCORD_PUBLIC_KEY"]
$discordUserId = Get-SecureSecret "DISCORD_USER_ID" "Your Discord user ID (for authorization)" $envVars["DISCORD_USER_ID"]

# GitHub Secrets
Write-Host "`n🐙 GITHUB CONFIGURATION" -ForegroundColor Blue
Write-Host "Get these from: https://github.com/settings/tokens" -ForegroundColor Gray

$githubToken = Get-SecureSecret "GITHUB_TOKEN" "Personal access token with 'repo' permissions" $envVars["GITHUB_TOKEN"]
$githubRepo = if ($envVars["GITHUB_REPO"]) { 
    $envVars["GITHUB_REPO"]
} else { 
    Read-Host "GitHub repository (format: username/repo-name)" 
}

# API Configuration
Write-Host "`n🔐 API CONFIGURATION" -ForegroundColor Blue

$apiKey = Get-SecureSecret "API_KEY" "API key for authentication (32+ characters)" $envVars["API_KEY"]

# Storage Provider Configuration
Write-Host "`n☁️ STORAGE PROVIDER CONFIGURATION" -ForegroundColor Blue
Write-Host "For permanent media hosting in Discord bot" -ForegroundColor Gray

$storageProvider = if ($envVars["STORAGE_PROVIDER"]) { 
    $envVars["STORAGE_PROVIDER"]
} else { 
    $defaultProvider = "linode"
    $userInput = Read-Host "Storage Provider (azure/linode, default: $defaultProvider)"
    if ([string]::IsNullOrWhiteSpace($userInput)) { $defaultProvider } else { $userInput }
}

# Azure Storage Configuration (if using Azure)
if ($storageProvider -eq "azure") {
    Write-Host "`n☁️ AZURE STORAGE CONFIGURATION" -ForegroundColor Blue
    
    $storageAccountName = if ($envVars["AZURE_STORAGE_ACCOUNT_NAME"]) { 
        $envVars["AZURE_STORAGE_ACCOUNT_NAME"]
    } else { 
        Read-Host "Azure Storage Account Name (existing account)" 
    }

    $storageContainerName = if ($envVars["AZURE_STORAGE_CONTAINER_NAME"]) { 
        $envVars["AZURE_STORAGE_CONTAINER_NAME"]
    } else { 
        $defaultContainer = "files"
        $userInput = Read-Host "Storage Container Name (default: $defaultContainer)"
        if ([string]::IsNullOrWhiteSpace($userInput)) { $defaultContainer } else { $userInput }
    }
}

# Linode Object Storage Configuration (if using Linode)
if ($storageProvider -eq "linode") {
    Write-Host "`n🌐 LINODE OBJECT STORAGE CONFIGURATION" -ForegroundColor Blue
    
    $linodeAccessKey = Get-SecureSecret "LINODE_STORAGE_ACCESS_KEY_ID" "Linode Object Storage Access Key ID" $envVars["LINODE_STORAGE_ACCESS_KEY_ID"]
    $linodeSecretKey = Get-SecureSecret "LINODE_STORAGE_SECRET_ACCESS_KEY" "Linode Object Storage Secret Access Key" $envVars["LINODE_STORAGE_SECRET_ACCESS_KEY"]
    
    $linodeBucket = if ($envVars["LINODE_STORAGE_BUCKET_NAME"]) { 
        $envVars["LINODE_STORAGE_BUCKET_NAME"]
    } else { 
        Read-Host "Linode Storage Bucket Name (e.g., cdn.lqdev.tech)" 
    }
    
    $linodeRegion = if ($envVars["LINODE_STORAGE_REGION"]) { 
        $envVars["LINODE_STORAGE_REGION"]
    } else { 
        $defaultRegion = "us-ord-1"
        $userInput = Read-Host "Linode Storage Region (default: $defaultRegion)"
        if ([string]::IsNullOrWhiteSpace($userInput)) { $defaultRegion } else { $userInput }
    }
    
    $linodeCustomDomain = if ($envVars["LINODE_STORAGE_CUSTOM_DOMAIN"]) { 
        $envVars["LINODE_STORAGE_CUSTOM_DOMAIN"]
    } else { 
        Read-Host "Custom CDN Domain (e.g., https://cdn.lqdev.tech)" 
    }
}

# Create secrets in Azure Container Apps
Write-Host "`n🚀 Creating secrets in Azure Container Apps..." -ForegroundColor Green

$secretsToCreate = @()

if ($discordToken) {
    $secretsToCreate += @{name="discord-bot-token"; value=$discordToken}
}
if ($discordAppId) {
    $secretsToCreate += @{name="discord-application-id"; value=$discordAppId}
}
if ($discordPublicKey) {
    $secretsToCreate += @{name="discord-public-key"; value=$discordPublicKey}
}
if ($discordUserId) {
    $secretsToCreate += @{name="discord-user-id"; value=$discordUserId}
}
if ($githubToken) {
    $secretsToCreate += @{name="github-token"; value=$githubToken}
}
if ($githubRepo) {
    $secretsToCreate += @{name="github-repo"; value=$githubRepo}
}
if ($apiKey) {
    $secretsToCreate += @{name="api-key"; value=$apiKey}
}

# Storage provider configuration
if ($storageProvider) {
    $secretsToCreate += @{name="storage-provider"; value=$storageProvider}
}

# Azure Storage secrets (if using Azure)
if ($storageProvider -eq "azure") {
    if ($storageAccountName) {
        $secretsToCreate += @{name="azure-storage-account-name"; value=$storageAccountName}
    }
    if ($storageContainerName) {
        $secretsToCreate += @{name="azure-storage-container-name"; value=$storageContainerName}
    }
}

# Linode Object Storage secrets (if using Linode)
if ($storageProvider -eq "linode") {
    if ($linodeAccessKey) {
        $secretsToCreate += @{name="linode-storage-access-key-id"; value=$linodeAccessKey}
    }
    if ($linodeSecretKey) {
        $secretsToCreate += @{name="linode-storage-secret-access-key"; value=$linodeSecretKey}
    }
    if ($linodeBucket) {
        $secretsToCreate += @{name="linode-storage-bucket-name"; value=$linodeBucket}
    }
    if ($linodeRegion) {
        $secretsToCreate += @{name="linode-storage-region"; value=$linodeRegion}
    }
    if ($linodeCustomDomain) {
        $secretsToCreate += @{name="linode-storage-custom-domain"; value=$linodeCustomDomain}
    }
    
    # Add endpoint URL based on region
    if ($linodeRegion) {
        $linodeEndpointUrl = "https://$linodeRegion.linodeobjects.com"
        $secretsToCreate += @{name="linode-storage-endpoint-url"; value=$linodeEndpointUrl}
    }
}

foreach ($secret in $secretsToCreate) {
    Write-Host "   Adding secret: $($secret.name)" -ForegroundColor Yellow
    
    try {
        az containerapp secret set `
            --name $ContainerAppName `
            --resource-group $ResourceGroupName `
            --secrets "$($secret.name)=$($secret.value)" `
            --output none
        
        Write-Host "   ✅ Secret '$($secret.name)' added successfully" -ForegroundColor Green
    } catch {
        Write-Error "Failed to add secret '$($secret.name)': $_"
    }
}

Write-Host "`n🎉 Secrets configuration complete!" -ForegroundColor Green
Write-Host "Your secrets are now securely stored in Azure and will be" -ForegroundColor Gray
Write-Host "automatically injected into your container at runtime." -ForegroundColor Gray

Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Update your container app configuration to reference these secrets" -ForegroundColor White
Write-Host "2. Deploy your container app with: az containerapp up" -ForegroundColor White
Write-Host "3. Verify secrets are properly injected via environment variables" -ForegroundColor White
Write-Host "4. Test Discord interactions and GitHub publishing" -ForegroundColor White

Write-Host "`n💡 Usage examples:" -ForegroundColor Yellow
Write-Host "# Use default .env.production file:" -ForegroundColor White
Write-Host "./azure-secrets-setup.ps1 -ResourceGroupName my-rg -ContainerAppName my-app" -ForegroundColor Gray
Write-Host "`n# Use custom .env file:" -ForegroundColor White
Write-Host "./azure-secrets-setup.ps1 -ResourceGroupName my-rg -ContainerAppName my-app -EnvFile .env.staging" -ForegroundColor Gray

Write-Host "`n🔒 Security Notes:" -ForegroundColor Yellow
Write-Host "• Secrets are encrypted at rest in Azure" -ForegroundColor White
Write-Host "• Secrets are only accessible to your container app" -ForegroundColor White
Write-Host "• You can rotate secrets anytime using this script" -ForegroundColor White
Write-Host "• Audit logs track all secret access" -ForegroundColor White
Write-Host "• .env files are never uploaded to Azure - only values are extracted" -ForegroundColor White
