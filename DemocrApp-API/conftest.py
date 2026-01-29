"""
Pytest configuration for DemocrApp API tests.

Configures the test environment to use InMemoryChannelLayer
instead of RedisChannelLayer, eliminating the Redis dependency.
"""
import pytest
from django.conf import settings


@pytest.fixture(scope='session', autouse=True)
def configure_test_channel_layer(django_db_setup, django_db_blocker):
    """
    Override CHANNEL_LAYERS to use InMemoryChannelLayer for all tests.

    This runs once per test session and ensures WebSocket tests work
    without requiring a Redis server. The in-memory layer is suitable
    for single-process testing and provides the same API as Redis.

    Scope: session - Runs once before all tests
    Autouse: True - Automatically applied to all tests
    """
    with django_db_blocker.unblock():
        settings.CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels.layers.InMemoryChannelLayer",
            }
        }
