"""Configuration module for the application.

This module provides a centralized configuration system that supports multiple
LLM drivers (openai, anthropic, ollama, etc.) and allows runtime selection
of which driver to use.
"""

import os
from string import Template
from typing import Any

import yaml


class Config:
    """Configuration system with driver-based settings.

    This class provides access to configuration values with a driver-specific
    hierarchy. When requesting a configuration value, it first checks the
    active driver's configuration, then falls back to default values.

    Example:
        # Set the active driver
        Config.set_driver("anthropic")

        # Get a configuration value
        model = Config.get("model")  # Returns the anthropic-specific model
    """

    _instance = None
    _config: dict[str, Any] = {}
    _active_driver: str = "openai"  # Default driver

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._load_config()
        return cls._instance

    @classmethod
    def _load_config(cls) -> None:
        """Load the configuration from YAML."""
        config_path = os.environ.get("AP_CONFIG_PATH", "config.yaml")
        try:
            with open(config_path) as file:
                cls._config = yaml.safe_load(file)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            cls._config = {}

    @classmethod
    def set_driver(cls, driver_name: str) -> None:
        """Set the active driver name.

        Args:
            driver_name: The name of the driver to use (e.g., "openai", "anthropic")

        Raises:
            ValueError: If the driver name doesn't exist in the configuration
        """
        if driver_name not in cls._config and driver_name != "default":
            raise ValueError(f"Unknown driver: {driver_name}")
        cls._active_driver = driver_name

    @classmethod
    def get_active_driver(cls) -> str:
        """Get the name of the currently active driver.

        Returns:
            The name of the active driver
        """
        return cls._active_driver

    @classmethod
    def get(cls, key: str, default: Any | None = None) -> Any:
        """Get a configuration value, checking driver settings first, then defaults.

        Args:
            key: The configuration key to look up
            default: The default value to return if the key is not found

        Returns:
            The configuration value or the default
        """
        # Try to get from active driver
        if cls._active_driver in cls._config and key in cls._config[cls._active_driver]:
            return cls._config[cls._active_driver][key]

        # Fall back to defaults
        if "default" in cls._config and key in cls._config["default"]:
            return cls._config["default"][key]

        return default

    @classmethod
    def get_available_drivers(cls) -> list[str]:
        """Get list of available driver names from config.

        Returns:
            List of driver names, excluding the "default" section
        """
        return [name for name in cls._config.keys() if name != "default"]

    @classmethod
    def get_prompt(cls, driver_name: str, prompt_type: str, **kwargs: Any) -> str:
        """Load and format a prompt template for a specific driver.

        Args:
            driver_name: The name of the driver (e.g., "openai", "anthropic")
            prompt_type: The type of prompt ("system", "user", "examples")
            **kwargs: Variables to substitute in the prompt template

        Returns:
            The formatted prompt string
        """
        prompt_path = f"prompts/{driver_name}/{prompt_type}.txt"
        try:
            with open(prompt_path) as f:
                template = f.read().strip()

            # Examples files don't need templating, return as-is
            if prompt_type == "examples":
                return template

            # Use Template instead of format to avoid brace conflicts
            template_obj = Template(template)
            return template_obj.safe_substitute(**kwargs)
        except Exception as e:
            raise ValueError(f"Error loading prompt {prompt_path}: {e}") from e
