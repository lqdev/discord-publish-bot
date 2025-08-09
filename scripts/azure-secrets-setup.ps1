# Azure Container Apps - Secure Secrets Setup Script
# This script helps you securely configure secrets for Discord Publish Bot

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$ContainerAppName,
    
    [Parameter(Mandatory=$false)]
    [string]$EnvironmentName = "example-environment"
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

Write-Host "`n📝 This script will help you securely add secrets to Azure Container Apps" -ForegroundColor Yellow
Write-Host "Your secrets will be encrypted and managed by Azure - never stored in code!" -ForegroundColor Yellow

# Function to securely prompt for secrets
function Get-SecureSecret {
    param([string]$SecretName, [string]$Description)
    
    Write-Host "`n🔑 $SecretName" -ForegroundColor Magenta
    Write-Host "   $Description" -ForegroundColor Gray
    
    $secret = Read-Host "Enter value (input will be hidden)" -AsSecureString
    $plainSecret = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret))
    
    if ([string]::IsNullOrWhiteSpace($plainSecret)) {
        Write-Warning "Skipping empty secret: $SecretName"
        return $null
    }
    
    return $plainSecret
}

# Discord Secrets
Write-Host "`n🤖 DISCORD CONFIGURATION" -ForegroundColor Blue
Write-Host "Get these from: https://discord.com/developers/applications" -ForegroundColor Gray

$discordToken = Get-SecureSecret "DISCORD_BOT_TOKEN" "Your bot's secret token (starts with 'Bot ')"
$discordAppId = Get-SecureSecret "DISCORD_APPLICATION_ID" "Your application's ID (numeric)"
$discordPublicKey = Get-SecureSecret "DISCORD_PUBLIC_KEY" "Your application's public key (for webhook verification)"
$discordUserId = Get-SecureSecret "DISCORD_USER_ID" "Your Discord user ID (for authorization)"

# GitHub Secrets
Write-Host "`n🐙 GITHUB CONFIGURATION" -ForegroundColor Blue
Write-Host "Get these from: https://github.com/settings/tokens" -ForegroundColor Gray

$githubToken = Get-SecureSecret "GITHUB_TOKEN" "Personal access token with 'repo' permissions"
$githubRepo = Read-Host "GitHub repository (format: username/repo-name)"

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
Write-Host "1. Deploy your container app" -ForegroundColor White
Write-Host "2. Verify secrets are properly injected" -ForegroundColor White
Write-Host "3. Test Discord interactions" -ForegroundColor White

Write-Host "`n🔒 Security Notes:" -ForegroundColor Yellow
Write-Host "• Secrets are encrypted at rest in Azure" -ForegroundColor White
Write-Host "• Secrets are only accessible to your container app" -ForegroundColor White
Write-Host "• You can rotate secrets anytime using this script" -ForegroundColor White
Write-Host "• Audit logs track all secret access" -ForegroundColor White
