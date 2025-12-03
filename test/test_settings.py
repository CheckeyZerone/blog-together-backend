import os.path
from unittest import TestCase

from app.core.config import Settings


class SettingsTest(TestCase):
    settings = Settings()

    def test_settings_root_url(self):
        settings = self.settings
        root_url = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        print(f'target_root_url = "{root_url}"')
        assert settings.root_url == root_url

    def test_settings_database_url(self):
        settings = self.settings
        database_url = settings.database_url
        print(f'target_database_url = "{database_url}"')
        if isinstance(database_url, str):
            assert database_url.startswith("sqlite+aiosqlite://")
        else:
            assert database_url.port is None