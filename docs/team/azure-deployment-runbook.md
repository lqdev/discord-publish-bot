# Azure Container Apps Deployment Runbook

## 🚀 Complete Deployment Process

### Prerequisites
- Azure CLI installed and logged in (`az login`)
- Docker installed (for local testing)
- Azure subscription with Container Apps enabled

### 1. Initial Setup (One Time)

#### 1.1 Create Resource Group
```bash
az group create --name <your-resource-group> --location <your-region>
```

#### 1.2 Create Container Apps Environment
```bash
az containerapp env create \
  --name <your-environment-name> \
  --resource-group <your-resource-group> \
  --location <your-region>
```

### 2. Deploy Application

#### 2.1 Deploy Container App
```bash
az containerapp up \
  --name <your-container-app-name> \
  --resource-group <your-resource-group> \
  --source . \
  --env-vars ENVIRONMENT=production
```

#### 2.2 ⚠️ CRITICAL: Configure Environment Variables with Secrets
**Note**: `az containerapp up` resets environment configuration. Always run this after deployment:

```bash
az containerapp update \
  --name <your-container-app-name> \
  --resource-group <your-resource-group> \
  --set-env-vars \
    ENVIRONMENT=production \
    DISCORD_BOT_TOKEN=secretref:discord-bot-token \
    DISCORD_APPLICATION_ID=secretref:discord-application-id \
    DISCORD_PUBLIC_KEY=secretref:discord-public-key \
    DISCORD_USER_ID=secretref:discord-user-id \
    GITHUB_TOKEN=secretref:github-token \
    GITHUB_REPO=secretref:github-repo \
    API_KEY=secretref:api-key
```

### 3. Configure Secrets

#### 3.1 Run Secrets Setup Script
```bash
./scripts/azure-secrets-setup.ps1 \
  -ResourceGroupName <your-resource-group> \
  -ContainerAppName <your-container-app-name> \
  -EnvFile .env.production
```

### 4. Verification

#### 4.1 Check Health
```bash
curl https://<your-container-app>.<region>.azurecontainerapps.io/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "production",
  "discord_configured": true,
  "github_configured": true
}
```

#### 4.2 Check Revision Status
```bash
az containerapp revision list \
  --name <your-container-app-name> \
  --resource-group <your-resource-group> \
  --query "[].{Name:name,Active:properties.active,TrafficWeight:properties.trafficWeight,RunningState:properties.runningState}" \
  --output table
```

### 5. Discord Configuration

#### 5.1 Update Discord Developer Portal
1. Go to https://discord.com/developers/applications
2. Select your Discord application
3. Navigate to "General Information" tab
4. Set **Interactions Endpoint URL** to:
   ```
   https://<your-container-app>.<region>.azurecontainerapps.io/discord/interactions
   ```

### 6. Testing

#### 6.1 Test Discord Integration
1. Use `/post note` command in Discord
2. Fill out the modal form
3. Verify:
   - ✅ Feature branch created (not direct commit to main)
   - ✅ Pull request opened
   - ✅ Correct frontmatter format (`type`, `date`, `slug`)

## 🔧 Troubleshooting

### Revision Activation Failed
**Symptom**: New revision shows "Activation failed"
**Cause**: Missing environment variable configuration
**Solution**: Run step 2.2 to configure environment variables with secret references

### Container Won't Start
**Symptom**: No replicas, "Could not find a replica for this app"
**Cause**: Missing secrets or environment variables
**Solution**: 
1. Verify secrets exist: `az containerapp secret list --name <app> --resource-group <rg>`
2. Run secrets setup script (step 3.1)
3. Configure environment variables (step 2.2)

### Discord Interactions Not Working
**Symptom**: Discord commands don't respond
**Cause**: Interactions endpoint not configured or incorrect
**Solution**: Verify Discord Developer Portal endpoint URL (step 5.1)

## 📋 Environment Variables Reference

| Variable | Secret Ref | Description |
|----------|------------|-------------|
| `DISCORD_BOT_TOKEN` | `discord-bot-token` | Bot authentication token |
| `DISCORD_APPLICATION_ID` | `discord-application-id` | Application ID |
| `DISCORD_PUBLIC_KEY` | `discord-public-key` | Webhook verification key |
| `DISCORD_USER_ID` | `discord-user-id` | Authorized user ID |
| `GITHUB_TOKEN` | `github-token` | Repository access token |
| `GITHUB_REPO` | `github-repo` | Target repository |
| `API_KEY` | `api-key` | API authentication key |
| `ENVIRONMENT` | (direct) | Set to `production` |

## 🔒 Security Notes

- All sensitive values stored as Azure Container Apps secrets
- Environment variables reference secrets, never contain plaintext
- Secrets are encrypted at rest and in transit
- Use `.env.production` file for local secret management (never commit)
- Regular secret rotation recommended
