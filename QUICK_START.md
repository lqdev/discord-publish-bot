# Quick Start: Media Upload Migration

**Goal**: Enable media uploads via GitHub issue forms on `luisquintanilla.me`

---

## 30-Second Overview

```
User drags image into GitHub issue
  ↓
GitHub auto-converts to markdown: ![file](github-url)
  ↓
Action downloads → uploads to Linode S3
  ↓
Transforms to :::media block with permanent CDN URL
  ↓
Creates PR → User merges → Published!
```

---

## Setup Checklist (15 minutes)

### Step 1: Storage (5 min)
- [ ] Have Linode Object Storage bucket (or create one)
- [ ] Get Access Key ID + Secret Key
- [ ] (Optional) Set up custom domain: `cdn.luisquintanilla.me`

### Step 2: GitHub Secrets (2 min)
Add to `luisquintanilla.me` repo settings:
```
LINODE_STORAGE_ACCESS_KEY_ID
LINODE_STORAGE_SECRET_ACCESS_KEY
LINODE_STORAGE_ENDPOINT_URL
LINODE_STORAGE_BUCKET_NAME
LINODE_STORAGE_CUSTOM_DOMAIN (optional)
```

### Step 3: Copy Files (5 min)
```bash
# In luisquintanilla.me repo:
mkdir -p .github/scripts

# Copy these files from migration package:
cp MIGRATION_SCRIPT.py      → .github/scripts/upload_media.py
cp MIGRATION_WORKFLOW.yml   → .github/workflows/process-media-issue.yml
cp EXAMPLE_ISSUE_FORM.yml   → .github/ISSUE_TEMPLATE/media.yml
```

### Step 4: Test (3 min)
- [ ] Create test issue with small image
- [ ] Watch Actions tab for workflow
- [ ] Verify PR created
- [ ] Check CDN URL loads

### Done! 🎉

---

## File Locations

```
luisquintanilla.me/
├── .github/
│   ├── workflows/
│   │   └── process-media-issue.yml     # Triggers on issue creation
│   ├── scripts/
│   │   └── upload_media.py             # Main processing script
│   └── ISSUE_TEMPLATE/
│       └── media.yml                   # User-facing form
└── _src/
    └── media/                          # Generated markdown files
        └── YYYY-MM-DD-slug.md
```

---

## How It Works

### User Experience
1. Go to: Issues → New Issue → Media Post
2. Drag image into Content field
3. Submit issue
4. Receive comment with PR link in ~30 seconds
5. Merge PR → Live!

### Under the Hood
```python
# upload_media.py (simplified)

# 1. Parse markdown
attachments = parse_markdown_for_attachments(issue_body)
# Finds: ![sunset.jpg](https://github.com/user-attachments/...)

# 2. Upload to S3 (code from discord-publish-bot)
permanent_url = uploader.upload_from_github(github_url, filename)
# Returns: https://cdn.luisquintanilla.me/files/images/2025/10/26/sunset.jpg

# 3. Transform markdown
:::media
- url: "https://cdn.luisquintanilla.me/files/images/2025/10/26/sunset.jpg"
  alt: "sunset.jpg"
  mediaType: "image"
:::media

# 4. Create PR (done by workflow)
```

---

## Code Reuse from Discord Bot

| Function | Source File | Reuse % |
|----------|-------------|---------|
| `_sanitize_filename()` | `linode_storage.py:234` | 100% |
| `_get_media_type_folder()` | `linode_storage.py:176` | 100% |
| `_detect_media_type()` | `publishing/service.py:551` | 100% |
| S3 upload logic | `linode_storage.py:94` | 95% |

**Total**: ~550 lines of proven production code reused

---

## Troubleshooting

### Workflow doesn't trigger
- Check file is at `.github/workflows/process-media-issue.yml` (note: workflowS with 's')
- Verify issue has `media` label

### 403 error during S3 upload
- Verify GitHub Secrets are set correctly
- Test credentials with AWS CLI: `aws s3 ls --endpoint-url https://... s3://bucket-name/`

### No attachments found
- Ensure files are dragged into **textarea**, not attached to issue
- Check issue body contains `![filename](https://github.com/...)`

### CDN URL returns 404
- Verify bucket ACL is public-read
- Check custom domain DNS (can take 24-48hrs)
- Test direct Linode URL first before custom domain

---

## Testing Commands

