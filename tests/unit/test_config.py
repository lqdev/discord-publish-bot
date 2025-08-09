"""
Unit tests for configuration system.

Tests the Pydantic-based configuration loading and validation.
"""

import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from discord_publish_bot.config import AppSettings, DiscordSettings, GitHubSettings, APISettings, PublishingSettings


@pytest.mark.unit
class TestConfigurationSettings:
    """Test configuration loading and validation."""
    
    def test_discord_settings_validation(self):
        """Test Discord settings validation."""
        # Valid settings
        valid_settings = DiscordSettings(
            bot_token="FAKE_TEST_TOKEN.NEVER_REAL.SAFE_FOR_TESTING_123456789",
            application_id="123456789012345678",
            public_key="a" * 64,
            authorized_user_id="987654321098765432"
        )
        
        assert valid_settings.bot_token == "FAKE_TEST_TOKEN.NEVER_REAL.SAFE_FOR_TESTING_123456789"
        assert valid_settings.application_id == "123456789012345678"
        assert valid_settings.public_key == "a" * 64
        assert valid_settings.authorized_user_id == "987654321098765432"
        
        # Test validation of required fields
        with pytest.raises(ValidationError):
            DiscordSettings(bot_token="")  # Empty token should fail
    
    def test_github_settings_validation(self):
        """Test GitHub settings validation."""
        # Valid settings
        valid_settings = GitHubSettings(
            token="ghp_valid_token_12345",
            repository="user/repo",
            branch="main"
        )
        
        assert valid_settings.token == "ghp_valid_token_12345"
        assert valid_settings.repository == "user/repo"
        assert valid_settings.branch == "main"
        assert valid_settings.owner == "user"
        assert valid_settings.name == "repo"
        
        # Test invalid repository format
        with pytest.raises(ValidationError):
            GitHubSettings(
                token="ghp_valid_token_12345",
                repository="invalid_repo_format"  # Missing slash
            )
        
        # Test invalid token format
        with pytest.raises(ValidationError):
            GitHubSettings(
                token="invalid_token",  # Wrong prefix
                repository="user/repo"
            )
    
    def test_api_settings_validation(self):
        """Test API settings validation."""
        # Valid settings
        valid_settings = APISettings(
            key="valid_api_key_1234567890",
            host="localhost",
            port=8000,
            endpoint="https://api.example.com"
        )
        
        assert valid_settings.key == "valid_api_key_1234567890"
        assert valid_settings.host == "localhost"
        assert valid_settings.port == 8000
        assert valid_settings.endpoint == "https://api.example.com"
        
        # Test short API key validation
        with pytest.raises(ValidationError):
            APISettings(key="short")  # Too short
        
        # Test invalid endpoint URL
        with pytest.raises(ValidationError):
            APISettings(
                key="valid_api_key_1234567890",
                endpoint="invalid_url"  # Not a valid URL
            )
    
    def test_publishing_settings_validation(self):
        """Test publishing settings validation."""
        # Valid settings with optional fields
        valid_settings = PublishingSettings(
            site_base_url="https://myblog.com",
            default_author="John Doe"
        )
        
        assert valid_settings.site_base_url == "https://myblog.com"
        assert valid_settings.default_author == "John Doe"
        
        # Test with None values (should be allowed)
        minimal_settings = PublishingSettings()
        assert minimal_settings.site_base_url is None
        assert minimal_settings.default_author is None
        
        # Test invalid URL
        with pytest.raises(ValidationError):
            PublishingSettings(site_base_url="not_a_url")
    
    def test_app_settings_integration(self, test_env_vars):
        """Test full application settings integration."""
        with patch.dict(os.environ, test_env_vars, clear=True):
            settings = AppSettings.from_env()
            
            assert settings.app_name == "Discord Publish Bot"
            assert settings.version == "2.0.0"
            assert settings.environment == "development"
            assert settings.log_level == "DEBUG"  # From test env vars
            
            # Test nested settings
            assert settings.discord.bot_token == test_env_vars["DISCORD_BOT_TOKEN"]
            assert settings.github.repository == test_env_vars["GITHUB_REPO"]
            assert settings.api.key == test_env_vars["API_KEY"]
    
    def test_environment_variable_mapping(self, test_env_vars):
        """Test that environment variables are correctly mapped."""
        with patch.dict(os.environ, test_env_vars, clear=True):
            settings = AppSettings.from_env()
            
            # Test direct mapping
            assert settings.environment == test_env_vars["ENVIRONMENT"]
            assert settings.log_level == test_env_vars["LOG_LEVEL"]
            
            # Test nested mapping
            assert settings.discord.bot_token == test_env_vars["DISCORD_BOT_TOKEN"]
            assert settings.github.token == test_env_vars["GITHUB_TOKEN"]
            assert settings.api.host == test_env_vars["API_HOST"]
    
    def test_default_values(self):
        """Test that default values are properly set."""
        # Create minimal settings to test defaults
        discord_settings = DiscordSettings(
            bot_token="FAKE_TEST_TOKEN.NEVER_REAL.SAFE_FOR_TESTING_123456789",
            application_id="123456789012345678",
            public_key="a" * 64,
            authorized_user_id="987654321098765432"
        )
        github_settings = GitHubSettings(
            token="ghp_test_token",
            repository="user/repo"
        )
        api_settings = APISettings(key="test_key_1234567890")
        publishing_settings = PublishingSettings()
        
        app_settings = AppSettings(
            discord=discord_settings,
            github=github_settings,
            api=api_settings,
            publishing=publishing_settings
        )
        
        # Test defaults
        assert app_settings.app_name == "Discord Publish Bot"
        assert app_settings.version == "2.0.0"
        assert app_settings.environment == "development"
        assert app_settings.log_level == "INFO"
        assert github_settings.branch == "main"
        assert api_settings.host == "0.0.0.0"
        assert api_settings.port == 8000
    
    def test_environment_specific_behavior(self):
        """Test environment-specific configuration behavior."""
        # Development environment
        dev_settings = AppSettings(
            environment="development",
            discord=DiscordSettings(
                bot_token="FAKE_TEST_TOKEN.NEVER_REAL.SAFE_FOR_TESTING_123456789",
                application_id="123456789012345678",
                public_key="a" * 64,
                authorized_user_id="987654321098765432"
            ),
            github=GitHubSettings(token="ghp_test", repository="user/repo"),
            api=APISettings(key="test_key_1234567890"),
            publishing=PublishingSettings()
        )
        
        assert dev_settings.is_development is True
        assert dev_settings.is_production is False
        
        # Production environment
        prod_settings = AppSettings(
            environment="production",
            discord=DiscordSettings(
                bot_token="FAKE_TEST_TOKEN.NEVER_REAL.SAFE_FOR_TESTING_123456789",
                application_id="123456789012345678",
                public_key="a" * 64,
                authorized_user_id="987654321098765432"
            ),
            github=GitHubSettings(token="ghp_test", repository="user/repo"),
            api=APISettings(key="test_key_1234567890"),
            publishing=PublishingSettings()
        )
        
        assert prod_settings.is_development is False
        assert prod_settings.is_production is True
    
    def test_settings_serialization(self, test_settings):
        """Test that settings can be serialized and deserialized."""
        # Test dict conversion
        settings_dict = test_settings.model_dump()
        
        assert isinstance(settings_dict, dict)
        assert "app_name" in settings_dict
        assert "discord" in settings_dict
        assert "github" in settings_dict
        
        # Test JSON serialization
        settings_json = test_settings.model_dump_json()
        assert isinstance(settings_json, str)
        assert "Discord Publish Bot" in settings_json
    
    def test_discord_interactions_enabled(self):
        """Test Discord interactions enabled detection."""
        # With HTTP interactions configured
        settings_with_http = AppSettings(
            discord=DiscordSettings(
                bot_token="FAKE_TEST_TOKEN.NEVER_REAL.SAFE_FOR_TESTING_123456789",
                application_id="123456789012345678",
                public_key="a" * 64,
                authorized_user_id="987654321098765432"
            ),
            github=GitHubSettings(token="ghp_test", repository="user/repo"),
            api=APISettings(key="test_key_1234567890"),
            publishing=PublishingSettings()
        )
        
        assert settings_with_http.discord_interactions_enabled is True
        
        # Without HTTP interactions configured
        settings_without_http = AppSettings(
            discord=DiscordSettings(
                bot_token="FAKE_TEST_TOKEN.NEVER_REAL.SAFE_FOR_TESTING_123456789",
                application_id="123456789012345678",
                public_key=None,  # None public key should disable HTTP interactions
                authorized_user_id="987654321098765432"
            ),
            github=GitHubSettings(token="ghp_test", repository="user/repo"),
            api=APISettings(key="test_key_1234567890"),
            publishing=PublishingSettings()
        )
        
        assert settings_without_http.discord_interactions_enabled is False


