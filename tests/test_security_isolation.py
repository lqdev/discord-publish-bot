"""
Security validation tests to ensure no production credentials are used in tests.
"""

import os
import pytest


class TestSecurityIsolation:
    """Test class to validate security isolation is working."""
    
    def test_no_production_credentials_in_environment(self):
        """Verify that no production credentials are present during testing."""
        # Check for patterns that might indicate real credentials
        dangerous_patterns = [
            ("DISCORD_BOT_TOKEN", ["FAKE_TOKENMzU1NDkyNzAwOTkwNQ"]),  # Start of real token
            ("GITHUB_TOKEN", ["ghp_FAKE4W2rwp0WycBUp76grs48jLSeorh"]),  # Start of real token
            ("DISCORD_USER_ID", ["727687304596160593"]),  # Real user ID
            ("GITHUB_REPO", ["example-dev/luisquintanilla.me"]),  # Real repo
        ]
        
        for env_var, dangerous_values in dangerous_patterns:
            current_value = os.environ.get(env_var, "")
            for dangerous_value in dangerous_values:
                assert dangerous_value not in current_value, (
                    f"SECURITY VIOLATION: Production credential detected!\n"
                    f"Environment variable '{env_var}' contains production data: {dangerous_value}\n"
                    f"Current value: {current_value}\n"
                    f"This should never happen during testing."
                )
    
    def test_environment_is_test_mode(self):
        """Verify that test environment is properly set."""
        # Environment should be development (valid value) for tests
        assert os.environ.get("ENVIRONMENT") == "development"
    
    def test_fake_credentials_are_used(self):
        """Verify that only fake credentials are present during testing."""
        # Check that we have obviously fake values
        discord_token = os.environ.get("DISCORD_BOT_TOKEN", "")
        github_token = os.environ.get("GITHUB_TOKEN", "")
        github_repo = os.environ.get("GITHUB_REPO", "")
        
        assert "FAKE" in discord_token or "TEST" in discord_token
        assert "FAKE" in github_token or "TEST" in github_token  
        assert "test-user" in github_repo or "test-repo" in github_repo
    
    def test_sensitive_env_vars_are_safe(self):
        """Verify all sensitive environment variables contain only safe test values."""
        sensitive_vars = [
            "DISCORD_BOT_TOKEN",
            "GITHUB_TOKEN", 
            "API_KEY"
        ]
        
        for var_name in sensitive_vars:
            value = os.environ.get(var_name, "")
            if value:  # Only check if variable is set
                assert any(safe_indicator in value.upper() for safe_indicator in ["FAKE", "TEST", "NEVER"]), (
                    f"Environment variable {var_name} does not appear to be a safe test value: {value}"
                )
