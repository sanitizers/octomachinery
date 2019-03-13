"""Version tools set."""

from typing import Optional

from setuptools_scm import get_version


def get_version_from_scm_tag(
        *,
        root: str = '.',
        relative_to: Optional[str] = None,
) -> str:
    """Retrieve the version from SCM tag in Git or Hg."""
    try:
        return get_version(root=root, relative_to=relative_to)
    except LookupError:
        return 'unknown'
