from __future__ import annotations

from copy import deepcopy
from typing import Any

from ..database import Database
from ..security import SecretStore
from .outbound_urls import normalize_connector_url


DEFAULT_SETTINGS: dict[str, Any] = {
    "grocy": {
        "enabled": False,
        "url": "http://grocy:80",
        "api_key": "",
    },
    "provider": {
        "type": "cortecs",
        "base_url": "https://api.cortecs.ai/v1",
        "model": "",
        "api_key": "",
    },
    "privacy": {
        "delete_image_after_analysis": False,
        "retention_days": 7,
    },
}


class SettingsService:
    DB_KEY = "connections.v1"

    def __init__(self, database: Database, secret_store: SecretStore) -> None:
        self.database = database
        self.secret_store = secret_store

    def get_private(self) -> dict[str, Any]:
        stored = self.secret_store.decrypt_json(self.database.get_setting(self.DB_KEY))
        result = deepcopy(DEFAULT_SETTINGS)
        stored_grocy = stored.get("grocy", {})
        for section in ("grocy", "provider", "privacy"):
            result[section].update(stored.get(section, {}))
        if "enabled" not in stored_grocy:
            result["grocy"]["enabled"] = bool(stored_grocy.get("api_key"))
        return result

    def get_public(self) -> dict[str, Any]:
        private = self.get_private()
        public = deepcopy(private)
        grocy_key = public["grocy"].pop("api_key", "")
        provider_key = public["provider"].pop("api_key", "")
        public["grocy"]["api_key_configured"] = bool(grocy_key)
        public["provider"]["api_key_configured"] = bool(provider_key)
        return public

    def save(self, incoming: dict[str, Any]) -> dict[str, Any]:
        current = self.get_private()
        for section in ("grocy", "provider", "privacy"):
            current[section].update(incoming.get(section, {}))

        if incoming.get("grocy", {}).get("api_key") is None:
            current["grocy"]["api_key"] = self.get_private()["grocy"].get("api_key", "")
        if incoming.get("provider", {}).get("api_key") is None:
            current["provider"]["api_key"] = self.get_private()["provider"].get(
                "api_key", ""
            )

        current["grocy"]["url"] = normalize_connector_url(current["grocy"]["url"])
        current["provider"]["base_url"] = normalize_connector_url(
            current["provider"]["base_url"],
            require_https=current["provider"]["type"]
            in {"cortecs", "openai", "openrouter", "anthropic"},
        )
        encrypted = self.secret_store.encrypt_json(current)
        self.database.put_setting(self.DB_KEY, encrypted)
        return self.get_public()
