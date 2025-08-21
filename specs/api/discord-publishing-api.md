# Discord Publishing API Documentation

## API Information
**API Name:** Discord Publish  "filepath": "_src/notes/2025-08-08-my-first-note.md",
  "commit_sha": "abc123def456",
  "site_url": "https://yoursite.com/notes/my-first-note" API  
**Version:** 1.0.0  
**Base URL:** `https://discord-publish-api.fly.dev`  
**Last Updated:** 2025-08-08  
**Maintainer:** Discord Publish Bot Team  
**Support Contact:** support@discord-publish-bot.dev

## Overview

### API Purpose
The Discord Publishing API enables automated publishing of Discord content to GitHub repositories as formatted markdown files with YAML frontmatter. It processes four post types (notes, responses, bookmarks, media) and handles GitHub repository commits with proper folder organization.

### Key Features
- **Secure Authentication**: API key and Discord user ID validation
- **Content Processing**: Automatic YAML frontmatter generation and markdown formatting
- **GitHub Integration**: Direct repository commits with automated site deployment triggers
- **Post Type Support**: Notes, responses, bookmarks, and media posts with type-specific handling
- **Error Handling**: Comprehensive error responses with actionable guidance

### Target Audience
- **Primary Users**: Discord bot applications requiring GitHub publishing capabilities
- **Use Cases**: Personal static site content publishing, automated blog posting, content archival
- **Integration Patterns**: Discord slash command workflows, webhook integrations, automated content pipelines

### API Design Principles
- **RESTful Design**: Standard HTTP methods with resource-based URLs
- **Consistency**: Uniform request/response formats and error handling
- **Versioning Strategy**: URL path versioning with backward compatibility
- **Error Handling**: Structured error responses with detailed error information

## Getting Started

### Prerequisites
- Valid Discord bot application with user authorization
- GitHub repository with write access permissions
- API key obtained from Discord Publishing service
- HTTPS endpoint capability for secure communications

### Quick Start Guide

#### 1. Authentication Setup
Obtain your API key from the Discord Publishing service and configure environment variables:

```bash
# Environment Configuration
export API_KEY="your_api_key_here"
export DISCORD_USER_ID="your_discord_user_id"
export GITHUB_TOKEN="your_github_token"
export GITHUB_REPO="username/repository"
```

#### 2. First API Call
Test connectivity with a health check:

```bash
curl -X GET "https://discord-publish-api.fly.dev/health" \
  -H "Accept: application/json"
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-08T10:30:00Z",
  "checks": {
    "github": "healthy",
    "config": "healthy"
  }
}
```

#### 3. Publishing Your First Post
Publish a note post using the publishing endpoint:

```bash
curl -X POST "https://discord-publish-api.fly.dev/publish" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "/post note\n---\ntitle: My First Note\n---\nThis is my first published note!",
    "user_id": "your_discord_user_id"
  }'
```

**Response:**
```json
{
  "status": "success",
  "filepath": "posts/notes/2025-08-08-my-first-note.md",
  "commit_sha": "abc123def456...",
  "site_url": "https://yoursite.com/posts/notes/my-first-note"
}
```

### SDK and Libraries

#### Official SDKs
- **Python SDK:** `pip install discord-publish-sdk` (Coming Soon)
- **JavaScript SDK:** `npm install discord-publish-js` (Coming Soon)
- **TypeScript SDK:** Included with JavaScript SDK

#### Community SDKs
- **Go Client:** `github.com/community/discord-publish-go` (Community Maintained)
- **Rust Client:** `discord-publish-rs` crate (Community Maintained)

