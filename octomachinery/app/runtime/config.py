"""The application runtime configuration."""
import attr
import environ

from .utils import detect_env_mode


@environ.config  # pylint: disable=too-few-public-methods
class RuntimeConfig:
    """Config of runtime env."""

    debug = environ.bool_var(False, name='DEBUG')
    env = environ.var(
        'prod', name='ENV',
        validator=attr.validators.in_(('dev', 'prod')),
    )
    mode = environ.var(
        'auto', name='OCTOMACHINERY_APP_MODE',
        converter=lambda val: detect_env_mode() if val == 'auto' else val,
        validator=attr.validators.in_(('app', 'action')),
    )

    app_name = environ.var(None, name='OCTOMACHINERY_APP_NAME')
    app_version = environ.var(None, name='OCTOMACHINERY_APP_VERSION')
    app_url = environ.var(None, name='OCTOMACHINERY_APP_URL')

    @property
    def user_agent(self):  # noqa: D401
        """The User-Agent value to use when hitting GitHub API."""
        return f'{self.app_name}/{self.app_version} (+{self.app_url})'
