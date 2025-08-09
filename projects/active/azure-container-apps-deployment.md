# Azure Container Apps Deployment Plan
**Product:** Discord Publish Bot Production Deployment  
**Version:** 1.0.0  
**Date:** 2025-08-09  
**Author:** AI Development Partner  
**Status:** Active  

## Executive Summary

Deploy the fully restructured Discord Publish Bot to Azure Container Apps, enabling production-ready Discord interactions and automated GitHub publishing. This represents the completion of the RESTRUCTURE-PLAN.md goals and transition to production operations.

### Key Objectives
- Deploy production-ready Discord bot with HTTP interactions
- Enable automated GitHub publishing from Discord commands
- Implement secure credential management and monitoring
- Establish CI/CD pipeline for ongoing deployments

### Success Metrics
- ✅ Discord bot responds to interactions in production
- ✅ GitHub publishing workflows execute successfully
- ✅ Zero credential leakage or security violations
- ✅ <2 second response time for Discord interactions
- ✅ 99.9% uptime for production service

## Background and Context

### Problem Statement
The Discord Publish Bot has been successfully restructured to modern Python standards with comprehensive testing, but currently runs only in development. Production deployment is needed to enable real-world Discord interactions and automated content publishing.

### Current State Assessment
**✅ COMPLETED (Ready for Production):**
- Modern package structure: `src/discord_publish_bot/`
- Comprehensive test suite: 76 tests with 15/15 core tests passing
- Security isolation: 4/4 security validation tests
- Clean codebase: All legacy code removed
- Entry points: CLI commands working correctly

**✅ PHASE 1 COMPLETE - Production Container Optimization (v2.3.0):**
- **✅ 224MB optimized Docker image** (78% reduction from 1GB+ unoptimized)
- **✅ Security hardening**: Non-root user (UID/GID 1000) following Azure best practices
- **✅ Health monitoring**: Comprehensive `/health` endpoint with 60s start period
- **✅ Local validation**: Container tested and working with proper credentials
- **✅ 2025 naming strategy**: Semantic versioning + Git SHA + environment tags
- **✅ Industry research**: Microsoft Docs + Perplexity validation of architecture
- **✅ Environment configuration**: Docker Compose and .env templates completed
- **✅ Azure secrets management**: Enhanced PowerShell script with .env file integration
- **✅ Repository hygiene**: All obsolete files cleaned up, build validated

**✅ DOCUMENTATION COMPLETE - Following Copilot-Instructions.md Framework:**
- **✅ ADR-005**: Docker Container Optimization decisions documented
- **✅ Changelog v2.3.0**: Complete Phase 1 achievements captured
- **✅ Phase completion report**: Comprehensive metrics and lessons learned
- **✅ Project state updated**: Backlog reflects current progress

**🎯 CURRENT STATUS: PHASE 2 READY - Azure Resource Setup**
With production-ready container validated and comprehensive documentation complete, proceed to Azure infrastructure creation.

## Technical Architecture

### Current Application Structure
```
discord_publish_bot/
├── api/          # FastAPI server for HTTP interactions
├── discord/      # Discord bot and interactions handling
├── publishing/   # GitHub publishing services
├── config/       # Unified configuration management
└── shared/       # Common utilities and types
```

### Deployment Architecture
```
Discord Platform
       ↓ (HTTP Interactions)
Azure Container Apps
       ↓ (Publishing API)
GitHub Repository
       ↓ (Content Creation)
Static Site Generator
```

## Phase 1: Container Configuration ✅ COMPLETE

### 🟢 GREEN Actions ✅ EXECUTED

#### 1.1 Optimize Dockerfile for Azure ✅ COMPLETE
**Status:** Production-ready Dockerfile with multi-stage build completed  
**Achievement:** 224MB optimized container (78% size reduction)

**Implementation Completed:**
```dockerfile
# Multi-stage build for production optimization ✅
FROM python:3.11-slim as builder
# Install uv and dependencies ✅
# Create optimized production image ✅

FROM python:3.11-slim as production  
# Copy only necessary files ✅
# Non-root user for security (UID/GID 1000) ✅
# Health check endpoint ✅
```

#### 1.2 Environment Configuration ✅ COMPLETE
**Files Created:**
- ✅ `.env.production.example` - Production environment template with comprehensive Azure configuration
- ✅ `.env.local.example` - Local development template matching settings.py requirements
- ✅ `docker-compose.yml` - Local testing with production-like setup and monitoring
- ✅ `.dockerignore` - Optimized build context

#### 1.3 Health Check Implementation ✅ COMPLETE
**Status:** Docker health checks and Azure probes working correctly  
**Validation:** Local container testing successful with health endpoint returning proper status

