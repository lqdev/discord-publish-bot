# Discord Publish Bot - Quick Reference

## 🎯 For Users: Publishing Content

### Discord Commands
| Command | Purpose | Example |
|---------|---------|---------|
| `/post note` | Personal thoughts & ideas | Daily observations, insights |
| `/post response` | Reply to other content | Article responses, social media reactions |
| `/post bookmark` | Save links with notes | Resource curation, link sharing |
| `/post media [file]` | Share media with descriptions | Photos, videos, documents |

### Publishing Workflow
1. **Type command** → 2. **Fill modal** → 3. **Submit** → 4. **Merge GitHub PR**

**Result**: Discord content becomes properly formatted website post! ✨

👉 **[Complete User Guide](docs/team/user-guide.md)** for detailed instructions

---

## 👨‍💻 For Developers: Quick Setup

### One-Command Setup
```bash
git clone <repository-url>
cd discord-publish-bot
python setup.py                    # Installs UV + dependencies
```

### Essential Commands
```bash
# Development workflow
uv run discord-bot                 # Start Discord bot
uv run publishing-api              # Start API server  
uv run pytest tests/unit/ -v       # Run tests (46/46 should pass)
uv run python scripts/security-check.py  # Security verification
```

### Configuration
1. **Copy template**: `cp .env.example .env`
2. **Follow guide**: [Credential Setup Guide](docs/team/credential-setup-guide.md)
3. **Verify setup**: All tests passing + security check passes

👉 **[Complete Developer Onboarding](docs/team/onboarding-guide.md)** for full setup

---

## 🔧 Troubleshooting

### Users: Bot Not Responding
- ✅ Check bot is online in Discord server
- ✅ Verify you have slash command permissions
- ✅ Contact admin to confirm your Discord User ID is authorized
- ✅ Try `/post note` exactly as shown

### Developers: Setup Issues
- ✅ Re-run `python setup.py` for clean setup
- ✅ Check `.env` file has real values (not placeholders)
- ✅ Run `uv run python scripts/security-check.py`
- ✅ Verify all tests pass: `uv run pytest tests/unit/ -v`

---

## 📚 Documentation Links

### User Resources
- **[User Guide](docs/team/user-guide.md)** - Complete usage instructions
- **[Discord Commands](docs/team/user-guide.md#discord-commands-reference)** - All command details
- **[Content Tips](docs/team/user-guide.md#content-formatting-guide)** - Writing and formatting guidance

### Developer Resources  
- **[Onboarding Guide](docs/team/onboarding-guide.md)** - New developer setup
- **[Technical Specs](specs/technical/discord-publish-bot-technical-spec.md)** - System architecture
- **[API Docs](specs/api/discord-publishing-api.md)** - Publishing API reference
- **[Security Guide](docs/team/security-guidelines.md)** - Security best practices

### Project Information
- **[README](README.md)** - Project overview and status
- **[Backlog](backlog.md)** - Features and development progress  
- **[Changelog](changelog.md)** - Detailed development history
- **[ADRs](docs/adr/)** - Architecture decisions and rationale

---

## 🎉 Production Status

**✅ LIVE**: Production system operational on Azure Container Apps  
**✅ VALIDATED**: Direct user confirmation: *"It worked!!!!"*  
**✅ COMPREHENSIVE**: Full Discord attachment support operational  
**✅ FAST**: <2 second Discord → GitHub → Site publishing workflow  
**✅ SECURE**: Zero production information exposure with full credential protection

**Latest Version**: 2.0.3 (Complete attachment functionality)  
**Health Status**: `https://<app-name>.<region>.azurecontainerapps.io/health`

---

*Quick Reference v1.0 | Production System Operational ✅*
