# Example: Mixed Content Transformation

This shows exactly how your issue content gets transformed into the final markdown file.

---

## What You Type in GitHub Issue

**Issue Title:** `[Media] Lossless audio coming to Spotify`

**Content field:**
```markdown
I guess people complained enough they're finally adding it

![screenshot.png](https://github.com/user-attachments/assets/abc123...)
```

**Tags field:** `music, spotify`

---

## What Gets Generated

**File:** `_src/media/lossless-audio-coming-to-spotify.md`

```markdown
---
title: Lossless audio coming to Spotify
post_type: media
published_date: "2025-10-26 14:30 -05:00"
tags: ["music", "spotify"]
---

I guess people complained enough they're finally adding it

:::media
- url: "https://cdn.luisquintanilla.me/files/images/2025/10/26/screenshot.png"
  alt: "screenshot.png"
  mediaType: "image"
  aspectRatio: "landscape"
  caption: "Lossless audio coming to Spotify"
:::media
```

---

## Key Transformations

| Input | Output |
|-------|--------|
| Issue title `[Media] ...` | Frontmatter `title: ...` (prefix removed) |
| Current datetime | `published_date: "YYYY-MM-DD HH:MM TZ"` |
| Tags field `music, spotify` | `tags: ["music", "spotify"]` |
| Markdown content | Preserved exactly as-is |
| `![alt](github-url)` | `:::media` block with permanent CDN URL |

---

## Example: Multiple Files with Commentary

**Issue Content:**
```markdown
Had an amazing day at the beach! Here are some highlights:

![sunset.jpg](https://github.com/user-attachments/assets/xyz789...)

The colors were incredible. Also recorded this moment:

![waves.mp4](https://github.com/user-attachments/assets/def456...)

Can't wait to go back!
```

**Generated Output:**
```markdown
---
title: Beach Day Highlights
post_type: media
published_date: "2025-10-26 15:45 -05:00"
tags: ["photography", "travel"]
---

Had an amazing day at the beach! Here are some highlights:

:::media
- url: "https://cdn.luisquintanilla.me/files/images/2025/10/26/sunset.jpg"
  alt: "sunset.jpg"
  mediaType: "image"
  aspectRatio: "landscape"
  caption: "Beach Day Highlights"
:::media

The colors were incredible. Also recorded this moment:

:::media
- url: "https://cdn.luisquintanilla.me/files/videos/2025/10/26/waves.mp4"
  alt: "waves.mp4"
  mediaType: "video"
  aspectRatio: "landscape"
  caption: "Beach Day Highlights"
:::media

Can't wait to go back!
```

---

## Example: Text-Only (No Media)

**Issue Content:**
```markdown
Interesting article about the future of web development.

Some key takeaways:
- Performance is critical
- Static sites are making a comeback
- IndieWeb principles matter
```

**Generated Output:**
```markdown
---
title: Future of Web Development
post_type: media
published_date: "2025-10-26 16:00 -05:00"
tags: ["webdev", "indieweb"]
---

Interesting article about the future of web development.

Some key takeaways:
- Performance is critical
- Static sites are making a comeback
- IndieWeb principles matter
```

*Note: No `:::media` blocks added since no files were uploaded.*

---

## Storage Organization

Files are automatically organized by type and date:

```
cdn.luisquintanilla.me/
└── files/
    ├── images/
    │   └── 2025/10/26/
    │       ├── sunset.jpg
    │       └── screenshot.png
    ├── videos/
    │   └── 2025/10/26/
    │       └── waves.mp4
    └── audio/
        └── 2025/10/26/
            └── podcast-clip.mp3
```

---

## Markdown Features Supported

All standard markdown works in the content field:

```markdown
# Heading 1
## Heading 2

**Bold text** and *italic text*

- Bullet lists
- Work great

1. Numbered lists
2. Also supported

[Links work](https://example.com)

> Blockquotes too

`Inline code` and code blocks:

```python
print("Hello, world!")
```

And of course, drag-and-drop media:

![your-file.jpg](github-url) ← Gets converted to :::media block
```

---

## What Gets Preserved vs Transformed

### ✅ Preserved Exactly
- All text content
- Markdown formatting (headings, lists, bold, italic)
- Links to external URLs
- Code blocks
- Blockquotes
- Order and structure of content

### 🔄 Transformed
- `![alt](https://github.com/user-attachments/...)` → `:::media` block
- GitHub temporary URL → Permanent CDN URL
- File categorized into appropriate folder (images/, videos/, audio/)

### ➕ Added
- YAML frontmatter with metadata
- `post_type: media` field
- Timestamp in correct format
- Structured tags array

---

## Real-World Example

Based on your existing file: [lossless-audio-coming-spotify.md](https://github.com/lqdev/luisquintanilla.me/blob/main/_src/media/lossless-audio-coming-spotify.md)

**What you would type in the issue:**

Title: `[Media] Lossless audio coming to Spotify`

Content:
```markdown
I guess people complained enough they're finally adding it

[Drag and drop your screenshot here]
```

Tags: `music, spotify`

**GitHub auto-converts to:**
```markdown
I guess people complained enough they're finally adding it

![Pasted image 20250913091632.png](https://github.com/user-attachments/assets/...)
```

**Automation generates:**
```markdown
---
title: Lossless audio coming to Spotify
post_type: media
published_date: "2025-09-13 09:16 -05:00"
tags: ["music", "spotify"]
---

I guess people complained enough they're finally adding it

:::media
- url: "https://cdn.luisquintanilla.me/files/images/2025/09/13/Pasted_image_20250913091632.png"
  alt: "Pasted image 20250913091632.png"
  mediaType: "image"
  aspectRatio: "landscape"
  caption: "Lossless audio coming to Spotify"
:::media
```

**Perfect match!** ✅

---

## Summary

**The workflow preserves your content completely** - it only transforms GitHub's temporary attachment URLs into permanent CDN URLs wrapped in `:::media` blocks. Everything else (text, formatting, structure) stays exactly as you wrote it.

This means you can:
- ✅ Write freely in markdown
- ✅ Add media anywhere in your content
- ✅ Mix text and media naturally
- ✅ Use all markdown features
- ✅ Get automatic permanent storage
- ✅ Have consistent `:::media` block formatting
