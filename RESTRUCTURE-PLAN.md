# Discord Publish Bot Restructuring Plan

## Current Issues Identified

### 🔴 Critical Issues (Code Quality & Maintainability)
1. **Organic Code Growth**: Legacy and new code intermixed in `src/` directory
2. **Import Path Issues**: Inconsistent import patterns (`src.module` vs relative imports)
3. **Test Script Proliferation**: 11+ test scripts in `scripts/` that should be proper pytest tests
4. **Entry Point Inconsistencies**: Mixed module paths and execution patterns
5. **Deployment Complexity**: Combined app pattern not following best practices

### 🟡 Structural Issues (Architecture)
1. **Module Duplication**: `discord_bot` and `discord_interactions` serve similar purposes
2. **Configuration Scattered**: Multiple config files with overlapping concerns
3. **Not Following uv Best Practices**: Missing proper project structure for modern Python
4. **Testing Strategy**: Ad-hoc testing instead of proper test suite

## Proposed Restructuring (Based on Research)

### Phase 1: Project Structure Modernization

#### New Directory Structure (src/ layout + uv best practices)
```
discord-publish-bot/
├── pyproject.toml                 # Enhanced with proper entry points
├── uv.lock
├── README.md
├── .python-version                # Python version pinning
├── src/
│   └── discord_publish_bot/       # Single, unified package
│       ├── __init__.py
│       ├── main.py                # CLI entry points
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py        # Unified configuration
│       │   └── environment.py     # Environment-specific configs
│       ├── discord/
│       │   ├── __init__.py
│       │   ├── bot.py             # WebSocket bot (dev/testing)
│       │   ├── interactions.py    # HTTP interactions (production)
│       │   ├── modals.py
│       │   └── commands.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── app.py             # FastAPI application
│       │   ├── routes/
│       │   ├── models/
│       │   └── dependencies.py
│       ├── publishing/
│       │   ├── __init__.py
│       │   ├── service.py
│       │   ├── github_client.py
│       │   └── models.py
│       └── shared/
│           ├── __init__.py
│           ├── exceptions.py
│           ├── types.py
│           └── utils.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_discord.py
│   │   ├── test_publishing.py
│   │   └── test_api.py
│   ├── integration/
│   │   ├── test_discord_integration.py
│   │   ├── test_api_integration.py
│   │   └── test_full_workflow.py
│   └── e2e/
│       └── test_end_to_end.py
├── scripts/                      # Utility scripts only
│   ├── dev.py                    # Development helpers
│   ├── deploy.py                 # Deployment helpers
│   └── security-check.py         # Security validation
└── docs/
    └── deployment.md
```

#### Key Improvements
1. **Single Package**: `discord_publish_bot` replaces multiple conflicting packages
2. **Domain-Driven Organization**: Code organized by business domains (discord, api, publishing)
3. **Proper Test Structure**: Unit, integration, and E2E tests with pytest
4. **Clear Entry Points**: Standardized CLI interfaces
5. **uv Optimization**: Proper dependency groups and build configuration

### Phase 2: Code Consolidation

#### Discord Module Unification
- Merge `discord_bot` and `discord_interactions` into unified `discord` module
- Support both WebSocket (development) and HTTP (production) modes
- Unified command handling and modal system

#### Configuration Consolidation  
- Single `settings.py` with Pydantic models
- Environment-specific overrides
- Validation and type safety

#### API Module Restructuring
- Clean FastAPI application structure
- Proper routing organization
- Dependency injection patterns

### Phase 3: Testing Migration

#### Convert Scripts to Proper Tests
- `test-*.py` scripts → `tests/integration/` or `tests/e2e/`
- Pytest fixtures for common setup
- Proper assertion patterns
- CI/CD integration

#### Test Categories
- **Unit Tests**: Individual function/class testing
- **Integration Tests**: Multi-component testing
- **E2E Tests**: Full workflow validation

### Phase 4: Entry Point Optimization

#### Standardized CLI Interface
```toml
[project.scripts]
discord-publish-bot = "discord_publish_bot.main:cli"
dpb-api = "discord_publish_bot.api.app:cli"
dpb-deploy = "discord_publish_bot.main:deploy"
```

#### Development Commands
```bash
uv run discord-publish-bot          # Start Discord bot
uv run dpb-api                      # Start API server  
uv run dpb-deploy                   # Deploy to Azure
```

## Implementation Plan

### Step 1: Backup and Branch
- [x] Create restructure branch
- [x] Archive current state

### Step 2: Create New Structure
- [ ] Initialize new package structure
- [ ] Update pyproject.toml
- [ ] Create new module hierarchy

### Step 3: Migrate Code
- [ ] Consolidate Discord modules
- [ ] Unify configuration
- [ ] Restructure API module
- [ ] Update imports

### Step 4: Test Migration
- [ ] Convert test scripts to pytest
- [ ] Create proper fixtures
- [ ] Validate functionality

### Step 5: Validation
- [ ] Build and test
- [ ] Deploy validation
- [ ] Performance testing

## Success Criteria

1. **Clean Build**: `uv build` succeeds without warnings
2. **Unified Interface**: Single package with clear entry points
3. **Proper Testing**: All functionality covered by pytest
4. **Deployment Ready**: Azure Container Apps compatible
5. **Maintainable**: Clear separation of concerns

## Risk Mitigation

1. **Backup Strategy**: Git branch with full history
2. **Incremental Migration**: Phase-by-phase validation
3. **Testing**: Continuous validation during migration
4. **Rollback Plan**: Ability to revert to current structure

This restructuring follows the research-backed best practices for modern Python development with uv, creating a maintainable, scalable, and production-ready codebase.
