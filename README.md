# Discord Publish Bot

A production-ready Discord bot that automatically publishes Discord posts to GitHub repositories as formatted markdown files, enabling seamless content publishing to static sites. Features complete Discord attachment support and is designed for deployment on Azure Container Apps with scale-to-zero cost optimization.

## 🚀 Quick Start

### For Users (Publishing Content)
1. **Get bot access** from your site administrator
2. **Type `/post note`** in Discord where bot is installed  
3. **Fill the modal** with your content
4. **Submit** to create GitHub PR automatically
5. **Merge PR** to publish on your site

👉 **[Complete User Guide](docs/team/user-guide.md)** for all commands and workflows

### For Developers (Contributing)
1. **Clone repository**: `git clone https://github.com/your-username/discord-publish-bot.git`
2. **Run setup**: `python setup.py` (installs UV + dependencies)
3. **Configure credentials**: Follow [credential setup guide](docs/team/credential-setup-guide.md)
4. **Start development**: `uv run discord-bot` and `uv run publishing-api`
5. **Run tests**: `uv run pytest tests/unit/ -v`

👉 **[Complete Developer Onboarding](docs/team/onboarding-guide.md)** for full setup and contribution guide

## Production Features

### ✅ Complete Discord Integration (Including Attachments)
- **Discord Commands**: `/post note`, `/post response`, `/post bookmark`, `/post media [attachment]`
- **Attachment Support**: Full Discord file upload → media block generation workflow
- **Real-time Publishing**: <2 second Discord → GitHub workflow including attachments
- **Perfect Format Compliance**: Custom frontmatter + automatic `:::media` block generation
- **Modal Interfaces**: User-friendly forms with automatic attachment data pre-filling

### ✅ Media Block Generation
- **Automatic Processing**: Discord attachments → `:::media` blocks with complete metadata
- **Media Syntax**: Proper url, alt, mediaType, aspectRatio, caption fields
- **Seamless Workflow**: Upload attachment → pre-filled modal → GitHub PR with media
- **Production Ready**: Full attachment functionality for content creation

### ✅ Azure Container Apps Deployment
- **Cloud-Ready**: Designed for Azure Container Apps deployment
- **Scale-to-Zero**: Cost optimization with automatic scaling
- **Security**: Comprehensive secret management and authentication
- **Monitoring**: Health checks and performance tracking
- **Attachment Support**: Full Discord webhook attachment processing

### ✅ GitHub Publishing Excellence
- **Format Precision**: Inline quoted tags arrays `["tag1","tag2"]` as required
- **Media Block Generation**: Automatic `:::media` syntax with complete metadata
- **Clean Filenames**: No unwanted date prefixes
- **Site Compliance**: Perfect frontmatter matching VS Code snippet schema
- **Error Handling**: Comprehensive validation and user feedback

## 🎯 Production Usage

### Discord Commands (Live + Attachment Support)
Use these commands in any Discord server where the bot is installed:

```
/post note                    # Publish a note to your site
/post response               # Create a response post  
/post bookmark               # Save and annotate a bookmark
/post media [attachment]     # Upload file and publish with automatic media blocks
```

### Attachment Functionality
- **File Upload**: Attach any media file to `/post media` command
- **Automatic Processing**: Attachment URL and metadata pre-fill in modal
- **Media Block Generation**: Automatic `:::media` syntax creation
- **Complete Workflow**: Discord upload → modal → GitHub PR with media content

### Health Monitoring
- **Health Check**: `https://<app-name>.<region>.azurecontainerapps.io/health`
- **Status**: Returns system health, version, and configuration status
- **Performance**: Optimized for fast response times

## 🛠️ Development Setup (For Contributors)

