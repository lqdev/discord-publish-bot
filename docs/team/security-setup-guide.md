# Discord Publish Bot - Security Setup Guide
# For single-user, mobile-first publishing workflow

## 🔒 Security Architecture for Your Use Case

### Overview
Since you're the only user and usage is minimal, we can implement a simplified but secure approach:

1. **Local Development**: `.env` file on your machine (never committed)
2. **Azure Production**: Azure Container Apps secrets (encrypted, managed)
3. **Container**: No secrets in the image itself (runtime injection only)

## 🛡️ Security Implementation

### 1. Local Development Security
```bash
# Create your local .env file (copy from .env.production.example)
cp .env.production.example .env

# Edit with your actual values - this file is in .gitignore
code .env
```

**Your .env file structure:**
```bash
# Discord Configuration (from Discord Developer Portal)
DISCORD_BOT_TOKEN=Bot_YOUR_ACTUAL_TOKEN_HERE
DISCORD_APPLICATION_ID=123456789012345678
DISCORD_PUBLIC_KEY=your_public_key_here
DISCORD_USER_ID=your_user_id_here

# GitHub Configuration (Personal Access Token)
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=yourusername/yourrepo
```

### 2. Azure Production Security
- ✅ Secrets stored in Azure Container Apps encrypted storage
- ✅ Runtime injection only (never in container image)
- ✅ Audit logging of all secret access
- ✅ Network isolation and HTTPS enforcement

### 3. Container Security Features
- ✅ Non-root user (UID 1000)
- ✅ Minimal base image (Python slim)
- ✅ No credentials in image layers
- ✅ Security-optimized build process

## 🔑 Credential Sources & Permissions

### Discord Developer Portal Setup
1. Go to https://discord.com/developers/applications
2. Create/select your application
3. **Bot Section:**
   - Copy Bot Token → `DISCORD_BOT_TOKEN`
   - Enable required gateway intents
4. **General Information:**
   - Copy Application ID → `DISCORD_APPLICATION_ID`
   - Copy Public Key → `DISCORD_PUBLIC_KEY`
5. **Your User ID:**
   - In Discord: Settings → Advanced → Developer Mode (enable)
   - Right-click your profile → Copy ID → `DISCORD_USER_ID`

### GitHub Personal Access Token Setup
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. **Required scopes:**
   - ✅ `repo` (full repository access)
   - ✅ `workflow` (if using GitHub Actions)
4. Copy token → `GITHUB_TOKEN`
5. Set repository → `GITHUB_REPO` (format: username/repo-name)

## 🚀 Deployment Security Process

### Step 1: Local Testing
```bash
# Test locally with your .env file
docker-compose up --build

# Verify environment variables are loaded
curl http://localhost:8000/health
```

### Step 2: Azure Secrets Configuration
```bash
# Use our secure script to add secrets
.\scripts\azure-secrets-setup.ps1 -ResourceGroupName "rg-discord-bot" -ContainerAppName "discord-publish-bot"
```

### Step 3: Container Deployment
- Container gets secrets injected at runtime
- No secrets stored in container image
- Encrypted in transit and at rest

## 🔍 Security Monitoring

### What Azure Monitors:
- ✅ Secret access attempts and timing
- ✅ Container app authentication events
- ✅ Network traffic and API calls
- ✅ Resource usage and scaling events

### What You Can Monitor:
- ✅ Discord bot interactions (via logs)
- ✅ GitHub publishing success/failure rates
- ✅ Container health and performance
- ✅ Cost and resource consumption

## 🎯 Optimized for Your Usage Pattern

### Why This Approach Works for You:
1. **Single User**: Simplified auth - just your Discord user ID check
2. **Mobile Focus**: Minimal latency for quick posting
3. **Low Traffic**: Scale-to-zero saves costs (likely free tier)
4. **Secure**: Enterprise-grade security without complexity

### Cost Optimization:
- **Free Tier Coverage**: Your usage likely stays within free limits
- **Scale-to-Zero**: No costs when not posting
- **Efficient Images**: Fast startup for mobile posting sessions

## 🔧 Maintenance & Rotation

### Token Rotation Schedule:
- **Discord Bot Token**: Rotate every 6-12 months
- **GitHub Token**: Rotate every 6-12 months  
- **Azure Secrets**: Can be rotated without downtime

### Rotation Process:
1. Generate new token in respective service
2. Update secret in Azure using the setup script
3. Container automatically gets new secret on next restart
4. Revoke old token after verification

## 🚨 Security Incident Response

### If Credentials Are Compromised:
1. **Immediate**: Revoke token in Discord/GitHub
2. **Update**: Generate new token and update Azure secret
3. **Monitor**: Check audit logs for unauthorized usage
4. **Verify**: Test bot functionality with new credentials

### Monitoring for Issues:
- Unexpected API usage patterns
- Failed authentication attempts
- Unusual container scaling events
- High resource consumption

This security approach balances enterprise-grade protection with operational simplicity for your single-user, mobile posting use case.
