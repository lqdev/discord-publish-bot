# 🚀 Quick Deployment Reference

## Essential Commands for Future Deployments

### 1. Deploy Code Changes
```bash
# Deploy new code
az containerapp up --name <your-container-app> --resource-group <your-resource-group> --source . --env-vars ENVIRONMENT=production

# ⚠️ CRITICAL: Always run after 'az containerapp up'
az containerapp update \
  --name <your-container-app> \
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

### 2. Check Deployment Status
```bash
# Check revision status
az containerapp revision list --name <your-container-app> --resource-group <your-resource-group> --query "[].{Name:name,Active:properties.active,TrafficWeight:properties.trafficWeight,RunningState:properties.runningState}" --output table

# Test health
curl https://<your-container-app>.<region>.azurecontainerapps.io/health
```

### 3. Update Secrets (if needed)
```bash
./scripts/azure-secrets-setup.ps1 -ResourceGroupName <your-resource-group> -ContainerAppName <your-container-app>
```

## 🔧 Key Lessons Learned

1. **Always Configure Environment Variables**: `az containerapp up` resets env vars
2. **Secrets Stay, Variables Don't**: Secrets persist but env var mappings get reset  
3. **Test After Each Deployment**: Use health check to verify deployment success
4. **Check Revision Status**: Failed revisions won't get traffic automatically

## 📋 Success Checklist

- [ ] Code deployed successfully
- [ ] Environment variables configured with secret references  
- [ ] Health check returns "healthy" status
- [ ] New revision shows "Running" state
- [ ] Discord interactions work end-to-end
- [ ] GitHub PR workflow functions correctly

## 🔗 Related Documentation

- Full deployment process: `docs/team/azure-deployment-runbook.md`
- Discord setup: `projects/active/discord-integration-setup.md`
- Security guidelines: `docs/team/security-guidelines.md`
