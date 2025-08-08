# Security Guidelines

## Environment Variables and Credentials

### Critical Security Rules
1. **NEVER commit `.env` files** - They contain sensitive credentials
2. **Use `.env.example`** as a template with placeholder values
3. **Generate strong API keys** - Use 32+ character random strings
4. **Rotate credentials regularly** - Especially if compromised
5. **Use environment-specific files** - `.env.development`, `.env.production`

### Setup Instructions

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your actual credentials:**
   - `DISCORD_BOT_TOKEN`: From Discord Developer Portal
   - `DISCORD_USER_ID`: Your Discord user ID (right-click profile → Copy ID)
   - `API_KEY`: Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - `GITHUB_TOKEN`: Personal Access Token with repo permissions
   - `GITHUB_REPO`: Format: `username/repository-name`

3. **Verify your .env is ignored:**
   ```bash
   git status  # Should not show .env file
   ```

### API Key Generation

Generate a secure API key:
```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using UV
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Discord Bot Setup

1. **Create Discord Application:**
   - Go to https://discord.com/developers/applications
   - Create New Application
   - Go to Bot section
   - Create Bot and copy token to `DISCORD_BOT_TOKEN`

2. **Get your Discord User ID:**
   - Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
   - Right-click your profile → Copy ID
   - Add to `DISCORD_USER_ID`

3. **Invite Bot to Server:**
   - Go to OAuth2 → URL Generator
   - Select `bot` and `applications.commands` scopes
   - Select required permissions
   - Use generated URL to invite bot

### GitHub Token Setup

1. **Create Personal Access Token:**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Generate new token (classic)
   - Select `repo` scope for full repository access
   - Copy token to `GITHUB_TOKEN`

### Security Best Practices

- **Use separate environments** for development, staging, and production
- **Store production secrets** in secure deployment environment variables
- **Never log sensitive information** in application logs
- **Implement proper error handling** to avoid credential leaks in error messages
- **Use HTTPS** for all API communications in production
- **Regular security audits** of dependencies and configurations

### Emergency Response

If credentials are accidentally committed:
1. **Immediately revoke** the exposed credentials
2. **Generate new credentials** and update environment
3. **Force push** to remove from git history (if recent)
4. **Audit logs** for any unauthorized access
5. **Update documentation** with lessons learned

### Deployment Security

- **Use encrypted environment variables** in production
- **Enable audit logging** for all API requests  
- **Implement rate limiting** to prevent abuse
- **Monitor for suspicious activity** patterns
- **Keep dependencies updated** for security patches
