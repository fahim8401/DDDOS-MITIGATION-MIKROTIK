"""
Configuration management for mt-ddos-manager
Loads from config.yml and overrides from environment variables
"""

import os
import yaml
from typing import Dict, Any


class Config:
    """Configuration manager"""

    def __init__(self, config_path: str = "config.yml"):
        self.config_path = config_path
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config = {}

        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f) or {}

        # Override with environment variables
        # Format: MT_DDOS_<SECTION>_<KEY>
        for key, value in os.environ.items():
            if key.startswith('MT_DDOS_'):
                parts = key[8:].lower().split('_')
                if len(parts) >= 2:
                    section = parts[0]
                    subkey = '_'.join(parts[1:])
                    if section not in config:
                        config[section] = {}
                    config[section][subkey] = self._parse_env_value(value)

        return config

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value"""
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)