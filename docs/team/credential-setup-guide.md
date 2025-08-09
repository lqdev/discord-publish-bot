# Discord Bot Credential Setup Guide

## 🎯 **Step-by-Step Setup Process**

This guide walks you through setting up real Discord credentials using our security guidelines. Follow these steps in order for proper authentication setup.

### **Prerequisites**
- ✅ `.gitignore` file protecting credentials (already done)
- ✅ Security guidelines documentation available
- ✅ `.env.example` template ready

---

## 🔧 **Step 1: Create Discord Application**

### 1.1 Access Discord Developer Portal
1. Go to **https://discord.com/developers/applications**
2. Log in with your Discord account
3. Click **"New Application"**
4. Enter application name: `Discord Publish Bot`
5. Click **"Create"**

### 1.2 Get Application Credentials
From your new application:

**Application ID:**
- Copy from **General Information** tab
- This is your `DISCORD_APPLICATION_ID`

**Public Key:**
- Copy from **General Information** tab  
- This is your `DISCORD_PUBLIC_KEY`

---

## 🤖 **Step 2: Create Bot User**

### 2.1 Create Bot
1. Navigate to **"Bot"** tab in left sidebar
2. Click **"Add Bot"** 
3. Confirm by clicking **"Yes, do it!"**

### 2.2 Configure Bot Settings
**Bot Username:** Set to something descriptive like `PublishBot`

**Bot Token:**
1. Under **"Token"** section, click **"Reset Token"**
2. Confirm and copy the token immediately
3. This is your `DISCORD_BOT_TOKEN`

⚠️ **CRITICAL:** The bot token is shown only once. Copy it immediately!

### 2.3 Bot Permissions Setup
**Required Intents:**
- ✅ **Message Content Intent** (for reading message content)
- ✅ **Server Members Intent** (optional, for user validation)

**Bot Permissions:**
- ✅ **Send Messages** 
- ✅ **Use Slash Commands**
- ✅ **Read Message History**

---

## 🔑 **Step 3: Generate API Key**

Generate a secure API key for authentication between Discord bot and Publishing API:

```bash
# Using UV (recommended)
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"

# Alternative: Using Python directly
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the generated key - this is your `API_KEY`.

---

## 📝 **Step 4: Get Your Discord User ID**

### 4.1 Enable Developer Mode
1. Open Discord settings (gear icon)
2. Go to **Advanced** → **Developer Mode** → Enable

### 4.2 Get Your User ID
1. Right-click on your username/profile
2. Click **"Copy User ID"**
3. This is your `DISCORD_USER_ID`

---

## 🏠 **Step 5: Create Test Server (Optional)**

### 5.1 Create Server
1. In Discord, click **"+"** to add server
2. Choose **"Create My Own"**
3. Name it `Bot Testing Server`

### 5.2 Get Guild ID
1. Right-click on server name
2. Click **"Copy Server ID"**
3. This is your `DISCORD_GUILD_ID`

---

## 🔗 **Step 6: Setup GitHub Integration**

### 6.1 Create Personal Access Token
1. Go to **GitHub.com** → **Settings** → **Developer settings**
2. Click **Personal access tokens** → **Tokens (classic)**
3. Click **"Generate new token (classic)"**
4. Configure token:
   - **Note:** `Discord Publish Bot`
   - **Expiration:** 90 days (or No expiration for development)
   - **Scopes:** ✅ `repo` (Full control of private repositories)

5. Click **"Generate token"** and copy immediately
6. This is your `GITHUB_TOKEN`

### 6.2 Target Repository
Identify your target repository:
- Format: `username/repository-name`
- Example: `johndoe/my-blog`
- This is your `GITHUB_REPO`

---

## 📋 **Step 7: Configure Environment Variables**

### 7.1 Copy Template
```bash
cd c:\Dev\discord-publish-bot
cp .env.example .env
```

### 7.2 Fill in Credentials
Edit `.env` file with your actual values:

```env
# Discord Bot Configuration
DISCORD_BOT_TOKEN=YOUR_ACTUAL_BOT_TOKEN_HERE
DISCORD_USER_ID=YOUR_ACTUAL_USER_ID_HERE

