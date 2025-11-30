import os.path

from app.core.config import Settings

def test_settings_root_url():
    settings = Settings()
    root_url = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    assert settings.root_url == root_url