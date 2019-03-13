"""Config schema for a GitHub App instance details."""
import environ


# pylint: disable=relative-beyond-top-level
from ...app.runtime.context import RUNTIME_CONTEXT
# pylint: disable=relative-beyond-top-level
from ..models.utils import SecretStr


@environ.config  # pylint: disable=too-few-public-methods
class GitHubAppIntegrationConfig:
    """GitHub App auth related config."""

    app_id = environ.var(name='GITHUB_APP_IDENTIFIER')
    private_key = environ.var(
        name='GITHUB_PRIVATE_KEY',
        converter=SecretStr,
    )
    webhook_secret = environ.var(
        None, name='GITHUB_WEBHOOK_SECRET',
        converter=lambda s: SecretStr(s) if s is not None else s,
    )

    @property
    def user_agent(self):  # noqa: D401
        """The User-Agent value to use when hitting GitHub API."""
        name = RUNTIME_CONTEXT.config.runtime.app_name
        version = RUNTIME_CONTEXT.config.runtime.app_version
        url = RUNTIME_CONTEXT.config.runtime.app_url
        return f'{name}/{version} (+{url})'