#### 1.4 Azure Secrets Management ✅ COMPLETE
**Enhancement:** PowerShell script with .env file integration
- ✅ Reads from `.env.production` automatically
- ✅ Intelligent secret prompting with masked values
- ✅ Complete secret coverage including API_KEY
- ✅ Comprehensive usage documentation

#### 1.5 2025 Docker Naming Best Practices ✅ COMPLETE
**Implementation:** PowerShell script with semantic versioning + Git SHA
- ✅ `docker-naming.ps1` script with Azure Container Registry patterns
- ✅ Semantic versioning integration
- ✅ Environment-aware tagging strategy
- ✅ Multi-tag strategy for deployment flexibility

## Phase 2: Azure Resource Setup (Day 1-2)

### 🟡 YELLOW Actions (Research-Enhanced Implementation)

#### 2.1 Azure Container Apps Environment
**Research Required:** Best practices for Container Apps environment configuration

**Resources to Create:**
```
Resource Group: rg-discord-publish-bot-prod
Container Apps Environment: cae-discord-bot-prod
Container App: example-container-app
Log Analytics Workspace: law-discord-bot-prod
```

#### 2.2 Container Configuration
**Specifications - OPTIMIZED FOR SCALE-TO-ZERO:**
- **CPU:** 0.25 cores (scalable to 1.0)
- **Memory:** 0.5GB (scalable to 2GB)  
- **Min Replicas:** 0 ✅ **SCALE-TO-ZERO ENABLED**
- **Max Replicas:** 2
- **Ingress:** HTTPS only, port 8000
- **Scale Rule:** HTTP (default) - scales automatically based on incoming requests
- **Cost Optimization:** Zero charges when idle (no Discord interactions)

#### 2.3 Environment Variables Configuration
**Critical Security:** Use Azure Container Apps secrets for sensitive data

