# Media Upload Migration Guide
## From Discord Bot to GitHub Issue Forms

This guide explains how to migrate the media upload workflow from `discord-publish-bot` to `luisquintanilla.me` using GitHub Issue Forms.

---

## Overview

### Current State (Discord Bot)
```
Discord /post media [attachment]
  → Discord CDN
  → Bot downloads
  → Upload to Linode S3
  → Create GitHub PR
  → Merge & Publish
```

### Target State (GitHub Issues)
```
GitHub Issue Form + Drag/Drop Files
  → GitHub auto-uploads to temporary storage
  → Action downloads
  → Upload to Linode S3
  → Create GitHub PR
  → Merge & Publish
```

**Key Insight**: GitHub issue forms with textarea fields **already support file uploads** via drag-and-drop. GitHub automatically inserts markdown like `![filename](https://github.com/user-attachments/...)`. We just need to:

1. ✅ Parse this markdown
2. ✅ Download from GitHub CDN
3. ✅ Upload to permanent storage
4. ✅ Transform to `:::media` blocks

---

## User Experience

### Creating a Media Post

1. **Go to Issues → New Issue → Media Post**

2. **Fill in the form:**
   - Title: "Sunset at the Beach"
   - Content: (drag and drop a photo here)
   - Tags: "photography, travel"

3. **When you drag a file into the Content field:**
   ```markdown
   Here's my photo:

   ![sunset.jpg](https://github.com/user-attachments/assets/abc123...)

   Taken yesterday evening!
   ```

4. **Submit the issue**

5. **GitHub Actions automatically:**
   - Downloads `sunset.jpg` from GitHub's CDN
   - Uploads to `https://cdn.luisquintanilla.me/files/images/2025/10/26/sunset.jpg`
   - Transforms markdown to:
   ```markdown
   Here's my photo:

   :::media
   - url: "https://cdn.luisquintanilla.me/files/images/2025/10/26/sunset.jpg"
     alt: "sunset.jpg"
     mediaType: "image"
     aspectRatio: "landscape"
     caption: "Sunset at the Beach"
   :::media

   Taken yesterday evening!
   ```
   - Creates a PR with this content
   - Comments on the issue with the PR link

6. **Review and merge the PR → Published!**

---

## Implementation Steps

### Phase 1: Prerequisites

#### 1.1 Linode Object Storage Setup

**If you don't have a bucket yet:**
1. Log into Linode Cloud Manager
2. Navigate to Object Storage
3. Create a bucket (e.g., `luisquintanilla-media`)
4. Create Access Keys
5. Note down:
   - Access Key ID
   - Secret Access Key
   - Endpoint URL (e.g., `https://us-east-1.linodeobjects.com`)

**If you're already using the discord-publish-bot setup:**
- ✅ Use the same bucket and credentials
- ✅ Same file organization structure
- ✅ No additional configuration needed

#### 1.2 Custom CDN Domain (Optional but Recommended)

Set up a custom domain for cleaner URLs:

1. **Add DNS CNAME record:**
   ```
   cdn.luisquintanilla.me → luisquintanilla-media.us-east-1.linodeobjects.com
   ```

2. **Benefits:**
   - `https://cdn.luisquintanilla.me/files/images/...` instead of long Linode URLs
   - Easier to migrate storage providers later
   - Professional appearance

#### 1.3 GitHub Secrets Configuration

In `luisquintanilla.me` repository settings → Secrets and variables → Actions:

Add these secrets:
```
LINODE_STORAGE_ACCESS_KEY_ID: [your-access-key-id]
LINODE_STORAGE_SECRET_ACCESS_KEY: [your-secret-key]
LINODE_STORAGE_ENDPOINT_URL: https://us-east-1.linodeobjects.com
LINODE_STORAGE_BUCKET_NAME: [your-bucket-name]
LINODE_STORAGE_CUSTOM_DOMAIN: https://cdn.luisquintanilla.me (optional)
```

---

### Phase 2: Code Migration

#### 2.1 Copy Files to `luisquintanilla.me`

Create these files in your repository:

```
luisquintanilla.me/
├── .github/
│   ├── workflows/
│   │   └── process-media-issue.yml          # ← From MIGRATION_WORKFLOW.yml
│   ├── scripts/
│   │   └── upload_media.py                  # ← From MIGRATION_SCRIPT.py
│   └── ISSUE_TEMPLATE/
│       └── media.yml                        # ← From EXAMPLE_ISSUE_FORM.yml
```

**Files provided in this migration package:**
- `MIGRATION_SCRIPT.py` → Copy to `.github/scripts/upload_media.py`
- `MIGRATION_WORKFLOW.yml` → Copy to `.github/workflows/process-media-issue.yml`
- `EXAMPLE_ISSUE_FORM.yml` → Copy to `.github/ISSUE_TEMPLATE/media.yml` (or update existing)

