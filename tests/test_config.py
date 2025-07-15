"""Tests for the configuration module."""

import os
from unittest.mock import mock_open, patch

import pytest

from src.ap.config import Config


class TestConfig:
    """Test the Config class."""

    @pytest.fixture
    def mock_config_file(self):
        """Mock config file for testing."""
        config_yaml = """
        default:
          max_actions: 10
          examples_path: src/ap/examples.txt

        openai:
          model: gpt-4.1-nano
          dev_prompt_id: ap/openai-dev

        anthropic:
          model: claude-3-haiku
        """
        return config_yaml.strip()
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_load_config(self, mock_yaml_load, mock_file, mock_config_file):
        """Test that config is loaded correctly."""
        # Setup
        mock_file.return_value.read.return_value = mock_config_file
        mock_yaml_load.return_value = {
            "default": {
                "max_actions": 10,
                "examples_path": "src/ap/examples.txt",
            },
            "openai": {
                "model": "gpt-4.1-nano",
                "dev_prompt_id": "ap/openai-dev",
            },
            "anthropic": {
                "model": "claude-3-haiku",
            },
        }
        
        # Clear any existing instance for testing
        Config._instance = None
        
        # Execute
        config = Config()
        
        # Verify
        assert mock_file.called
        assert mock_yaml_load.called
        assert Config._config == mock_yaml_load.return_value
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_with_driver_specific_value(self, mock_yaml_load, mock_file):
        """Test getting a driver-specific configuration value."""
        # Setup
        mock_yaml_load.return_value = {
            "default": {"max_actions": 10},
            "openai": {"model": "gpt-4.1-nano"},
            "anthropic": {"model": "claude-3-haiku"},
        }
        
        # Clear any existing instance for testing
        Config._instance = None
        Config()
        
        # Default driver is "openai"
        assert Config.get("model") == "gpt-4.1-nano"
        
        # Change driver
        Config.set_driver("anthropic")
        assert Config.get("model") == "claude-3-haiku"
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_with_default_fallback(self, mock_yaml_load, mock_file):
        """Test falling back to default values when driver-specific not found."""
        # Setup
        mock_yaml_load.return_value = {
            "default": {"max_actions": 10},
            "openai": {"model": "gpt-4.1-nano"},
        }
        
        # Clear any existing instance for testing
        Config._instance = None
        Config()
        
        # Should fall back to default
        assert Config.get("max_actions") == 10
        
        # Change driver, should still use default
        Config.set_driver("openai")
        assert Config.get("max_actions") == 10
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_available_drivers(self, mock_yaml_load, mock_file):
        """Test getting list of available drivers."""
        # Setup
        mock_yaml_load.return_value = {
            "default": {"max_actions": 10},
            "openai": {"model": "gpt-4.1-nano"},
            "anthropic": {"model": "claude-3-haiku"},
            "ollama": {"model": "llama3"},
        }
        
        # Clear any existing instance for testing
        Config._instance = None
        Config()
        
        # Get available drivers
        drivers = Config.get_available_drivers()
        assert "openai" in drivers
        assert "anthropic" in drivers
        assert "ollama" in drivers
        assert "default" not in drivers
