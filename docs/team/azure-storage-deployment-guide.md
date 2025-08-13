# Azure Storage Integration - Deployment Guide

## 🚀 Quick Start

Your Discord bot is now ready to store media permanently in Azure Blob Storage! Follow these steps to deploy the integration.

### Prerequisites ✅

- [x] Existing Azure Storage Account
- [x] Discord bot deployed on Azure Container Apps
- [x] Azure CLI installed and logged in

### Step 1: Configure Azure Storage

Run the setup script to configure your storage account for Discord integration:

```powershell
# Navigate to your project directory
cd c:\Dev\discord-publish-bot

# Run the Azure Storage setup script
.\scripts\setup-azure-storage.ps1
```

**The script will:**
- Create a `discord-media` container in your storage account
- Configure CORS for Discord integration
- Grant your Container App permissions to access storage
- Set up lifecycle management for cost optimization
- Display the environment variables you need

### Step 2: Update Environment Configuration

Add these variables to your `.env.production` file:

```bash
# Azure Storage Configuration
ENABLE_AZURE_STORAGE=true
AZURE_STORAGE_ACCOUNT_NAME=yourstorageaccount
AZURE_STORAGE_CONTAINER_NAME=discord-media
AZURE_STORAGE_SAS_EXPIRY_HOURS=8760
```

### Step 3: Deploy Secrets to Container Apps

Update your Container App with the new configuration:

```powershell
# Run the secrets setup script
.\scripts\azure-secrets-setup.ps1 -ResourceGroupName "your-bot-rg" -ContainerAppName "your-container-app"
```

### Step 4: Deploy Updated Code

Deploy your updated Discord bot:

```powershell
# Build and deploy (adjust for your deployment method)
az containerapp up --name your-container-app --resource-group your-bot-rg
```

## 🔧 Configuration Details

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ENABLE_AZURE_STORAGE` | Enable Azure Storage integration | `true` |
| `AZURE_STORAGE_ACCOUNT_NAME` | Your Azure Storage Account name | `mystorageaccount` |
| `AZURE_STORAGE_CONTAINER_NAME` | Container for Discord media | `discord-media` |
| `AZURE_STORAGE_SAS_EXPIRY_HOURS` | How long URLs stay valid | `8760` (1 year) |
| `AZURE_STORAGE_IMAGES_FOLDER` | Folder for image files | `images` |
| `AZURE_STORAGE_VIDEOS_FOLDER` | Folder for video files | `videos` |
| `AZURE_STORAGE_AUDIO_FOLDER` | Folder for audio files | `audio` |
| `AZURE_STORAGE_DOCUMENTS_FOLDER` | Folder for document files | `documents` |
| `AZURE_STORAGE_OTHER_FOLDER` | Folder for other file types | `other` |
| `AZURE_STORAGE_USE_SAS_TOKENS` | Use SAS tokens for secure access | `true` (recommended) |

### Azure Permissions Required

Your Container App's managed identity needs:
- **Storage Blob Data Contributor** role on the storage account
- Access to create containers and upload blobs

### Container Access Options

**🔐 Private Container + SAS Tokens (Recommended)**
- ✅ **Secure**: Time-limited authenticated access
- ✅ **Auditable**: Track access in Azure logs  
- ✅ **Revocable**: Can invalidate access by rotating keys
- ⚠️ Longer URLs with SAS tokens

```bash
AZURE_STORAGE_USE_SAS_TOKENS=true  # Default
# URL: https://account.blob.core.windows.net/container/images/file.jpg?sv=2021-06-08&ss=b...
```

**🌐 Public Container (Direct URLs)**
- ✅ **Simple**: Clean URLs without tokens
- ✅ **Fast**: No authentication overhead
- ⚠️ **Security Risk**: Anyone can access files with URL
- ⚠️ **Not recommended** for Discord media

```bash
AZURE_STORAGE_USE_SAS_TOKENS=false
# URL: https://account.blob.core.windows.net/container/images/file.jpg
```

**Configure container access:**
```powershell
# Set to private (recommended for Discord media)
.\scripts\configure-container-access.ps1 -StorageAccountName "youraccount" -ResourceGroupName "your-rg" -AccessLevel "private"

# Or set to public (less secure but simpler URLs)  
.\scripts\configure-container-access.ps1 -StorageAccountName "youraccount" -ResourceGroupName "your-rg" -AccessLevel "public"
```

### Cost Optimization

The setup includes lifecycle management rules:
- **30 days**: Move to Cool storage tier (lower cost)
- **365 days**: Move to Archive tier (lowest cost)

## 🧪 Testing

### Test the Integration

1. **Upload a file via Discord**: Use your bot command with an attachment
2. **Check the response**: Should show a permanent Azure URL instead of Discord CDN
3. **Verify storage**: Check Azure Portal for uploaded files in the container

### Example Test

```
/post_to_github "Test Azure Storage" 
[Attach an image file]
```

Expected behavior:
- Bot uploads file to Azure Storage
- Returns permanent URL like: `https://youraccount.blob.core.windows.net/discord-media/2025/01/filename.jpg`
- File remains accessible even after Discord's 24-hour expiry

## 🔍 Troubleshooting

### Common Issues

**Authentication Error**
```
Error: Failed to authenticate with Azure Storage
```
**Solution**: Check that your Container App has managed identity enabled and proper RBAC permissions.

**Container Not Found**
```
Error: The specified container does not exist
```
**Solution**: Run the setup script again to create the container.

**CORS Issues**
```
Error: CORS policy blocks access
```
**Solution**: Verify CORS configuration includes Discord domains.

### Debug Steps

1. **Check Container App logs**:
   ```powershell
   az containerapp logs show --name your-app --resource-group your-rg
   ```