#### 2.2 Install Python Dependencies in Workflow

The workflow already includes:
```yaml
- name: Install dependencies
  run: |
    pip install boto3 requests
```

No additional setup needed - GitHub Actions runners have Python pre-installed.

---

### Phase 3: Testing

#### 3.1 Test Checklist

**Test 1: Single Image**
- [ ] Create issue with 1 image via drag-and-drop
- [ ] Verify Action triggers
- [ ] Check file uploaded to S3 at `/files/images/YYYY/MM/DD/`
- [ ] Verify PR created with `:::media` block
- [ ] Confirm permanent CDN URL works

**Test 2: Multiple Files**
- [ ] Drag 3 images into one issue
- [ ] Verify all 3 processed
- [ ] Check 3 separate `:::media` blocks in PR

**Test 3: Video/Audio**
- [ ] Upload an MP4 video
- [ ] Verify categorized to `/files/videos/`
- [ ] Check `mediaType: "video"` in block

**Test 4: Mixed Content**
- [ ] Content with text + image + more text
- [ ] Verify markdown structure preserved
- [ ] Image converted to media block in correct position

**Test 5: Filename Edge Cases**
- [ ] Upload file with spaces: `My Photo 2024.jpg`
- [ ] Upload special chars: `test@#$%.png`
- [ ] Verify sanitized: `My_Photo_2024.jpg`, `test____.png`

**Test 6: Error Handling**
- [ ] Invalid credentials → Check error comment on issue
- [ ] Network timeout → Verify retry/fallback
- [ ] No attachments → Graceful skip

#### 3.2 Manual Test Procedure

1. **Create a test issue**:
   ```
   Title: [TEST] Media Upload Test
   Content:
   Testing the new media workflow!

   [Drag a small test image here]

   This should be converted automatically.
   ```

2. **Monitor the workflow**:
   - Go to Actions tab
   - Watch "Process Media Issue" workflow run
   - Check logs for each step

3. **Verify PR created**:
   - Check that PR exists
   - Review the generated markdown file
   - Verify CDN URL is accessible

