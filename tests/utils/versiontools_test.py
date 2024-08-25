"""Test suite for version utility helper functions."""

import contextlib
import os
import pathlib
import tempfile

import pytest

from octomachinery.utils.versiontools import get_version_from_scm_tag


@contextlib.contextmanager
def working_directory(path):
    """Change working directory and return back to previous on exit."""
    prev_cwd = pathlib.Path.cwd()
    os.chdir(path)
    try:
        yield path
    finally:
        os.chdir(prev_cwd)


@pytest.fixture
def temporary_working_directory():
    """Create a temporary working directory, cd there and back on exit."""
    with tempfile.TemporaryDirectory() as tmp_git_repo_dir:
        with working_directory(tmp_git_repo_dir) as path:
            yield path


def test_get_version_from_scm_tag_outside_git_repo(
        temporary_working_directory,
):
    """Check that version is unknown outside of Git repo."""
    assert get_version_from_scm_tag() == 'unknown'
