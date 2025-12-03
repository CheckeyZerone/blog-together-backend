import os.path
from typing import TextIO
from unittest import TestCase

from app.core.config import Settings


class SettingsTest(TestCase):
    settings = Settings()

    def test_settings_root_url(self):
        settings = self.settings
        root_url = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        print(f'root_url = "{settings.root_url}"')
        assert settings.root_url == root_url

    def test_settings_database_url(self):
        settings = self.settings
        database_url = settings.database_url
        print(f'database_url = "{database_url}"')
        if isinstance(database_url, str):
            assert database_url.startswith("sqlite+aiosqlite://")
        else:
            assert database_url.port is None

    def test_settings_output_dir(self):
        settings = self.settings
        output_path, _ = settings.logger_config
        print(f'output_path = "{output_path}"')
        print(f'is_dir = "{os.path.isdir(output_path)}"')
        assert isinstance(output_path, str) or isinstance(output_path, TextIO)
        assert output_path.endswith(".log")