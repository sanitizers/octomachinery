"""GitHub App/bot configuration."""

from functools import lru_cache
import os
from typing import Optional

import environ
import envparse

# pylint: disable=relative-beyond-top-level
from ..github.config.app import GitHubAppIntegrationConfig
# pylint: disable=relative-beyond-top-level
from .action.config import GitHubActionConfig
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
    action = environ.group(GitHubActionConfig)
    server = environ.group(WebServerConfig)
    runtime = environ.group(RuntimeConfig)

    @classmethod
    @lru_cache(maxsize=1)
    def from_dotenv(
            cls,
            *,
            app_name: Optional[str] = None,
            app_version: Optional[str] = None,
            app_url: Optional[str] = None,
    ):
        """Return an initialized dev config instance.

        Read .env into env vars before that.
        """
        envparse.Env.read_envfile(
            '.env',  # Making it relative to CWD, relative to caller if None
        )
        return cls.from_env(
            app_name=app_name,
            app_version=app_version,
            app_url=app_url,
        )

    @classmethod
    @lru_cache(maxsize=1)
    def from_env(
            cls,
            *,
            app_name: Optional[str] = None,
            app_version: Optional[str] = None,
            app_url: Optional[str] = None,
    ):
        """Return an initialized config instance."""
        env_vars = dict(os.environ)
        if app_name is not None:
            env_vars['OCTOMACHINERY_APP_NAME'] = app_name
        if app_version is not None:
            env_vars['OCTOMACHINERY_APP_VERSION'] = app_version
        if app_url is not None:
            env_vars['OCTOMACHINERY_APP_URL'] = app_url
        return environ.to_config(cls, environ=env_vars)
