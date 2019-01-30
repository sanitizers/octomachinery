"""Config schema for a GitHub App instance details."""
import environ


from ...models.utils import SecretStr
from .utils import USER_AGENT


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

    user_agent = USER_AGENT
