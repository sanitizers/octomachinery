"""Config schema for a GitHub App instance details."""
import environ


# pylint: disable=relative-beyond-top-level
from ..models.private_key import GitHubPrivateKey
# pylint: disable=relative-beyond-top-level
from ..models.utils import SecretStr


def validate_is_not_none_if_app(
        self,  # pylint: disable=unused-argument
        attr, value,
):
    """Forbid None value in a GitHub App context."""
    # pylint: disable=relative-beyond-top-level,import-outside-toplevel
    from ...app.runtime.utils import detect_env_mode

    if value is None and detect_env_mode() == 'app':
        raise ValueError(
            f'GitHub App must provide a proper value for {attr!r}',
        )


def validate_fingerprint_if_present(instance, _attribute, value):
    r"""Validate that the private key matches the fingerprint pin.

    :raises ValueError: if the fingerprint pin is present \
                        but doesn't match the private key
    """
    if not value:
        return

    if instance.private_key.matches_fingerprint(value):
        return

    raise ValueError(
        'The private key provided (with a fingerprint of '
        f'{instance.private_key.fingerprint!s}) does not match '
        f'the pinned fingerprint value of {value!s}',
    )


@environ.config
class GitHubAppIntegrationConfig:  # pylint: disable=too-few-public-methods
    """GitHub App auth related config."""

    app_id = environ.var(
        None,
        name='GITHUB_APP_IDENTIFIER',
        validator=validate_is_not_none_if_app,
    )
    private_key = environ.var(
        None,
        name='GITHUB_PRIVATE_KEY',
        converter=lambda raw_data:
        None if raw_data is None else GitHubPrivateKey(raw_data.encode()),
        validator=validate_is_not_none_if_app,
    )
    private_key_fingerprint = environ.var(
        None,
        name='GITHUB_PRIVATE_KEY_FINGERPRINT',
        validator=validate_fingerprint_if_present,
    )
    webhook_secret = environ.var(
        None, name='GITHUB_WEBHOOK_SECRET',
        converter=lambda s: SecretStr(s) if s is not None else s,
    )

    app_name = environ.var(None, name='OCTOMACHINERY_APP_NAME')
    app_version = environ.var(None, name='OCTOMACHINERY_APP_VERSION')
    app_url = environ.var(None, name='OCTOMACHINERY_APP_URL')

    @property
    def user_agent(self):  # noqa: D401
        """The User-Agent value to use when hitting GitHub API."""
        return f'{self.app_name}/{self.app_version} (+{self.app_url})'
