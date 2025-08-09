# ADR-005: Docker Container Optimization for Azure Container Apps

## Status
**ACCEPTED** - Implemented and validated (2025-08-09)

## Context
Phase 1 of Azure Container Apps deployment required optimizing the Discord Publish Bot for containerized production deployment. Initial attempts revealed several critical issues:

1. **Container Size**: Unoptimized builds were exceeding 1GB
2. **Security**: Containers running as root user
3. **Startup Issues**: Module path resolution problems preventing application startup
4. **Credential Validation**: Strict validation preventing local testing
5. **Multi-stage Confusion**: Dockerfile stage ordering causing wrong entry points

### Research Insights
- Industry research via Microsoft Docs and Perplexity validated Azure Container Apps approach
- 2025 Docker naming best practices research identified semantic versioning + Git traceability patterns
- Container security research confirmed non-root user requirements (UID 1000)

## Decision

### Multi-Stage Docker Build Architecture
```dockerfile
# Build stage: Dependencies only
FROM python:3.11-slim AS builder
# Production base: Runtime environment
FROM python:3.11-slim AS production-base  
# Final production: Default stage with correct entry point
FROM production-base AS production
```

### Key Optimizations Implemented
1. **Size Optimization**: Multi-stage build reducing image from 1GB+ to 224MB
2. **Security Hardening**: Non-root user (UID/GID 1000) following Azure best practices
3. **Startup Reliability**: Direct uvicorn import resolving module path issues
4. **Health Monitoring**: Comprehensive `/health` endpoint with 60s start period
5. **Environment Validation**: Strict credential validation preventing production leakage

### 2025 Naming Strategy
- **Registry**: `your-discord-bot.azurecr.io` (globally unique)
- **Repository**: `personal/discord-publish-bot` (team/project pattern)
- **Tags**: Semantic versioning + Git SHA + environment context
- **Example**: `your-discord-bot.azurecr.io/personal/discord-publish-bot:v0.2.0-5cfbd23-dev`

### Entry Point Resolution
**Problem**: Multi-stage Dockerfile with conflicting entry points
**Solution**: Ordered stages with production as final default stage
```dockerfile
CMD ["python", "-c", "import uvicorn; from discord_publish_bot.api import app; uvicorn.run(app, host='0.0.0.0', port=8000)"]
```

## Consequences

### Positive
- ✅ **224MB optimized image** (vs 1GB+ unoptimized)
- ✅ **Production security compliance** (non-root user, credential validation)
- ✅ **Local testing capability** with properly formatted test credentials
- ✅ **Health monitoring** with comprehensive status reporting
- ✅ **Azure Container Apps ready** following industry best practices
- ✅ **2025 naming compliance** with semantic versioning and Git traceability

### Technical Validation
```json
{
  "status": "healthy",
  "version": "2.0.0", 
  "environment": "development",
  "discord_configured": true,
  "github_configured": true,
  "timestamp": "2025-08-09T15:04:49.304920"
}
```

### Risks Mitigated
- **Container Security**: Non-root user prevents privilege escalation
- **Credential Leakage**: Strict validation prevents production secrets in containers
- **Build Performance**: Multi-stage optimization reduces build time and image size
- **Deployment Reliability**: Health checks ensure proper startup validation

### Next Phase Enablement
Container optimization enables **Phase 2: Azure Resource Setup** with:
- Production-ready image for Azure Container Registry
- Validated security compliance for Azure Container Apps
- Proven health monitoring for Azure deployment pipelines
- Established naming conventions for production deployment

## Implementation Details

### Test Credentials Format (Development Only)
```bash
DISCORD_BOT_TOKEN="MTIzNDU2Nzg5MDEyMzQ1Njc4.FAKE.TEST_TOKEN_NEVER_REAL_SAFE_FOR_TESTING"
DISCORD_USER_ID="987654321098765432"
GITHUB_TOKEN="ghp_FAKE_TEST_TOKEN_SAFE_1234567890abcdef_NEVER_REAL"
GITHUB_REPO="test-user/test-repo-safe"
API_KEY="test_api_key_SAFE_FAKE_1234567890abcdef_NEVER_REAL"
```

### Build and Test Commands
```bash
# Build with proper naming
.\scripts\docker-naming.ps1 -Build

# Local testing
docker run -p 8000:8000 [test-credentials] your-discord-bot.azurecr.io/personal/discord-publish-bot:latest-dev

# Health validation
curl http://localhost:8000/health
```

## References
- **Industry Research**: Microsoft Azure Container Apps documentation
- **Naming Research**: 2025 Docker registry best practices via Perplexity
- **Security Standards**: Azure Container Apps security guidelines
- **Project Plan**: `projects/active/azure-container-apps-deployment.md`
- **Implementation**: `TOMORROW-CHECKLIST.md` Phase 1 validation
