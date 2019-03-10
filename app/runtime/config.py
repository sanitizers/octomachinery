"""The application runtime configuration."""
import attr
import environ


@environ.config  # pylint: disable=too-few-public-methods
class RuntimeConfig:
    """Config of runtime env."""

    debug = environ.bool_var(False, name='DEBUG')
    env_mode = environ.var(
        'prod', name='ENV_MODE',
        validator=attr.validators.in_(('dev', 'prod')),
    )

    app_name = environ.var(None, name='OCTOMACHINERY_APP_NAME')
    app_version = environ.var(None, name='OCTOMACHINERY_APP_VERSION')
    app_url = environ.var(None, name='OCTOMACHINERY_APP_URL')