4. **Merge and verify**:
   - Merge the PR
   - Build the site (F# generator)
   - Check that media displays correctly

---

### Phase 4: Go Live

#### 4.1 Documentation Updates

Update your repository README with:

```markdown
## Publishing Media via GitHub Issues

1. Go to [Issues → New Issue → Media Post](https://github.com/lqdev/luisquintanilla.me/issues/new?template=media.yml)
2. Fill in title and tags
3. **Drag and drop** your media files (images, videos, audio) directly into the Content field
4. Submit the issue
5. GitHub Actions will:
   - Upload files to permanent CDN storage
   - Create a PR with formatted markdown
   - Comment on the issue with the PR link
6. Review and merge the PR to publish!

**Supported formats**: JPG, PNG, GIF, WebP, MP4, MOV, WebM, MP3, WAV, FLAC, AAC, OGG

**Tips**:
- Multiple files: Drag several at once - all will be processed
- Alt text: Edit the `![alt text]` in the markdown for accessibility
- Videos: Work exactly like images - just drag and drop!
```

#### 4.2 Deprecation Plan (Optional)

If you want to phase out the Discord bot:

**Option A: Keep Both**
- Discord bot for quick mobile posts
- GitHub issues for desktop workflow with richer metadata

**Option B: Migrate Fully**
- Add deprecation notice to Discord bot
- Guide users to GitHub issues
- Keep bot running for 30 days
- Archive after migration complete

#### 4.3 Announcement

Sample announcement text:

```markdown
🎉 New Feature: Media Publishing via GitHub Issues!

You can now publish photos, videos, and audio directly through GitHub issue forms!

**Why?**
- ✅ No Discord app required
- ✅ Better for desktop workflows
- ✅ Built-in version control
- ✅ Rich metadata support
- ✅ Same permanent CDN storage

**Try it now**: [Create a Media Post](https://github.com/lqdev/luisquintanilla.me/issues/new?template=media.yml)

The Discord bot will continue to work as before - use whichever workflow you prefer!
```

---

## Architecture Deep Dive

### File Organization

Both systems use identical storage structure:

```
cdn.luisquintanilla.me/
└── files/
    ├── images/
    │   └── 2025/
    │       └── 10/
    │           └── 26/
    │               ├── sunset.jpg
    │               └── photo-2024.png
    ├── videos/
    │   └── 2025/10/26/
    │       └── clip.mp4
    └── audio/
        └── 2025/10/26/
            └── podcast.mp3
```

### Code Reuse from Discord Bot

| Component | Reuse Level | Notes |
|-----------|-------------|-------|
| `_sanitize_filename()` | 100% | Identical logic copied |
| `_get_media_type_folder()` | 100% | Identical categorization |
| `_detect_media_type()` | 100% | Same media type detection |
| S3 upload logic | 95% | Changed from Discord URL to GitHub URL source |
| Media block generation | 90% | Same template, different trigger |

**Total code reuse**: ~350 lines from `linode_storage.py` + 200 lines from `publishing/service.py`

### Workflow Comparison

#### Discord Bot Flow
```python
# discord/interactions.py
@app.post("/discord/interactions")
async def handle_interaction(request):
    # 1. Verify signature
    # 2. Extract attachment from Discord's resolved data
    # 3. Show modal with pre-filled URL
    # 4. On modal submit:
    background_tasks.add_task(process_post)
    return deferred_response()

# publishing/service.py
async def process_post():
    if is_discord_url(media_url):
        permanent_url = await storage.upload_discord_attachment(...)
        media_url = permanent_url

    markdown = generate_markdown_with_media_blocks(...)
    await github.create_pr(...)
```

#### GitHub Actions Flow
```yaml
# .github/workflows/process-media-issue.yml
on:
  issues:
    types: [opened]

jobs:
  process:
    steps:
      - Parse issue body for markdown images
      - Extract GitHub attachment URLs
      - python upload_media.py  # ← Same logic as Discord bot!
      - Create PR with transformed content
```

```python
# .github/scripts/upload_media.py
def main():
    attachments = parse_markdown_for_attachments(issue_body)

    for attachment in attachments:
        if is_github_url(attachment.url):
            permanent_url = upload_from_github(...)  # ← Same S3 upload!
            attachment.permanent_url = permanent_url

    markdown = transform_to_media_blocks(...)  # ← Same template!
    generate_markdown_file(...)
```

**Key Insight**: The _core upload and transformation logic is identical_ - only the trigger mechanism changes!

---

## Troubleshooting

### Common Issues

#### Issue: Action fails with "403 Forbidden" on S3 upload
**Solution**: Check that GitHub Secrets are correctly set:
```bash
# Verify secrets exist in repo settings
LINODE_STORAGE_ACCESS_KEY_ID
LINODE_STORAGE_SECRET_ACCESS_KEY
```

#### Issue: No PR created after issue submitted
**Solution**: Check workflow file location:
```bash
# Must be exactly:
.github/workflows/process-media-issue.yml

# Not:
.github/workflow/... (missing 's')
github/workflows/... (missing '.')
```

#### Issue: Media files not found in issue body
**Solution**: Ensure files are drag-and-dropped into the **textarea field**, not just attached to the issue. GitHub only converts dragged files to markdown.

#### Issue: S3 URLs return 404
**Solution**:
1. Check bucket permissions (must be public-read)
2. Verify endpoint URL format: `https://us-east-1.linodeobjects.com` (no trailing slash)
3. Check custom domain DNS propagation (can take 24-48 hours)

#### Issue: Filename collisions
**Solution**: The script includes timestamp in path (`YYYY/MM/DD/filename`), which minimizes collisions. For additional safety, could add:
```python
# In _sanitize_filename():
import uuid
if collision_detected:
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
```

#### Issue: F# build doesn't recognize :::media blocks
**Solution**: Verify Markdig extension is configured. Check your existing media posts to ensure format matches:
```fsharp
// In your F# generator code, ensure media block parsing is enabled
// Should already exist since luisquintanilla.me mentions :::media support
```

---

## Performance & Costs

### Expected Performance

| Metric | Estimate |
|--------|----------|
| Action execution time | 30-60 seconds per issue |
| File upload speed | ~2 MB/s (GitHub → S3) |
| Concurrent issues | Unlimited (queued by GitHub) |
| API rate limits | None (using repo token) |

### Cost Estimate (Linode Object Storage)

**Linode Pricing** (as of 2024):
- Storage: $0.02/GB/month
- Transfer: $0.005/GB (outbound)
- First 1TB transfer free

**Example monthly cost**:
- 100 images @ 2MB each = 200MB storage = **$0.004/month**
- 10,000 pageviews @ 2MB each = 20GB transfer = **$0.10/month** (or free if under 1TB)
- **Total: ~$0.10/month or less**

**Compared to Discord Bot**: Identical - same storage backend!

---

## Advanced Customization

### Adding Video Thumbnails

Extend the script to generate video thumbnails:

```python
# In upload_media.py, add after S3 upload:
if media_type == 'video':
    thumbnail_url = generate_thumbnail(permanent_url)

    media_block = f''':::media
- url: "{permanent_url}"
  thumbnail: "{thumbnail_url}"
  mediaType: "video"
:::media'''
```

### Batch Processing

For migrating old Discord bot content:

```python
# migration_batch.py
from github import Github

g = Github(os.environ['GITHUB_TOKEN'])
repo = g.get_repo('lqdev/luisquintanilla.me')

# Find all content with Discord CDN URLs
for file in repo.get_contents('_src/media'):
    content = file.decoded_content.decode()
    if 'cdn.discordapp.com' in content:
        # Re-upload to Linode and update
        process_file(file)
```

### Multi-Language Support

Add language detection:

```yaml
# In issue form:
- type: dropdown
  id: language
  attributes:
    label: "Language"
    options:
      - English
      - Español
      - Français
```

```python
# In script:
frontmatter = f"""---
title: "{title}"
lang: "{language}"
---"""
```

---

## Success Metrics

Track these metrics to measure success:

- [ ] **Migration Time**: Total hours from start to production
- [ ] **Issues Processed**: Count of successful media issues
- [ ] **Error Rate**: Failed uploads / total attempts
- [ ] **User Adoption**: Issues created vs Discord bot usage
- [ ] **Performance**: Average processing time per issue
- [ ] **Storage Costs**: Monthly Linode bill

**Target Goals**:
- Migration time: < 1 day
- Error rate: < 5%
- Processing time: < 60 seconds
- Cost increase: $0 (same backend)

---

## Next Steps

### Immediate (Day 1)
1. ✅ Review this guide
2. ✅ Set up Linode bucket (or verify existing)
3. ✅ Configure GitHub Secrets
4. ✅ Copy migration files to repository

### Testing (Day 2)
1. ✅ Create test issue with sample image
2. ✅ Monitor workflow execution
3. ✅ Verify PR creation and content
4. ✅ Test merge and site build

### Production (Day 3)
1. ✅ Update documentation
2. ✅ Announce new feature
3. ✅ Create first real media post
4. ✅ Monitor for issues

### Optional Enhancements (Week 2+)
- [ ] Add video thumbnail generation
- [ ] Implement batch migration of Discord content
- [ ] Create analytics dashboard
- [ ] Add image optimization/compression
- [ ] Support for image galleries (multiple images → single post)

---

## Support & Feedback

If you encounter issues during migration:

1. **Check workflow logs**: GitHub Actions tab → Select failed run → View logs
2. **Verify secrets**: Settings → Secrets → Actions
3. **Test S3 manually**: Use AWS CLI or S3 browser to verify credentials
4. **Review issue body**: Ensure markdown images are properly formatted

**Common Success Indicators**:
- ✅ Workflow completes in < 60 seconds
- ✅ PR created with correct filename in `_src/media/`
- ✅ CDN URL loads in browser
- ✅ Issue auto-commented with PR link

---

## Appendix: Code Reference

### Key Files from Discord Bot (Reference Only)

These files were adapted for the migration:

1. **Storage Logic**: `src/discord_publish_bot/storage/linode_storage.py`
   - Lines 234-249: `_sanitize_filename()`
   - Lines 176-232: `_get_media_type_folder()`
   - Lines 94-174: `upload_discord_attachment()`

2. **Publishing Service**: `src/discord_publish_bot/publishing/service.py`
   - Lines 303-366: `_process_media_uploads()`
   - Lines 551-560: `_generate_media_block()`
   - Lines 368-370: `_is_discord_url()`

3. **Configuration**: `src/discord_publish_bot/config/settings.py`
   - Lines 176-221: `LinodeStorageSettings` class

### Migration Files (Use These)

1. **Upload Script**: `MIGRATION_SCRIPT.py`
   - Main processor for GitHub issues
   - Handles download, upload, transformation
   - Direct adaptation of Discord bot logic

2. **Workflow**: `MIGRATION_WORKFLOW.yml`
   - GitHub Actions configuration
   - Triggers on issue creation
   - Creates PRs automatically

3. **Issue Form**: `EXAMPLE_ISSUE_FORM.yml`
   - User-facing form template
   - Drag-and-drop support
   - Helpful instructions

---

## License & Credits

This migration preserves the architecture and logic from `discord-publish-bot`, adapted for GitHub Actions trigger instead of Discord webhooks.

**Original Discord Bot**: https://github.com/lqdev/discord-publish-bot
**Target Site**: https://github.com/lqdev/luisquintanilla.me

**Core principles maintained**:
- ✅ Same storage backend (Linode S3)
- ✅ Same file organization structure
- ✅ Same markdown output format
- ✅ Same validation and sanitization
- ✅ Same error handling patterns

**Key innovation**: Replacing Discord's 3-second webhook timeout constraint with GitHub Actions' more flexible execution environment.