2. **Verify managed identity**:
   ```powershell
   az containerapp identity show --name your-app --resource-group your-rg
   ```

3. **Test storage access**:
   ```powershell
   az storage blob list --container-name discord-media --account-name youraccount
   ```

## 📊 Monitoring

### Key Metrics to Monitor

- **Storage Requests**: Number of uploads per day
- **Storage Size**: Total data stored
- **Bandwidth**: Data transfer costs
- **Error Rate**: Failed uploads

### Azure Portal Monitoring

1. Navigate to your Storage Account
2. Go to **Monitoring** → **Metrics**
3. Add charts for:
   - Blob requests
   - Blob capacity
   - Egress traffic

## �️ Media Type Organization

Your Discord bot now automatically organizes uploaded media by type in separate folders:

### Folder Structure

```
discord-media/
├── images/          # Photos, screenshots, drawings
│   ├── 20250812_143052_photo.jpg
│   ├── 20250812_143055_screenshot.png
│   └── 20250812_143058_avatar.gif
├── videos/          # Video clips, recordings
│   ├── 20250812_143100_video.mp4
│   └── 20250812_143102_clip.avi
├── audio/           # Voice notes, music, sounds
│   ├── 20250812_143105_song.mp3
│   └── 20250812_143107_voice_note.wav
├── documents/       # PDFs, Office docs, text files
│   ├── 20250812_143110_document.pdf
│   └── 20250812_143112_report.docx
└── other/           # Unknown or miscellaneous files
    └── 20250812_143115_unknown.xyz
```

### File Type Detection

The bot automatically detects file types using:
1. **Content-Type headers** (primary method)
2. **File extensions** (fallback method)

**Supported File Types:**
- **Images**: jpg, jpeg, png, gif, bmp, webp, svg, ico, tiff
- **Videos**: mp4, avi, mov, wmv, flv, webm, mkv, m4v, 3gp, mpg
- **Audio**: mp3, wav, flac, aac, ogg, wma, m4a, opus
- **Documents**: pdf, doc, docx, xls, xlsx, ppt, pptx, txt, csv, rtf
- **Other**: Any unrecognized file types

## 🔄 URL Format

### Before (Ephemeral Discord URLs)
```
https://cdn.discordapp.com/attachments/123/456/image.jpg
# Expires in 24 hours
```

### After (Permanent Azure URLs)
```
https://youraccount.blob.core.windows.net/discord-media/images/20250812_143052_image.jpg?sas=token
# Valid for 1 year (configurable)
```

### URL Structure

```
https://{account}.blob.core.windows.net/{container}/{media-type}/{timestamp}_{filename}?{sas-token}
```

- **Media-type organization**: Files organized by type (images, videos, audio, documents, other)
- **Timestamp prefixes**: Prevent filename conflicts and enable chronological sorting
- **SAS tokens**: Secure access without exposing account keys
- **Clean structure**: Easy to browse and manage in Azure Portal

### Customize Folder Names

You can customize the folder names in your configuration:

```bash
# Default folder configuration
AZURE_STORAGE_IMAGES_FOLDER=images
AZURE_STORAGE_VIDEOS_FOLDER=videos
AZURE_STORAGE_AUDIO_FOLDER=audio
AZURE_STORAGE_DOCUMENTS_FOLDER=documents
AZURE_STORAGE_OTHER_FOLDER=other

# Custom folder names (examples)
AZURE_STORAGE_IMAGES_FOLDER=photos
AZURE_STORAGE_VIDEOS_FOLDER=clips
AZURE_STORAGE_AUDIO_FOLDER=sounds
AZURE_STORAGE_DOCUMENTS_FOLDER=files
AZURE_STORAGE_OTHER_FOLDER=misc
```

## 🛡️ Security Features

### Authentication
- **Managed Identity**: No secrets in code or environment
- **RBAC**: Granular permissions per service
- **SAS Tokens**: Time-limited access URLs

### Data Protection
- **Encryption at rest**: All data encrypted in Azure
- **HTTPS only**: All transfers use TLS
- **Private containers**: No public read access

### Access Control
- **Container App only**: Only your bot can upload
- **Time-limited URLs**: SAS tokens expire automatically
- **Audit logging**: All access logged in Azure

## 💰 Cost Optimization

### Storage Tiers
- **Hot**: First 30 days (frequent access)
- **Cool**: 30-365 days (reduced cost)
- **Archive**: 365+ days (lowest cost, slower access)

### Cost Estimates (example)
- **1GB/month**: ~$0.02/month (Hot tier)
- **10GB/month**: ~$0.20/month (Hot tier)
- **100GB/month**: ~$2.00/month (mixed tiers)

### Cost Controls
- Lifecycle policies automatically move old data
- Monitor usage in Azure Cost Management
- Set budget alerts for unexpected growth

## 🚀 Next Steps

### Optional Enhancements

1. **CDN Integration**: Add Azure CDN for faster global access
2. **Image Processing**: Resize images automatically
3. **Backup Strategy**: Cross-region replication
4. **Monitoring Alerts**: Set up automated monitoring

### Production Checklist

- [ ] Storage account configured
- [ ] Container App permissions granted
- [ ] Environment variables set
- [ ] Code deployed
- [ ] Test upload successful
- [ ] Monitoring configured
- [ ] Cost alerts set

## 📚 Additional Resources

- [Azure Blob Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Container Apps Managed Identity](https://docs.microsoft.com/en-us/azure/container-apps/managed-identity)
- [Azure Storage Security Guide](https://docs.microsoft.com/en-us/azure/storage/common/storage-security-guide)

---

**🎉 Congratulations!** Your Discord bot now stores media permanently in Azure Blob Storage, giving you reliable, cost-effective, and secure media hosting that scales with your needs.