# API Security  
API_KEY=YOUR_GENERATED_32_CHAR_KEY_HERE
FASTAPI_ENDPOINT=http://localhost:8000

# GitHub Integration
GITHUB_TOKEN=YOUR_GITHUB_PERSONAL_ACCESS_TOKEN
GITHUB_REPO=yourusername/your-repository-name
GITHUB_BRANCH=main

# Optional Configuration
SITE_BASE_URL=https://yoursite.com
LOG_LEVEL=INFO
ENVIRONMENT=development

# Discord Bot Development (if you created test server)
DISCORD_GUILD_ID=YOUR_TEST_SERVER_GUILD_ID
```

---

## 🔒 **Step 8: Security Verification**

### 8.1 Run Security Check
```bash
uv run python scripts/security-check.py
```

Expected output:
```
🔒 Discord Publish Bot Security Verification
==================================================
✅ PASS GitIgnore Configuration: .gitignore properly configured
✅ PASS Environment Files: Environment files properly configured  
✅ PASS Credential Setup: No placeholder values found in .env
==================================================
🎉 All security checks passed! Project is secure.
```

### 8.2 Verify Git Ignoring
```bash
git status
```
Should **NOT** show `.env` file in untracked files.

---

## 🎮 **Step 9: Invite Bot to Server**

### 9.1 Generate Invite URL
1. Go back to Discord Developer Portal
2. Navigate to **OAuth2** → **URL Generator**
3. **Scopes:** ✅ `bot` ✅ `applications.commands`
4. **Bot Permissions:** 
   - ✅ Send Messages
   - ✅ Use Slash Commands
   - ✅ Read Message History
5. Copy generated URL

### 9.2 Invite Bot
1. Open the generated URL in browser
2. Select your test server (or target server)
3. Click **"Authorize"**
4. Complete any captcha if required

---

## ✅ **Step 10: Test Authentication**

### 10.1 Test Discord Bot Connection
```bash
# Start Discord bot to test connection
uv run python src/discord_bot/main.py
```

Expected output:
```
INFO - Bot logged in as: YourBotName#1234
INFO - Bot is ready!
```

### 10.2 Test GitHub Access
```bash
# Test GitHub API connection
uv run python -c "
from github import Github
import os
from dotenv import load_dotenv

load_dotenv()
g = Github(os.getenv('GITHUB_TOKEN'))
repo = g.get_repo(os.getenv('GITHUB_REPO'))
print(f'✅ Successfully connected to: {repo.full_name}')
print(f'✅ Repository permissions: {repo.permissions}')
"
```

---

## 🛡️ **Security Best Practices Applied**

### ✅ **Credentials Protected**
- ✅ `.env` file ignored by git
- ✅ Strong API key generated (32+ characters)  
- ✅ Tokens scoped with minimal required permissions
- ✅ No credentials in source code

### ✅ **Environment Security**
- ✅ Development environment isolated
- ✅ Placeholder detection implemented
- ✅ Automated security verification

### ✅ **Access Control**
- ✅ Bot limited to specific user ID
- ✅ GitHub token scoped to repository access only
- ✅ Discord bot permissions minimized

---

## 🚨 **Troubleshooting**

### **Bot Token Issues**
- **Error:** `401 Unauthorized`
- **Solution:** Regenerate bot token in Discord Developer Portal

### **GitHub Access Issues**  
- **Error:** `403 Forbidden`
- **Solution:** Check GitHub token has `repo` scope and hasn't expired

### **Discord User ID Issues**
- **Error:** Bot doesn't respond to commands
- **Solution:** Verify `DISCORD_USER_ID` matches your actual Discord user ID

### **Permission Issues**
- **Error:** Bot can't send messages
- **Solution:** Re-invite bot with proper permissions using OAuth2 URL Generator

---

## 📞 **Support**

If you encounter issues:
1. Check security verification passes: `uv run python scripts/security-check.py`
2. Verify all environment variables are filled in `.env`
3. Ensure bot is invited to server with correct permissions
4. Check [Security Guidelines](docs/team/security-guidelines.md) for detailed troubleshooting

---

**Next Steps:** With credentials configured, you can proceed to implement Discord bot authentication in Sprint 2! 🚀