**Required Variables:**
```bash
# Discord Configuration
DISCORD_BOT_TOKEN=***          # Azure secret
DISCORD_APPLICATION_ID=***     # Azure secret  
DISCORD_PUBLIC_KEY=***         # Azure secret
DISCORD_USER_ID=***           # Azure secret

# GitHub Configuration  
GITHUB_TOKEN=***              # Azure secret
GITHUB_REPO=***               # Azure secret

# API Security
API_KEY=***                   # Azure secret (32+ characters)

# Application Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

## Phase 3: CI/CD Pipeline (Day 2-3)

### 🟡 YELLOW Actions (Template-Based Implementation)

#### 3.1 GitHub Actions Workflow
**File:** `.github/workflows/deploy-azure.yml`

**Workflow Stages:**
1. **Test Stage:** Run full test suite (76 tests)
2. **Security Stage:** Validate no production credentials in code  
3. **Build Stage:** Create optimized Docker image
4. **Deploy Stage:** Deploy to Azure Container Apps
5. **Verification Stage:** Health check and integration tests

#### 3.2 Infrastructure as Code
**Technology:** Azure Bicep or ARM templates
**Purpose:** Reproducible infrastructure deployment

**Files to Create:**
- `infra/main.bicep` - Container Apps environment
- `infra/container-app.bicep` - Application configuration  
- `infra/parameters.prod.json` - Production parameters

#### 3.3 Secrets Management
**Azure Integration:**
- Azure Key Vault for sensitive configuration
- Container Apps secrets integration
- Managed identity for secure access

## Phase 4: Discord Integration Setup (Day 3)

### 🟢 GREEN Actions (Production Configuration)

#### 4.1 Discord Application Configuration
**Discord Developer Portal Setup:**
1. Update Interactions Endpoint URL to Azure Container Apps URL
2. Configure slash commands for production
3. Verify webhook signature validation
4. Test Discord interactions with production endpoint

#### 4.2 GitHub Webhook Configuration  
**Repository Setup:**
1. Verify GitHub token permissions for target repository
2. Configure webhook endpoints if needed
3. Test publishing workflows end-to-end

## Phase 5: Monitoring and Observability (Day 3-4)

### 🟡 YELLOW Actions (Best Practice Implementation)

#### 5.1 Application Monitoring
**Azure Application Insights Integration:**
- Custom telemetry for Discord interactions
- Publishing workflow metrics
- Error tracking and alerting
- Performance monitoring

#### 5.2 Log Management
**Log Analytics Workspace:**
- Centralized logging for all application components
- Structured logging with correlation IDs
- Log retention policies
- Alert rules for critical errors

#### 5.3 Health Monitoring
**Multi-Level Health Checks:**
- Azure Container Apps health probes
- Application-level health endpoints
- GitHub API connectivity validation
- Discord API connectivity validation

## Phase 6: Documentation and Runbooks (Day 4-5)

### 🟢 GREEN Actions (Documentation Standards)

#### 6.1 Deployment Documentation
**Files to Create:**
- `docs/team/deployment-runbook.md` - Step-by-step deployment guide
- `docs/team/troubleshooting-guide.md` - Common issues and solutions
- `docs/team/monitoring-guide.md` - How to monitor production

#### 6.2 User Documentation
**End-User Guides:**
- Discord command reference
- Publishing workflow documentation  
- Troubleshooting for end users

#### 6.3 Operational Procedures
**Production Operations:**
- Incident response procedures
- Rollback procedures
- Scaling guidelines
- Security incident response

## Risk Assessment and Mitigation

### High Risk Items
**Risk:** Azure Container Apps service limits or quotas  
**Impact:** Deployment failure or scaling issues  
**Mitigation:** Research quotas upfront, request increases if needed

**Risk:** Discord webhook signature validation in production  
**Impact:** Security vulnerability or interaction failures  
**Mitigation:** Comprehensive testing in staging environment

**Risk:** GitHub API rate limiting in production  
**Impact:** Publishing failures during high usage  
**Mitigation:** Implement exponential backoff and error handling

### Medium Risk Items  
**Risk:** Environment variable configuration errors  
**Impact:** Application startup failures  
**Mitigation:** Validation scripts and staged deployment

**Risk:** Log volume exceeding Azure Log Analytics limits  
**Impact:** Additional costs or data loss  
**Mitigation:** Log level configuration and retention policies

## Success Validation Checklist

### Technical Validation
- [ ] Docker image builds successfully in CI/CD
- [ ] Container starts and passes health checks
- [ ] All 76 tests pass in production environment
- [ ] Security validation: No production credentials exposed
- [ ] Discord interactions respond within 2 seconds
- [ ] GitHub publishing creates files successfully

### Operational Validation  
- [ ] Monitoring dashboards show green status
- [ ] Log aggregation working correctly
- [ ] Alert rules trigger appropriately  
- [ ] Rollback procedure tested and documented
- [ ] On-call procedures defined and tested

### User Validation
- [ ] Discord slash commands work in production
- [ ] Published content appears correctly on target site
- [ ] Error messages are user-friendly
- [ ] Documentation enables self-service troubleshooting

## Next Steps for Tomorrow

### Immediate Actions (30 minutes)
1. **Review Dockerfile** - Enhance for production use
2. **Create environment templates** - Production configuration examples
3. **Research Azure Container Apps** - Best practices and limitations

### Development Work (2-3 hours)
1. **Azure resource creation** - Container Apps environment setup
2. **CI/CD pipeline** - GitHub Actions workflow implementation  
3. **Security configuration** - Azure Key Vault integration

### Testing and Validation (1-2 hours)  
1. **End-to-end testing** - Full production workflow validation
2. **Security validation** - Credential handling verification
3. **Performance testing** - Response time and load validation

### Documentation (1 hour)
1. **Deployment runbook** - Step-by-step operational guide
2. **Troubleshooting guide** - Common issues and solutions
3. **User documentation** - End-user command reference

## Resource Links and References

### Azure Documentation
- [Azure Container Apps Overview](https://docs.microsoft.com/azure/container-apps/)
- [Container Apps Environment Variables](https://docs.microsoft.com/azure/container-apps/environment-variables)
- [Container Apps Secrets](https://docs.microsoft.com/azure/container-apps/manage-secrets)

### Discord Documentation  
- [Discord Interactions](https://discord.com/developers/docs/interactions/receiving-and-responding)
- [Discord Webhooks](https://discord.com/developers/docs/resources/webhook)

### Implementation Templates
- Use `templates/runbook-template.md` for operational documentation
- Use `templates/adr-template.md` for architectural decisions
- Follow existing security patterns from `tests/test_security_isolation.py`

---

## Autonomous Development Partner Notes

**Following Copilot Instructions:**
- ✅ **Research-First Approach**: Plan includes research phases for Azure best practices
- ✅ **Template Usage**: Leveraging existing documentation templates  
- ✅ **Security Focus**: Comprehensive credential management and validation
- ✅ **Continuous Testing**: Validation at every deployment phase
- ✅ **Documentation Standards**: Complete operational and user documentation

**Project State Management:**
- This file placed in `projects/active/` following directory discipline
- Will be archived to `projects/archive/` upon completion
- Changelog updates will document deployment success metrics

**Ready for Tomorrow:** All research, templates, and implementation steps clearly defined for immediate execution upon return.
