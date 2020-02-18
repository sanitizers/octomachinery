"""The globally accessible context vars mapping.

It is supposed to be used as follows:

>>> from octomachinery.runtime.context import RUNTIME_CONTEXT

Or shorter:
>>> from octomachinery import RUNTIME_CONTEXT
"""
# pylint: disable=relative-beyond-top-level
from .utils import _ContextMap


RUNTIME_CONTEXT = _ContextMap(
    app_installation='app installation',
    app_installation_client='app installation client',
    config='config context',
    github_app='github app',
    github_event='GitHub Event',
    IS_GITHUB_ACTION='Is GitHub Action',
    IS_GITHUB_APP='Is GitHub App',
)
