# Discord Integration Setup - Phase 4
**Product:** Discord Publish Bot Production Integration  
**Date:** 2025-08-10  
**Status:** Active  
**Priority:** CRITICAL - Bot functionality dependent  

## Executive Summary

Connect the deployed Azure Container Apps Discord bot to Discord platform for production use. This enables the complete Discord → Azure → GitHub publishing workflow that users need.

### Key Objectives
- Configure Discord application to use Azure Container Apps endpoint
- Register production slash commands
- Validate webhook signature verification
- Test complete end-to-end publishing workflow

### Success Metrics
- ✅ Discord slash commands respond in production
- ✅ Azure health endpoint accessible from Discord
- ✅ Complete publishing workflow (Discord → GitHub PR creation)
- ✅ Response time <3 seconds for Discord interactions

## Current State Assessment

### ✅ **Infrastructure Ready** - VERIFIED
- **Azure Container Apps**: `<your-container-app>.<region>.azurecontainerapps.io` - HEALTHY
- **Health Endpoint**: `/health` returning `{"status":"healthy","version":"2.0.0","environment":"production","discord_configured":true,"github_configured":true}`
- **API Endpoints**: All publishing endpoints deployed and functional
- **Security**: All Discord secrets properly configured in Azure Container Apps
- **Resource Group**: `<your-resource-group>` - ACTIVE

### 🎯 **IMMEDIATE NEXT STEP - Discord Developer Portal Configuration**
- **Interactions Endpoint**: Configure Discord app to use `https://<your-container-app>.<region>.azurecontainerapps.io/discord/interactions`
- **Status**: Azure endpoint validated and ready for Discord configuration

## Implementation Plan

### Step 1: ✅ Azure Endpoint Identification - COMPLETED

**Azure Container App URL**: `https://ca-discord-publish-bot.kindpond-ed8a3757.eastus2.azurecontainerapps.io`  
**Resource Group**: `rg-discord-publish-bot-prod`  
**Health Status**: HEALTHY (Version 2.0.0, production environment)  
**Discord Configuration**: ✅ All secrets configured  

**Validation Completed**:
- ✅ Health endpoint responding: `{"status":"healthy","version":"2.0.0","environment":"production","discord_configured":true,"github_configured":true}`
- ✅ Interactions endpoint exists: `/discord/interactions` (returns Method Not Allowed for GET - correct behavior)
- ✅ Azure secrets configured: discord-bot-token, discord-application-id, discord-public-key, discord-user-id

### Step 2: Discord Developer Portal Configuration (10 minutes)

