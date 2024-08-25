"""Version tools set."""

from typing import Callable, Optional, Union

from setuptools_scm import get_version
from setuptools_scm.version import ScmVersion


def get_version_from_scm_tag(
        *,
        root: str = '.',
        relative_to: Optional[str] = None,
        local_scheme: Union[
            Callable[[ScmVersion], str], str,
        ] = 'node-and-date',
) -> str:
    """Retrieve the version from SCM tag in Git or Hg."""
    try:
        return get_version(
            root=root,
            relative_to=relative_to,
            local_scheme=local_scheme,
        )
    except LookupError:
        return 'unknown'