#### Code Examples
- **Python Examples:** [GitHub Repository](https://github.com/discord-publish-bot/examples-python)
- **JavaScript Examples:** [GitHub Repository](https://github.com/discord-publish-bot/examples-js)
- **Discord.py Integration:** [Integration Guide](https://docs.discord-publish-bot.dev/integration/discord-py)

## Authentication

### Authentication Methods

#### API Key Authentication
**Header:** `Authorization: Bearer {api_key}`

**How to obtain:**
1. Register your Discord bot application
2. Configure authorized Discord user ID
3. Generate API key through service dashboard
4. Configure secure storage for API credentials

**Example:**
```bash
curl -X POST "https://discord-publish-api.fly.dev/publish" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json"
```

#### User ID Validation
All requests must include the authorized Discord user ID in the request payload for additional security validation.

**Example Request Body:**
```json
{
  "message": "/post note\nContent here",
  "user_id": "123456789012345678"
}
```

### Security Considerations
- **HTTPS Only:** All API calls must use HTTPS encryption
- **Key Rotation:** API keys should be rotated regularly for security
- **Rate Limiting:** 60 requests per minute per API key
- **User Whitelisting:** Only pre-configured Discord user IDs are authorized

## Base URL and Versioning

### Environment URLs
- **Production:** `https://discord-publish-api.fly.dev`
- **Staging:** `https://staging.discord-publish-api.fly.dev`
- **Development:** `https://dev.discord-publish-api.fly.dev`

### API Versioning
**Current Version:** `v1`  
**Versioning Scheme:** URL path versioning (`/v1/publish`)  
**Deprecation Policy:** 12 months notice for breaking changes

**Versioned Endpoint Example:**
```bash
curl -X POST "https://discord-publish-api.fly.dev/v1/publish" \
  -H "Authorization: Bearer {api_key}" \
  -H "Accept: application/vnd.api+json;version=1"
```

### Backward Compatibility
- **Breaking Changes:** Introduced only in new major versions
- **Migration Guide:** Provided 3 months before deprecation
- **Support Timeline:** Each version supported for minimum 18 months

## API Reference

### Core Resources

#### Health Check

##### Get API Health Status
```http
GET /health
```

**Description:** Check API service health and dependencies status

**Parameters:** None

**Example Request:**
```bash
curl -X GET "https://discord-publish-api.fly.dev/health" \
  -H "Accept: application/json"
```

**Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-08T10:30:00Z",
  "checks": {
    "github": "healthy",
    "config": "healthy"
  },
  "version": "1.0.0"
}
```

**Response Codes:**
- `200 OK` - Service is healthy
- `503 Service Unavailable` - Service is degraded or unhealthy

#### Publishing Endpoint

##### Publish Discord Post
```http
POST /publish
```

**Description:** Publish a Discord post to GitHub repository as formatted markdown file

**Headers:**
| Header | Type | Required | Description |
|--------|------|----------|-------------|
| Authorization | string | Yes | Bearer token with API key |
| Content-Type | string | Yes | Must be `application/json` |

**Request Body:**
```json
{
  "message": "string",
  "user_id": "string"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| message | string | Yes | Discord command message with content and optional frontmatter |
| user_id | string | Yes | Discord user ID for authorization validation |

**Message Format:**
The message parameter should follow this structure:
```
/post {type}
---
{optional frontmatter}
---
{content}
```

**Example Request:**
```bash
curl -X POST "https://discord-publish-api.fly.dev/publish" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "/post note\n---\ntitle: Development Update\ntags: [development, progress]\n---\nMade significant progress on the API today. Implemented authentication and basic publishing workflow.",
    "user_id": "123456789012345678"
  }'
```

**Example Response:**
```json
{
  "status": "success",
  "filepath": "_src/notes/2025-08-08-development-update.md",
  "commit_sha": "a1b2c3d4e5f6789012345678901234567890abcd",
  "site_url": "https://yoursite.com/notes/development-update"
}
```

**Response Codes:**
- `200 OK` - Post published successfully
- `400 Bad Request` - Invalid message format or content
- `401 Unauthorized` - Invalid or missing API key
- `403 Forbidden` - Discord user ID not authorized
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - GitHub API or processing error

### Post Type Specifications

#### Note Posts
**Command:** `/post note`  
**Storage Folder:** `_src/notes/`  
**Description:** General purpose notes and thoughts

**Message Format:**
```
/post note
---
title: "Optional Title"
tags: ["tag1", "tag2"]
---
Your note content in **markdown** format.

- Supports lists
- And other markdown features
```

**Generated Frontmatter:**
```yaml
---
type: note
title: "Note Title"
date: "2025-08-08T10:30:00Z"
slug: "note-title-slug"
tags: ["development", "notes"]
---
```

#### Response Posts
**Command:** `/post response`  
**Storage Folder:** `posts/responses/`  
**Description:** Responses to other content (replies, likes, reshares)

**Message Format:**
```
/post response
---
response_type: "reply"
in_reply_to: "https://example.com/original-post"
---
This is my response to the original post.
```

**Generated Frontmatter:**
```yaml
---
type: response
response_type: "reply"
date: "2025-08-08T10:30:00Z"
slug: "response-slug"
in_reply_to: "https://example.com/original-post"
---
```

**Response Types:**
- `reply` - Direct response to content
- `like` - Positive reaction
- `reshare` - Sharing with commentary

#### Bookmark Posts
**Command:** `/post bookmark`  
**Storage Folder:** `_src/bookmarks/`  
**Description:** Saved links with optional notes

**Message Format:**
```
/post bookmark
---
url: "https://example.com/article"
title: "Interesting Article"
tags: ["reading", "development"]
---
This article has some great insights about API design.
```

**Generated Frontmatter:**
```yaml
---
type: bookmark
title: "Interesting Article"
url: "https://example.com/article"
date: "2025-08-08T10:30:00Z"
slug: "interesting-article"
tags: ["reading", "development"]
---
```

#### Media Posts
**Command:** `/post media`  
**Storage Folder:** `posts/media/`  
**Description:** Images, videos, and other media with captions

**Message Format:**
```
/post media
---
media_url: "https://example.com/image.jpg"
alt_text: "Screenshot of the new feature"
title: "New Feature Preview"
---
Here's a preview of the new feature we've been working on.
```

**Generated Frontmatter:**
```yaml
---
type: media
title: "New Feature Preview"
media_url: "https://example.com/image.jpg"
alt_text: "Screenshot of the new feature"
date: "2025-08-08T10:30:00Z"
slug: "new-feature-preview"
---
```

## Error Handling

### Error Response Format
All errors follow a consistent JSON structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description",
    "details": {
      "field": "specific field error",
      "suggestion": "how to fix the error"
    },
    "request_id": "req_1234567890abcdef"
  }
}
```

### HTTP Status Codes
| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request data or message format |
| 401 | Unauthorized | Authentication required or invalid API key |
| 403 | Forbidden | Discord user ID not authorized |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | GitHub API or server error |
| 503 | Service Unavailable | API temporarily unavailable |

### Error Codes
| Error Code | Description | Resolution |
|------------|-------------|------------|
| INVALID_MESSAGE_FORMAT | Discord message format is incorrect | Check message follows `/post {type}` format |
| MISSING_CONTENT | Required content fields are missing | Ensure message includes content after frontmatter |
| INVALID_POST_TYPE | Post type not supported | Use: note, response, bookmark, or media |
| GITHUB_API_ERROR | GitHub API request failed | Check repository permissions and token validity |
| RATE_LIMIT_EXCEEDED | Too many requests in time window | Wait before retrying, current limit: 60/minute |
| USER_NOT_AUTHORIZED | Discord user ID not in whitelist | Contact administrator for access |
| INVALID_FRONTMATTER | YAML frontmatter syntax error | Check YAML formatting between `---` markers |

### Error Handling Best Practices
- Always check the HTTP status code first
- Parse the error response body for detailed information
- Use the `request_id` when contacting support
- Implement exponential backoff for retries
- Handle rate limiting gracefully with delays

### Example Error Responses

#### 400 Bad Request - Invalid Message Format
```json
{
  "error": {
    "code": "INVALID_MESSAGE_FORMAT",
    "message": "Message must start with '/post {type}' command",
    "details": {
      "received": "note content without command",
      "expected": "/post note\n{content}",
      "suggestion": "Start message with '/post note' or other valid post type"
    },
    "request_id": "req_abc123def456"
  }
}
```

#### 403 Forbidden - Unauthorized User
```json
{
  "error": {
    "code": "USER_NOT_AUTHORIZED",
    "message": "Discord user ID not authorized for publishing",
    "details": {
      "user_id": "123456789012345678",
      "suggestion": "Contact administrator to add user ID to authorized list"
    },
    "request_id": "req_def456ghi789"
  }
}
```

## Rate Limiting

### Rate Limit Policies
| Authentication Type | Requests per Minute | Requests per Hour |
|-------------------|-------------------|-------------------|
| API Key | 60 | 3,600 |
| Burst Allowance | 10 | N/A |

### Rate Limit Headers
Every response includes rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1691495460
X-RateLimit-Window: 60
```

### Handling Rate Limits
When rate limited (HTTP 429), the response includes:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded",
    "details": {
      "retry_after": 30,
      "limit": 60,
      "window": "minute"
    },
    "request_id": "req_rate_limit_123"
  }
}
```

**Best Practices:**
- Monitor rate limit headers in responses
- Implement exponential backoff for retries
- Cache API responses when appropriate
- Consider request batching for multiple posts

## Code Examples

### Python

#### Installation
```bash
pip install requests python-dotenv
```

#### Basic Usage
```python
import requests
import os
from datetime import datetime

