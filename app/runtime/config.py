"""The application runtime configuration."""
import attr
import environ


@environ.config  # pylint: disable=too-few-public-methods
class RuntimeConfig:
    """Config of runtime env."""

    debug = environ.bool_var(False, name='DEBUG')
    env = environ.var(
        'prod', name='ENV',
        validator=attr.validators.in_(('dev', 'prod')),
    )