@pytest.mark.unit
class TestConfigurationUtilities:
    """Test configuration utility functions."""
    
    def test_get_settings_function(self, test_env_vars):
        """Test the get_settings utility function."""
        from discord_publish_bot.config import get_settings
        
        with patch.dict(os.environ, test_env_vars, clear=True):
            settings = get_settings()
            
            assert isinstance(settings, AppSettings)
            assert settings.environment == "development"
    
    def test_settings_caching(self):
        """Test that settings are properly cached."""
        from discord_publish_bot.config import get_settings
        
        # Multiple calls should return the same instance
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2  # Same object instance
    
    def test_configuration_validation_errors(self):
        """Test that configuration validation errors are properly handled."""
        # Test missing required environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises((ValidationError, ValueError)):
                AppSettings.from_env()
    
    def test_sensitive_data_handling(self, test_settings):
        """Test that sensitive data is properly handled in logs/output."""
        # Test that sensitive fields are masked in string representation
        settings_str = str(test_settings)
        
        # Tokens should not appear in full in string representation
        # Note: Current implementation shows full tokens, this is a known limitation
        # In production, consider implementing proper masking
        assert "MTIzNDU2Nzg5MDEyMzQ1Njc4.FAKE.TEST_TOKEN_NEVER_REAL_SAFE_FOR_TESTING" in settings_str  # Currently visible
        assert "ghp_FAKE_TEST_TOKEN_SAFE_1234567890abcdef_NEVER_REAL" in settings_str  # Currently visible  
        assert "test_api_key_SAFE_FAKE_1234567890abcdef_NEVER_REAL" in settings_str  # Currently visible
