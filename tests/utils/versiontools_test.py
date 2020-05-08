"""Test suite for version utility helper functions."""
# pylint: disable=redefined-outer-name

import contextlib
import os
import pathlib
import subprocess
import tempfile

import pytest
import setuptools_scm.version

from octomachinery.utils.versiontools import (
    cut_local_version_on_upload,
    get_self_version,
    get_version_from_scm_tag,
)


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


@pytest.fixture
def git_cmd():
    """Provide a Git command helper."""
    git_cmd = ('git', )
    # pylint: disable=unexpected-keyword-arg
    return lambda *args: subprocess.check_output(git_cmd + args, text=True)


@pytest.fixture
def git_init_cmd(git_cmd):
    """Provide a Git init command helper."""
    return lambda *args: git_cmd(*(('init', ) + args))


@pytest.fixture
def git_config_cmd(git_cmd):
    """Provide a Git config command helper."""
    return lambda *args: git_cmd(*(('config', '--local') + args))


@pytest.fixture
def git_commit_cmd(git_cmd):
    """Provide a Git commit command helper."""
    return lambda *args: git_cmd(*(('commit', '--allow-empty') + args))


@pytest.fixture
def git_tag_cmd(git_cmd):
    """Provide a Git tag command helper."""
    return lambda *args: git_cmd(*(('tag', ) + args))


@pytest.fixture
def tmp_git_repo(temporary_working_directory, git_config_cmd, git_init_cmd):
    """Create a temporary Git repo and cd there, coming back upon cleanup."""
    git_init_cmd()
    git_config_cmd('user.name', 'Test User')
    git_config_cmd('user.email', 'test.user@example.com')
    yield temporary_working_directory


def test_get_self_version_in_git_repo(
        monkeypatch,
        tmp_git_repo,  # pylint: disable=unused-argument
        git_cmd, git_commit_cmd, git_tag_cmd,
):
    """Check that get_self_version works properly in existing Git repo."""
    assert get_self_version() == '0.1.dev0'

    git_commit_cmd('-m', 'Test commit')
    git_tag_cmd('v1.3.9')
    assert get_self_version() == '1.3.9'

    git_commit_cmd('-m', 'Test commit 2')
    head_sha1_hash = git_cmd('rev-parse', '--short', 'HEAD').strip()
    assert get_self_version() == f'1.3.10.dev1+g{head_sha1_hash}'

    with monkeypatch.context() as mp_ctx:
        mp_ctx.setenv('PYPI_UPLOAD', 'true')
        assert get_self_version() == '1.3.10.dev1'


def test_get_self_version_outside_git_repo(
        temporary_working_directory,  # pylint: disable=unused-argument
):
    """Check that version is unknown outside of Git repo."""
    assert get_self_version() == 'unknown'


def test_cut_local_version_on_upload(
        monkeypatch,
        tmp_git_repo,  # pylint: disable=unused-argument
):
    """Test that PEP440 local version isn't emitted when upload."""
    scm_node = 'gfe99188'
    ver = setuptools_scm.version.ScmVersion(
        'v1.1.4',
        distance=3, node='gfe99188',
        dirty=False, branch='master',
    )
    assert cut_local_version_on_upload(ver) == f'+{scm_node}'

    with monkeypatch.context() as mp_ctx:
        mp_ctx.setenv('PYPI_UPLOAD', 'true')
        assert cut_local_version_on_upload(ver) == ''


def test_get_version_from_scm_tag_in_git_repo(
        monkeypatch,
        tmp_git_repo,  # pylint: disable=unused-argument
        git_cmd, git_commit_cmd, git_tag_cmd,
):
    """Check that get_version_from_scm_tag works properly in Git repo."""
    assert get_self_version() == '0.1.dev0'

    git_commit_cmd('-m', 'Test commit')
    git_tag_cmd('v1.3.9')
    assert get_version_from_scm_tag() == '1.3.9'

    git_commit_cmd('-m', 'Test commit 2')
    head_sha1_hash = git_cmd('rev-parse', '--short', 'HEAD').strip()
    assert get_version_from_scm_tag() == f'1.3.10.dev1+g{head_sha1_hash}'

    with monkeypatch.context() as mp_ctx:
        mp_ctx.setenv('PYPI_UPLOAD', 'true')
        assert get_version_from_scm_tag() == f'1.3.10.dev1+g{head_sha1_hash}'


def test_get_version_from_scm_tag_outside_git_repo(
        temporary_working_directory,  # pylint: disable=unused-argument
):
    """Check that version is unknown outside of Git repo."""
    assert get_version_from_scm_tag() == 'unknown'
