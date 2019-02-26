"""GitHub App/bot configuration."""

from functools import lru_cache

import environ
import envparse

# pylint: disable=relative-beyond-top-level
from ..github.config.app import GitHubAppIntegrationConfig
# pylint: disable=relative-beyond-top-level
from .runtime.config import RuntimeConfig
# pylint: disable=relative-beyond-top-level
from .server.config import WebServerConfig


@environ.config
class BotAppConfig:
    """Bot app config.

    Construct it as follows::
    >>> from octomachinery.app.config import BotAppConfig
    >>> config = BotAppConfig.from_dotenv()  # for dev env
    >>> config = BotAppConfig.from_env()  # for pure env
    >>>
    """

    github = environ.group(GitHubAppIntegrationConfig)
    server = environ.group(WebServerConfig)
    runtime = environ.group(RuntimeConfig)

    @classmethod
    @lru_cache(maxsize=1)
    def from_dotenv(cls):
        """Return an initialized dev config instance.

        Read .env into env vars before that.
        """
        envparse.Env.read_envfile()
        return cls.from_env()

    @classmethod
    @lru_cache(maxsize=1)
    def from_env(cls):
        """Return an initialized config instance."""
        return environ.to_config(cls)
