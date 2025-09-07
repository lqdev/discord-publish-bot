# Azure Container Apps Deployment Runbook

## 🚀 Complete Deployment Process

### Prerequisites
- Azure CLI installed and logged in (`az login`)
- Docker installed (for local testing)
- Azure subscription with Container Apps enabled

### 0. Resource Discovery (Required Before Deployment)

#### 0.1 Discover Resource Groups
```bash
# Find resource groups for the current project
az group list --query "[].{Name:name,Location:location}" --output table
```

#### 0.2 Discover Container Apps
```bash
# List all container apps in discovered resource group
az containerapp list --resource-group <discovered-resource-group> --query "[].{Name:name,Status:properties.provisioningState,FQDN:properties.configuration.ingress.fqdn}" --output table
```

#### 0.3 Verify Current Status
```bash
# Check current container app status
az containerapp show --name <discovered-container-app> --resource-group <discovered-resource-group> --query "{name:name,status:properties.provisioningState,fqdn:properties.configuration.ingress.fqdn,activeRevisions:properties.latestRevisionName}" --output table
```

**Use discovered values in all subsequent commands below**

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
# Use values discovered in step 0
az containerapp up \
  --name <discovered-container-app-name> \
  --resource-group <discovered-resource-group> \
  --source . \
  --env-vars ENVIRONMENT=production
```

#### 2.2 ⚠️ CRITICAL: Configure Environment Variables with Secrets
**Note**: `az containerapp up` resets environment configuration. Always run this after deployment:

```bash
# Use discovered values from step 0
az containerapp update \
  --name <discovered-container-app-name> \
  --resource-group <discovered-resource-group> \
  --set-env-vars \
    ENVIRONMENT=production \
    AZURE_STORAGE_USE_RELATIVE_PATHS=true \
    AZURE_STORAGE_USE_SAS_TOKENS=false \
    ENABLE_AZURE_STORAGE=true \
    AZURE_STORAGE_ACCOUNT_NAME=secretref:azure-storage-account-name \
    AZURE_STORAGE_CONTAINER_NAME=secretref:azure-storage-container-name \
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
# Use discovered values from step 0
./scripts/azure-secrets-setup.ps1 \
  -ResourceGroupName <discovered-resource-group> \
  -ContainerAppName <discovered-container-app-name> \
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

## 📚 Deployment Lessons Learned

### Timezone Consistency Fix Deployment (2025-08-21)
**Issue**: Timezone inconsistency in frontmatter date fields across different content types
**Solution**: Updated PublishingService._generate_frontmatter() to use consistent -05:00 timezone format
**Deployment**: Successful production deployment with timezone fix (version 2.2.3)

#### Key Learnings
1. **Docker Build Resilience**: Initial network timeout during Docker layer pull resolved with simple retry
   - First attempt failed with "net/http: request canceled while waiting for connection"
   - Second attempt completed successfully without any configuration changes
   - Azure Container Registry build process handles transient network issues with retry strategy

2. **Environment Variable Restoration**: Critical step 2.2 successfully restores production configuration
   - `az containerapp up` resets environment variables as documented
   - Secret references properly restored with update command
   - All 9 required secrets maintained proper mapping to environment variables

3. **Health Verification Process**:
   - Health endpoint confirmed all services operational immediately after deployment
   - Version verification showed successful update to 2.2.3
   - Discord and GitHub integrations maintained full functionality

4. **Production Deployment Pattern Validation**:
   - Change identification → Local fix → Production deployment → Health verification
   - Total deployment time: ~45 minutes including initial timeout retry
   - Zero downtime deployment achieved with Container Apps revision model
   - Revision ca-discord-publish-bot--0000046 successfully activated

#### Enhanced Deployment Best Practices
- **Retry Strategy**: Network timeouts during Docker build are transient; simple retry resolves issue
- **Environment Configuration**: Always execute step 2.2 immediately after `az containerapp up`
- **Health Monitoring**: Verify both health endpoint and functional integration post-deployment
- **Documentation Integration**: Update changelog with deployment details for operational tracking

### Critical Modal Routing & Response Type Enhancement (2025-08-10)
**Issue**: Discord commands showed wrong modals for different post types; users limited to "reply" responses only
**Solution**: Modal parsing fix + response type selection implementation with correct frontmatter values
**Deployment**: Successful same-day feature enhancement with zero downtime

#### Key Learnings
1. **Azure CLI PATH**: Ensure Azure CLI is in system PATH before deployment
   - Location: `C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin`
   - Add to session: `$env:PATH += ";C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"`

2. **Environment Variable Persistence**: Always run step 2.2 after `az containerapp up`
   - Command resets environment configuration
   - Secret references must be re-applied after deployment
   - Monitor container logs to verify successful startup

3. **Health Verification Process**: 
   - Check application logs: `az containerapp logs show -n <app> -g <rg> --tail 10`
   - Verify health endpoint: PowerShell `Invoke-WebRequest` for JSON response
   - Test functional endpoints before marking deployment complete

4. **Enhanced Rapid Development Pattern**:
   - Bug identification → Modal parsing fix → Response type enhancement → Production deployment → User validation
   - Total time: ~45 minutes for complete feature enhancement from bug report to user validation
   - Zero downtime deployment with scale-to-zero architecture
   - Command registration automation for Discord global command updates

5. **Feature Enhancement Deployment**:
   - Custom_id parsing complexity requires thorough testing for compound identifiers
   - Import scope management critical for function-level variable usage
   - User-specific frontmatter requirements ("reshare", "star") accommodated through enum value mapping

#### Best Practices Validated
- **Incremental Testing**: Local validation before deployment prevents production issues
- **Container Health Checks**: Built-in health endpoint enables quick verification
- **Secret Management**: Proper secret references maintain security during rapid deployments
- **Documentation Integration**: ADR creation ensures architectural decisions are captured
- Regular secret rotation recommended
