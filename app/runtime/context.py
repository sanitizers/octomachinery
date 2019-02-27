"""The globally accessible context vars mapping.

It is supposed to be used as follows:

>>> from octomachinery.app.runtime.context import RUNTIME_CONTEXT

Or shorter:
>>> from octomachinery.app import RUNTIME_CONTEXT
"""
from .utils import _ContextMap


RUNTIME_CONTEXT = _ContextMap(
    app_installation='app installation',
    app_installation_client='app installation client',
    config='config context',
    github_app='github app',
)
