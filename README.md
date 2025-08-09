# Discord Publish Bot

A Discord bot that automatically publishes Discord posts to GitHub repositories as formatted markdown files, enabling seamless content publishing to static sites.

## Quick Start

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
   git clone <repository-url>
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

### Development Setup

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
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
# Activate virtual environment first
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Start Publishing API
cd src/publishing_api
uv run uvicorn main:app --reload --port 8000

# Start Discord Bot (in separate terminal)
cd src/discord_bot
uv run python main.py
```

#### Production Deployment
See [Deployment Guide](docs/deployment.md) for production setup instructions.

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

- [Product Requirements Document](projects/active/discord-publish-bot.md)
- [Technical Specification](specs/technical/discord-publish-bot-technical-spec.md)
- [API Documentation](specs/api/discord-publishing-api.md)
- [Architecture Decision Records](docs/adr/)
- [Project Backlog](backlog.md)
- [Changelog](changelog.md)

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
uv run uvicorn src.publishing_api.main:app --reload  # Start API
uv run python src/discord_bot/main.py               # Start bot
```

### Project Management
This project follows sprint-based development with comprehensive documentation. See:
- [Project Backlog](backlog.md) for current sprint status
- [Changelog](changelog.md) for detailed progress tracking

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

## Contributing

1. Follow the established documentation templates in `templates/`
2. Update appropriate documentation when making changes
3. Ensure tests pass and coverage remains above 80%
4. Follow sprint planning methodology outlined in backlog

## License

[Add your license information here]

## Support

For technical issues and questions:
- Review [Technical Specification](specs/technical/discord-publish-bot-technical-spec.md)
- Check [API Documentation](specs/api/discord-publishing-api.md)
- Consult [Project Backlog](backlog.md) for known issues

---

**Project Status:** Active Development (Sprint 1)  
**Last Updated:** 2025-08-08  
**Next Milestone:** Development Environment Setup (2025-08-15)
