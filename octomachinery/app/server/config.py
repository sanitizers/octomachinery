"""The web-server configuration."""

import environ


@environ.config
class WebServerConfig:  # pylint: disable=too-few-public-methods
    """Config of a web-server."""

    host = environ.var('0.0.0.0', name='HOST')
    port = environ.var(8080, name='PORT', converter=int)