#### 2.1 Access Discord Application
1. **Navigate**: [Discord Developer Portal](https://discord.com/developers/applications)
2. **Select**: Your Discord Publish Bot application
3. **Go to**: "General Information" tab

#### 2.2 Update Interactions Endpoint URL - **CURRENT ACTION**
**Current Setting**: Likely empty or localhost URL  
**New Setting**: `https://ca-discord-publish-bot.kindpond-ed8a3757.eastus2.azurecontainerapps.io/discord/interactions`

**⚡ IMMEDIATE CONFIGURATION STEPS:**
1. **Interactions Endpoint URL**: `https://ca-discord-publish-bot.kindpond-ed8a3757.eastus2.azurecontainerapps.io/discord/interactions`
2. **Save Changes** - Discord will validate the endpoint automatically
3. **Verify**: Discord validation should succeed (Azure endpoint is ready)

#### 2.3 Register Slash Commands (Production)
**Commands to Register:**
```json
[
  {
    "name": "post",
    "description": "Publish content to GitHub",
    "options": [
      {
        "name": "type",
        "description": "Type of post",
        "type": 3,
        "required": true,
        "choices": [
          {"name": "note", "value": "note"},
          {"name": "response", "value": "response"},
          {"name": "bookmark", "value": "bookmark"},
          {"name": "media", "value": "media"}
        ]
      }
    ]
  }
]
```

### Step 3: Test Endpoint Connectivity (10 minutes)

#### 3.1 Verify Azure Health Endpoint
```bash
# Test health endpoint
curl https://<azure-fqdn>/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "environment": "production",
  "discord_configured": true,
  "github_configured": true,
  "timestamp": "2025-08-10T..."
}
```

#### 3.2 Test Discord Interactions Endpoint
```bash
# Test interactions endpoint (should reject without proper headers)
curl https://<azure-fqdn>/discord/interactions
```

**Expected Response**: 401/403 error (proper security)

### Step 4: Discord Webhook Validation (15 minutes)

#### 4.1 Discord Validation Process
When you save the interactions endpoint URL, Discord will:
1. **Send** a `PING` interaction to your endpoint
2. **Expect** a `PONG` response with type `1`
3. **Validate** the signature using your public key

#### 4.2 Troubleshooting Common Issues
**Issue**: "The interactions endpoint URL is invalid"
**Causes**:
- Azure Container App not responding
- Incorrect URL path
- Signature verification failing
- Timeout (>3 seconds response)

**Debug Steps**:
1. **Check Azure Logs**: Look for incoming requests
2. **Verify Public Key**: Ensure it matches Discord application
3. **Test Locally**: Use ngrok to test signature validation

### Step 5: End-to-End Testing (20 minutes)

#### 5.1 Test Discord Commands
**In Discord Server:**
1. **Type**: `/post note`
2. **Fill Modal**: Add title, content, tags
3. **Submit**: Check for success response
4. **Verify**: Check GitHub for PR creation

#### 5.2 Validate Complete Workflow
**Expected Flow:**
```
Discord User → /post note → Modal Form → Submit
    ↓
Azure Container Apps → Process Content → Generate Frontmatter
    ↓
GitHub API → Create Branch → Create PR → Return Success
    ↓
Discord Response → "PR created successfully: #123"
```

### Step 6: Production Validation (10 minutes)

#### 6.1 GitHub Integration Test
**Verify**:
- ✅ PR created with correct branch name
- ✅ Frontmatter matches VS Code snippet schema
- ✅ Content properly formatted
- ✅ File placed in correct directory (`_src/feed/`)

#### 6.2 Performance Validation
**Metrics**:
- ✅ Response time <3 seconds
- ✅ No timeout errors
- ✅ Proper error handling

## Implementation Commands

### Get Azure URL
```bash
# PowerShell command to get Azure Container App URL
az containerapp show --name ca-discord-publish-bot --resource-group discord-bot-rg --query "properties.configuration.ingress.fqdn" --output tsv
```

### Test Health Endpoint
```bash
# Test the health endpoint
$azureUrl = "https://$(az containerapp show --name ca-discord-publish-bot --resource-group discord-bot-rg --query 'properties.configuration.ingress.fqdn' --output tsv)"
curl "$azureUrl/health"
```

## Risk Assessment

### High Risk Items
**Risk**: Discord validation fails due to signature mismatch  
**Impact**: Cannot connect Discord to Azure  
**Mitigation**: Verify public key configuration in Azure secrets

**Risk**: Azure Container App not responding to Discord  
**Impact**: Timeout during Discord validation  
**Mitigation**: Check Azure Container App logs and scaling

### Medium Risk Items
**Risk**: GitHub token permissions insufficient  
**Impact**: Publishing fails after Discord integration works  
**Mitigation**: Test GitHub operations before Discord setup

## Success Criteria

### Technical Success
- ✅ Discord Developer Portal shows green status for interactions endpoint
- ✅ Slash commands appear in Discord server
- ✅ Commands respond without timeout
- ✅ Modal submissions process successfully

### User Success
- ✅ User can type `/post note` and see the command
- ✅ Modal opens with proper form fields
- ✅ Submission creates GitHub PR
- ✅ User receives success confirmation with PR link

## Troubleshooting Guide

### Discord Validation Issues
**Symptom**: "Invalid interactions endpoint URL"
**Solution**:
1. Check Azure Container App is running: `az containerapp show --name ca-discord-publish-bot --resource-group discord-bot-rg`
2. Test health endpoint manually
3. Verify Discord public key in Azure secrets
4. Check Azure Container App logs for validation attempts

### Performance Issues
**Symptom**: Discord command timeouts
**Solution**:
1. Check Azure Container App scaling (should scale from 0 to 1 when needed)
2. Verify health endpoint responds quickly
3. Monitor Azure Application Insights for performance

### GitHub Integration Issues
**Symptom**: Discord works but no GitHub PR created
**Solution**:
1. Test GitHub token permissions
2. Check Azure Container App logs for GitHub API errors
3. Verify repository configuration

## Next Steps After Completion

1. **✅ Discord Integration Complete**: Bot functional for end users
2. **🎯 Phase 5**: Set up CI/CD pipeline for automated deployments
3. **🎯 Phase 6**: Add monitoring and alerting
4. **🎯 Phase 7**: Performance optimization and scaling

---

**Implementation Time**: 60 minutes  
**Dependencies**: Azure Container Apps deployment completed  
**Validation**: End-to-end Discord → GitHub workflow successful