### Prerequisites
- Python 3.11+
- [UV Package Manager](https://github.com/astral-sh/uv) (faster than pip)
- Discord Developer Account
- GitHub Repository with appropriate permissions
- HTTPS-capable hosting for Publishing API (for production)

### Automated Setup (Recommended)

1. **One-Command Setup**
   ```bash
   # Clone the repository
   git clone https://github.com/your-username/discord-publish-bot.git
   cd discord-publish-bot
   
   # Run automated setup
   python setup.py
   ```

   This script will:
   - Install UV if not present
   - Create virtual environment
   - Install all dependencies
   - Set up configuration template
   - Run basic tests

2. **Manual Configuration**
   ```bash
   # Edit environment variables
   notepad .env  # Windows
   # nano .env    # Linux/Mac
   ```

### Manual Setup

1. **Clone and Setup Environment**
   ```bash
   git clone https://github.com/your-username/discord-publish-bot.git
   cd discord-publish-bot
   
   # Install UV if not already installed
   # Windows: 
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   # Linux/Mac:
   # curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment and install dependencies
   uv venv
   uv pip install -r requirements.txt
   
   # Or install with development dependencies
   uv pip install -e ".[dev]"
   ```

2. **Activate Virtual Environment**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac  
   source .venv/bin/activate
   ```

3. **Configure Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Discord Bot Setup**
   - Create Discord Application at https://discord.com/developers/applications
   - Create Bot and copy token to `DISCORD_BOT_TOKEN`
   - Enable privileged intents if needed
   - Invite bot to test server with appropriate permissions

4. **GitHub Setup**
   - Create Personal Access Token with `repo` scope
   - Add token to `GITHUB_TOKEN` in .env
   - Specify target repository in `GITHUB_REPO`

### Running the Application

#### Development Mode  
```bash
# Using UV (recommended - no virtual environment activation needed)
# Start Publishing API
uv run publishing-api

# Start Discord Bot (in separate terminal)
uv run discord-bot
```

#### Production Deployment
See deployment documentation for production setup instructions.

## Project Structure

```
discord-publish-bot/
├── docs/                    # Internal documentation and ADRs
├── specs/                   # Technical specifications and API docs
├── projects/               # Project management and PRDs
├── templates/              # Documentation templates
├── src/
│   ├── discord_bot/        # Discord bot implementation
│   ├── publishing_api/     # FastAPI publishing service
│   └── shared/             # Shared utilities and models
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
└── .env.example           # Environment configuration template
```

## Features

### Post Types Supported
- **Notes**: Personal thoughts and observations
- **Responses**: Replies, likes, and reshares to other content
- **Bookmarks**: Links with annotations and tags
- **Media**: Images and videos with captions

### Discord Commands
- `/post note` - Publish a note post
- `/post response` - Publish a response to content
- `/post bookmark` - Save and publish a bookmark
- `/post media` - Publish media with caption

## Documentation

### 📖 User Documentation
- **[User Guide](docs/team/user-guide.md)** - Complete guide for Discord bot users
- **[Getting Started](docs/team/user-guide.md#quick-start---publish-content-in-30-seconds)** - Publish content in 30 seconds
- **[Discord Commands Reference](docs/team/user-guide.md#discord-commands-reference)** - All `/post` commands explained

### 👨‍💻 Developer Documentation  
- **[Developer Onboarding Guide](docs/team/onboarding-guide.md)** - Complete setup for new contributors
- **[Credential Setup Guide](docs/team/credential-setup-guide.md)** - Step-by-step Discord & GitHub configuration
- **[Security Guidelines](docs/team/security-guidelines.md)** - Security best practices and verification

### 🏗️ Technical Documentation
- **[Technical Specification](specs/technical/discord-publish-bot-technical-spec.md)** - Complete system architecture
- **[API Documentation](specs/api/discord-publishing-api.md)** - Publishing API reference
- **[Architecture Decision Records](docs/adr/)** - Key architectural decisions and rationale

### 📋 Project Management
- **[Changelog](changelog.md)** - Detailed development progress and releases

## Development

### Development Commands

UV makes development workflow much faster. Use these commands:

```bash
# Quick development commands
python scripts/dev.py test-fast    # Run fast tests
python scripts/dev.py format       # Format code
python scripts/dev.py lint         # Full code quality check
python scripts/dev.py dev          # Start development servers

# Direct UV commands
uv run pytest                      # Run all tests
uv run black src/ tests/           # Format code
uv run publishing-api              # Start API  
uv run discord-bot                 # Start bot
```

### Project Management
This project follows systematic development with comprehensive documentation. See the [Changelog](changelog.md) for development progress tracking.

## Security

⚠️ **IMPORTANT**: Never commit `.env` files or credentials to version control!

### Quick Security Setup
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Generate secure API key
uv run python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Follow detailed setup guide
# See docs/team/credential-setup-guide.md for complete process

# 4. Verify security setup
uv run python scripts/security-check.py
```

**🔧 Need help setting up credentials?** See our comprehensive [Credential Setup Guide](docs/team/credential-setup-guide.md) for step-by-step Discord Developer Portal setup, GitHub token generation, and security configuration.

### Security Features
- All API endpoints require authentication via API key
- Discord user validation prevents unauthorized usage  
- Environment variables for secure configuration
- HTTPS enforcement for production deployments
- Comprehensive .gitignore protecting sensitive files

For complete security guidelines, see [Security Documentation](docs/team/security-guidelines.md).

## Project Status & Testing

### Test Suite Validation
```bash
# Run unit tests
uv run pytest tests/unit/ -v

# Run all tests
uv run pytest tests/unit/ tests/test_security_isolation.py

# Validate Docker build
docker build -t discord-publish-bot:test .
```

## Contributing

1. Follow the established documentation templates in `templates/`
2. Update appropriate documentation when making changes
3. Ensure tests pass and maintain good coverage
4. Follow the contribution guidelines

## License

[Add your license information here]

## Support

For technical issues and questions:
- Review [Technical Specification](specs/technical/discord-publish-bot-technical-spec.md)
- Check [API Documentation](specs/api/discord-publishing-api.md)
- Open an issue on GitHub for bug reports or feature requests

---

**Project Status:** Production-Ready with Full Discord Integration ✅
