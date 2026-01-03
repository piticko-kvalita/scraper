"""Settings manager for storing user configuration."""
import json
from pathlib import Path
from typing import Dict, Optional
import config

class SettingsManager:
    """Manage application settings."""
    
    def __init__(self):
        self.settings_path = config.SETTINGS_PATH
        self.settings = self._load_settings()
    
    def _load_settings(self) -> Dict:
        """Load settings from file."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        # Default settings
        return {
            "openrouter_api_key": "",
            "ai_enabled": False,
            "auto_gather_interval": 24,
            "quality_threshold": 0.3,
        }
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set a setting value."""
        self.settings[key] = value
        self._save_settings()
    
    def get_all(self) -> Dict:
        """Get all settings (excluding sensitive data for display)."""
        safe_settings = self.settings.copy()
        if "openrouter_api_key" in safe_settings and safe_settings["openrouter_api_key"]:
            # Mask API key for display
            key = safe_settings["openrouter_api_key"]
            safe_settings["openrouter_api_key_masked"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
            safe_settings["openrouter_api_key_set"] = True
        else:
            safe_settings["openrouter_api_key_set"] = False
        
        # Don't send actual key to frontend
        if "openrouter_api_key" in safe_settings:
            del safe_settings["openrouter_api_key"]
        
        return safe_settings
    
    def update_multiple(self, updates: Dict):
        """Update multiple settings at once."""
        for key, value in updates.items():
            self.settings[key] = value
        self._save_settings()
    
    def get_openrouter_key(self) -> str:
        """Get OpenRouter API key."""
        return self.settings.get("openrouter_api_key", "")
    
    def is_ai_enabled(self) -> bool:
        """Check if AI features are enabled."""
        has_key = bool(self.get_openrouter_key())
        enabled = self.settings.get("ai_enabled", False)
        return has_key and enabled


# Global settings manager instance
_settings_manager = None

def get_settings_manager() -> SettingsManager:
    """Get or create the global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