```bash
# Test S3 credentials locally
export LINODE_ACCESS_KEY=your-key
export LINODE_SECRET_KEY=your-secret
export LINODE_ENDPOINT=https://us-east-1.linodeobjects.com
export LINODE_BUCKET=your-bucket

python .github/scripts/upload_media.py --issue-json test_issue.json

# Test S3 upload manually
aws s3 cp test.jpg \
  s3://your-bucket/files/images/2025/10/26/test.jpg \
  --endpoint-url https://us-east-1.linodeobjects.com \
  --acl public-read

# Verify uploaded file
curl https://cdn.luisquintanilla.me/files/images/2025/10/26/test.jpg
```

---

## Example Issue Body (What User Sees)

```markdown
Title: [Media] Beautiful Sunset

Content:
Had an amazing evening at the beach today!

![sunset-beach.jpg](https://github.com/user-attachments/assets/abc123...)

The colors were incredible. Can't wait to go back!

Tags: photography, travel, beach
```

## Generated Markdown (What Gets Created)

```markdown
---
title: "Beautiful Sunset"
date: 2025-10-26T14:30:00Z
tags: ["photography", "travel", "beach"]
---

Had an amazing evening at the beach today!

:::media
- url: "https://cdn.luisquintanilla.me/files/images/2025/10/26/sunset-beach.jpg"
  alt: "sunset-beach.jpg"
  mediaType: "image"
  aspectRatio: "landscape"
  caption: "Beautiful Sunset"
:::media

The colors were incredible. Can't wait to go back!
```

---

## Comparison: Discord vs GitHub

| Feature | Discord Bot | GitHub Issues |
|---------|-------------|---------------|
| **Trigger** | `/post media [attachment]` | Drag-and-drop in issue |
| **Mobile** | ✅ Excellent | ⚠️ OK (via browser) |
| **Desktop** | ⚠️ Need Discord app | ✅ Native browser |
| **Storage** | Linode S3 | Linode S3 (same!) |
| **Output** | `:::media` blocks | `:::media` blocks (same!) |
| **Speed** | ~30 seconds | ~30 seconds |
| **Metadata** | Modal form | Issue form (more flexible) |
| **Version Control** | PR only | Issue + PR (better tracking) |

**Recommendation**: Keep both! Use Discord for quick mobile posts, GitHub for desktop workflow.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    GITHUB ISSUES FLOW                   │
└─────────────────────────────────────────────────────────┘

  USER ACTION
  ┌────────────────────────────┐
  │ Create Issue + Drag Image  │
  └────────────────────────────┘
            ↓
  ┌────────────────────────────┐
  │ GitHub Auto-Upload         │
  │ → Markdown inserted        │
  │   ![file](github-url)      │
  └────────────────────────────┘
            ↓
  ┌────────────────────────────┐
  │ Workflow Triggered         │
  │ - Parse markdown           │
  │ - Extract GitHub URLs      │
  └────────────────────────────┘
            ↓
  ┌────────────────────────────┐
  │ Python Script              │
  │ - Download from GitHub     │
  │ - Upload to Linode S3      │
  │ - Generate :::media block  │
  └────────────────────────────┘
            ↓
  ┌────────────────────────────┐
  │ Create PR                  │
  │ - New markdown file        │
  │ - Comment on issue         │
  └────────────────────────────┘
            ↓
  ┌────────────────────────────┐
  │ User Merges PR             │
  │ → F# Build → Publish       │
  └────────────────────────────┘
```

---

## Next Actions

### Right Now
1. Review `MIGRATION_GUIDE.md` for full details
2. Set up GitHub Secrets
3. Copy files to repository
4. Create test issue

### Tomorrow
1. Run through test checklist
2. Fix any issues
3. Document for yourself

### This Week
1. Create first real media post
2. Update README
3. Announce to users (if applicable)

### Optional Later
- Batch migrate old Discord content
- Add video thumbnail generation
- Implement image optimization
- Create analytics dashboard

---

## Success Criteria

✅ **You're done when:**
- Issue created → PR appears in ~30 seconds
- CDN URL loads the image
- Merge PR → Site builds successfully
- Media displays correctly on published site
- No errors in Actions logs

---

## Support

**Full Documentation**: See `MIGRATION_GUIDE.md`

**Key Files**:
- `MIGRATION_SCRIPT.py` - Main Python processor
- `MIGRATION_WORKFLOW.yml` - GitHub Actions config
- `EXAMPLE_ISSUE_FORM.yml` - User form template

**Discord Bot Reference**:
- Storage logic: `src/discord_publish_bot/storage/linode_storage.py`
- Publishing: `src/discord_publish_bot/publishing/service.py`

**Questions?** Review the full guide or check workflow logs in Actions tab.

---

**Total Migration Time**: ~15-30 minutes
**Difficulty**: Easy (mostly configuration, proven code)
**Risk**: Low (same storage backend as Discord bot)

🚀 **Ready to start? Follow the Setup Checklist above!**