class DiscordPublishAPI:
    def __init__(self, api_key: str, base_url: str = "https://discord-publish-api.fly.dev"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def publish_note(self, content: str, title: str = None, tags: list = None, user_id: str = None):
        """Publish a note post."""
        frontmatter = []
        if title:
            frontmatter.append(f"title: {title}")
        if tags:
            frontmatter.append(f"tags: {tags}")
        
        frontmatter_str = "\n".join(frontmatter)
        message = f"/post note\n---\n{frontmatter_str}\n---\n{content}"
        
        data = {
            "message": message,
            "user_id": user_id or os.getenv("DISCORD_USER_ID")
        }
        
        response = self.session.post(f"{self.base_url}/publish", json=data)
        return response.json()
    
    def publish_bookmark(self, url: str, notes: str = None, title: str = None, tags: list = None, user_id: str = None):
        """Publish a bookmark post."""
        frontmatter = [f"url: {url}"]
        if title:
            frontmatter.append(f"title: {title}")
        if tags:
            frontmatter.append(f"tags: {tags}")
        
        frontmatter_str = "\n".join(frontmatter)
        content = notes or f"Bookmarked: {url}"
        message = f"/post bookmark\n---\n{frontmatter_str}\n---\n{content}"
        
        data = {
            "message": message,
            "user_id": user_id or os.getenv("DISCORD_USER_ID")
        }
        
        response = self.session.post(f"{self.base_url}/publish", json=data)
        return response.json()
    
    def health_check(self):
        """Check API health status."""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()

# Example usage
api = DiscordPublishAPI(os.getenv("API_KEY"))

# Publish a note
result = api.publish_note(
    content="This is my first note via the API!",
    title="API Test Note",
    tags=["testing", "api"],
    user_id=os.getenv("DISCORD_USER_ID")
)

print(f"Published: {result}")
```

#### Advanced Example with Error Handling
```python
import requests
import time
import logging
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DiscordPublishAPIClient:
    def __init__(self, api_key: str, user_id: str, base_url: str = "https://discord-publish-api.fly.dev"):
        self.api_key = api_key
        self.user_id = user_id
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, max_retries: int = 3) -> Dict[str, Any]:
        """Make API request with retry logic."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, json=data)
                
                if response.status_code == 429:
                    # Rate limited - extract retry time
                    error_data = response.json()
                    retry_after = error_data.get("error", {}).get("details", {}).get("retry_after", 60)
                    logger.warning(f"Rate limited. Retrying in {retry_after} seconds...")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception(f"Failed to complete request after {max_retries} attempts")
    
    def publish_post(self, post_type: str, content: str, frontmatter: Dict = None) -> Dict[str, Any]:
        """Generic post publishing method."""
        frontmatter = frontmatter or {}
        
        # Build frontmatter string
        fm_lines = []
        for key, value in frontmatter.items():
            if isinstance(value, list):
                fm_lines.append(f"{key}: {value}")
            else:
                fm_lines.append(f"{key}: {value}")
        
        fm_str = "\n".join(fm_lines)
        message = f"/post {post_type}"
        if fm_str:
            message += f"\n---\n{fm_str}\n---"
        message += f"\n{content}"
        
        data = {
            "message": message,
            "user_id": self.user_id
        }
        
        return self._make_request("POST", "/publish", data)

# Example usage with error handling
try:
    client = DiscordPublishAPIClient(
        api_key=os.getenv("API_KEY"),
        user_id=os.getenv("DISCORD_USER_ID")
    )
    
    # Publish a note
    result = client.publish_post(
        post_type="note",
        content="This is a test note with error handling.",
        frontmatter={
            "title": "Error Handling Test",
            "tags": ["testing", "error-handling"]
        }
    )
    
    logger.info(f"Successfully published: {result['filepath']}")
    
except Exception as e:
    logger.error(f"Failed to publish post: {e}")
```

### JavaScript/Node.js

#### Installation
```bash
npm install axios dotenv
```

#### Basic Usage
```javascript
const axios = require('axios');
require('dotenv').config();

class DiscordPublishAPI {
    constructor(apiKey, baseUrl = 'https://discord-publish-api.fly.dev') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json'
            }
        });
    }
    
    async publishNote(content, options = {}) {
        const { title, tags, userId } = options;
        
        let frontmatter = [];
        if (title) frontmatter.push(`title: ${title}`);
        if (tags) frontmatter.push(`tags: [${tags.map(t => `"${t}"`).join(', ')}]`);
        
        const frontmatterStr = frontmatter.join('\n');
        const message = `/post note\n---\n${frontmatterStr}\n---\n${content}`;
        
        const data = {
            message,
            user_id: userId || process.env.DISCORD_USER_ID
        };
        
        try {
            const response = await this.client.post('/publish', data);
            return response.data;
        } catch (error) {
            throw new Error(`API request failed: ${error.response?.data?.error?.message || error.message}`);
        }
    }
    
    async publishBookmark(url, options = {}) {
        const { notes, title, tags, userId } = options;
        
        let frontmatter = [`url: ${url}`];
        if (title) frontmatter.push(`title: ${title}`);
        if (tags) frontmatter.push(`tags: [${tags.map(t => `"${t}"`).join(', ')}]`);
        
        const frontmatterStr = frontmatter.join('\n');
        const content = notes || `Bookmarked: ${url}`;
        const message = `/post bookmark\n---\n${frontmatterStr}\n---\n${content}`;
        
        const data = {
            message,
            user_id: userId || process.env.DISCORD_USER_ID
        };
        
        try {
            const response = await this.client.post('/publish', data);
            return response.data;
        } catch (error) {
            throw new Error(`API request failed: ${error.response?.data?.error?.message || error.message}`);
        }
    }
    
    async healthCheck() {
        try {
            const response = await this.client.get('/health');
            return response.data;
        } catch (error) {
            throw new Error(`Health check failed: ${error.message}`);
        }
    }
}

// Example usage
(async () => {
    try {
        const api = new DiscordPublishAPI(process.env.API_KEY);
        
        // Check API health
        const health = await api.healthCheck();
        console.log('API Health:', health);
        
        // Publish a note
        const noteResult = await api.publishNote(
            'This is my first note via the JavaScript API!',
            {
                title: 'JavaScript API Test',
                tags: ['testing', 'javascript', 'api'],
                userId: process.env.DISCORD_USER_ID
            }
        );
        
        console.log('Note published:', noteResult);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
})();
```

### cURL Examples

#### Basic Post Publishing
```bash
# Publish a note
curl -X POST "https://discord-publish-api.fly.dev/publish" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "/post note\n---\ntitle: My Note\ntags: [\"development\", \"notes\"]\n---\nThis is my note content.",
    "user_id": "your_discord_user_id"
  }'

# Publish a bookmark
curl -X POST "https://discord-publish-api.fly.dev/publish" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "/post bookmark\n---\nurl: https://example.com\ntitle: Useful Article\n---\nThis article has great insights.",
    "user_id": "your_discord_user_id"
  }'

# Publish a response
curl -X POST "https://discord-publish-api.fly.dev/publish" \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "/post response\n---\nresponse_type: reply\nin_reply_to: https://example.com/original\n---\nThis is my response.",
    "user_id": "your_discord_user_id"
  }'

# Health check
curl -X GET "https://discord-publish-api.fly.dev/health" \
  -H "Accept: application/json"
```

## Testing

### Test Environment
**Base URL:** `https://staging.discord-publish-api.fly.dev`  
**Test API Key:** Contact support for staging credentials

### Testing Checklist
- [ ] Test authentication with valid/invalid API keys
- [ ] Test all post types (note, response, bookmark, media)
- [ ] Test error scenarios (400, 401, 403, 429, 500)
- [ ] Test rate limiting behavior
- [ ] Test frontmatter parsing and generation
- [ ] Verify GitHub repository commits

### Postman Collection
**Download:** [Discord Publishing API Postman Collection](https://api.discord-publish-bot.dev/postman)

The Postman collection includes:
- Pre-configured environment variables
- Authentication setup
- All endpoint examples with various post types
- Error scenario tests
- Rate limiting tests

## FAQ

### General Questions

**Q: How do I get an API key?**  
A: Register your Discord bot application and configure the authorized Discord user ID. API keys are generated through the service dashboard.

**Q: What post types are supported?**  
A: Four post types: `note` (general content), `response` (replies/reactions), `bookmark` (saved links), and `media` (images/videos with captions).

**Q: How long do API keys last?**  
A: API keys don't expire but should be rotated regularly for security. We recommend rotation every 90 days.

**Q: Can I use this with multiple GitHub repositories?**  
A: Currently, each API key is configured for a single repository. Contact support for multi-repository access.

### Technical Questions

**Q: Why am I getting a 401 error?**  
A: Check that your API key is valid and included in the Authorization header as `Bearer {api_key}`.

**Q: How do I handle rate limiting?**  
A: Monitor the rate limit headers and implement exponential backoff. Current limit is 60 requests per minute.

**Q: What's the maximum content size?**  
A: Post content is limited to 10MB per request. Large media files should be hosted externally with URLs.

**Q: How do I format frontmatter correctly?**  
A: Use YAML syntax between `---` markers. Example: `title: My Title` or `tags: ["tag1", "tag2"]`.

### Troubleshooting

**Q: My post isn't appearing on my site. What should I check?**  
A: Verify the GitHub commit was successful, check GitHub Actions status, and ensure your static site generator is processing the new file.

**Q: How do I debug API responses?**  
A: Use the `request_id` from error responses when contacting support. Enable detailed logging in your client code.

**Q: What if GitHub API fails?**  
A: The API will return a 500 error with details. Check your GitHub token permissions and repository access.

## Support and Resources

### Getting Help
- **Documentation:** [https://docs.discord-publish-bot.dev](https://docs.discord-publish-bot.dev)
- **API Status:** [https://status.discord-publish-bot.dev](https://status.discord-publish-bot.dev)
- **Support Portal:** [https://support.discord-publish-bot.dev](https://support.discord-publish-bot.dev)
- **Email Support:** support@discord-publish-bot.dev
- **Community Discord:** [Discord Server Invite](https://discord.gg/discord-publish)

### Additional Resources
- **Changelog:** [API Changelog](https://docs.discord-publish-bot.dev/changelog)
- **Migration Guides:** [Version Migration](https://docs.discord-publish-bot.dev/migration)
- **Best Practices:** [Implementation Guide](https://docs.discord-publish-bot.dev/best-practices)
- **Security Guidelines:** [Security Documentation](https://docs.discord-publish-bot.dev/security)

### SLA and Uptime
- **Uptime Target:** 99.9%
- **Response Time Target:** < 2 seconds (95th percentile)
- **Status Page:** [https://status.discord-publish-bot.dev](https://status.discord-publish-bot.dev)

### Contact Information
- **Technical Support:** tech-support@discord-publish-bot.dev
- **Business Development:** business@discord-publish-bot.dev
- **Security Issues:** security@discord-publish-bot.dev

---
*API Documentation Version: 1.0*  
*Last Updated: 2025-08-08*  
*Next Review: 2025-08-22*
