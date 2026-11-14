"""Test the Probot-compatible repository config lookup."""

from base64 import b64encode
from http import HTTPStatus
from types import SimpleNamespace

import gidgethub

import pytest

from octomachinery.app.runtime.installation_utils import (
    get_installation_config,
)
from octomachinery.runtime.context import RUNTIME_CONTEXT


REPO_CONFIG_URL = '/repos/octocat/hello-world/contents/.github/config.yml'
ORG_CONFIG_URL = '/repos/octocat/.github/contents/.github/config.yml'
SETTINGS_CONFIG_URL = '/repos/octocat/settings/contents/.github/config.yml'


class _FakeGitHubAPI:  # pylint: disable=too-few-public-methods
    """A GitHub API client stub serving the repository contents."""

    def __init__(self, repo_files):
        self._repo_files = repo_files
        self.requested_urls = []

    async def getitem(self, url):
        """Return a file from the contents API or a 404 error."""
        self.requested_urls.append(url)
        try:
            file_contents = self._repo_files[url]
        except KeyError:
            raise gidgethub.BadRequest(HTTPStatus.NOT_FOUND) from None

        return {
            'encoding': 'base64',
            'content': b64encode(file_contents.encode()).decode(),
        }


def _set_up_runtime_context(
        repo_files,
        repo_slug='octocat/hello-world',
        is_github_action=False,
):
    """Populate the runtime context with an event and an API client."""
    github_api = _FakeGitHubAPI(repo_files)
    RUNTIME_CONTEXT.IS_GITHUB_ACTION = is_github_action
    RUNTIME_CONTEXT.app_installation_client = github_api
    RUNTIME_CONTEXT.github_event = SimpleNamespace(
        payload={'repository': {'full_name': repo_slug}},
    )
    return github_api


@pytest.fixture
def anyio_backend():
    """Run the async tests under asyncio."""
    return 'asyncio'


@pytest.mark.anyio
async def test_repo_config_takes_precedence():
    """Test that the repository config doesn't need the org one."""
    github_api = _set_up_runtime_context({
        REPO_CONFIG_URL: 'greeting: hello\n',
        ORG_CONFIG_URL: 'greeting: hi\nfarewell: bye\n',
    })

    assert await get_installation_config() == {'greeting': 'hello'}
    assert github_api.requested_urls == [REPO_CONFIG_URL]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ('repo_slug', 'repo_files', 'expected_config', 'expected_urls'),
    (
        pytest.param(
            'octocat/hello-world',
            {ORG_CONFIG_URL: 'greeting: hi\n'},
            {'greeting': 'hi'},
            [REPO_CONFIG_URL, ORG_CONFIG_URL],
            id='org-config',
        ),
        pytest.param(
            'octocat/hello-world',
            {},
            {},
            [REPO_CONFIG_URL, ORG_CONFIG_URL],
            id='no-config',
        ),
        pytest.param(
            'octocat/.github',
            {},
            {},
            [ORG_CONFIG_URL],
            id='no-config-in-org-repo',
        ),
    ),
)
async def test_org_config_fallback(
        repo_slug, repo_files,
        expected_config, expected_urls,
):
    """Test that a missing repository config falls back to the org one."""
    github_api = _set_up_runtime_context(repo_files, repo_slug=repo_slug)

    assert await get_installation_config() == expected_config
    assert github_api.requested_urls == expected_urls


@pytest.mark.anyio
async def test_ref_only_applies_to_event_repo():
    """Test that the org config is read from its default branch."""
    github_api = _set_up_runtime_context({ORG_CONFIG_URL: 'greeting: hi\n'})

    assert await get_installation_config(ref='feature') == {'greeting': 'hi'}
    assert github_api.requested_urls == [
        f'{REPO_CONFIG_URL}?ref=feature',
        ORG_CONFIG_URL,
    ]


@pytest.mark.anyio
@pytest.mark.parametrize(
    ('repo_files', 'expected_config'),
    (
        pytest.param(
            {
                REPO_CONFIG_URL: '_extends: settings\ngreeting: hello\n',
                SETTINGS_CONFIG_URL: (
                    '_extends: other/shared:.github/base.yaml\n'
                    'greeting: hi\nfarewell: bye\n'
                ),
                '/repos/other/shared/contents/.github/base.yaml': (
                    'farewell: ciao\nlabels: [bug]\n'
                ),
            },
            {'greeting': 'hello', 'farewell': 'bye', 'labels': ['bug']},
            id='extends-chain',
        ),
        pytest.param(
            {
                ORG_CONFIG_URL: '_extends: settings\ngreeting: hi\n',
                SETTINGS_CONFIG_URL: 'farewell: bye\n',
            },
            {'greeting': 'hi', 'farewell': 'bye'},
            id='org-config-extends',
        ),
        pytest.param(
            {REPO_CONFIG_URL: '_extends: missing\ngreeting: hello\n'},
            {'greeting': 'hello'},
            id='missing-base-config',
        ),
        pytest.param(
            {REPO_CONFIG_URL: '_extends:\ngreeting: hello\n'},
            {'greeting': 'hello'},
            id='empty-extends',
        ),
        pytest.param({REPO_CONFIG_URL: ''}, {}, id='empty-config'),
    ),
)
async def test_extends(repo_files, expected_config):
    """Test that configs inherit the keys of the configs they extend."""
    _set_up_runtime_context(repo_files)

    assert await get_installation_config() == expected_config


@pytest.mark.anyio
@pytest.mark.parametrize(
    ('repo_files', 'expected_error'),
    (
        pytest.param(
            {REPO_CONFIG_URL: '_extends: octocat/settings/extra\n'},
            r"^Invalid `_extends` value 'octocat/settings/extra' in "
            r'octocat/hello-world:\.github/config\.yml$',
            id='too-many-slashes',
        ),
        pytest.param(
            {REPO_CONFIG_URL: '_extends: settings:config.json\n'},
            '^Invalid `_extends` value',
            id='non-yaml-path',
        ),
        pytest.param(
            {REPO_CONFIG_URL: '_extends: [settings]\n'},
            '^Invalid `_extends` value',
            id='non-string',
        ),
        pytest.param(
            {
                REPO_CONFIG_URL: '_extends: settings\n',
                SETTINGS_CONFIG_URL: '_extends: hello-world\n',
            },
            r"^Recursive `_extends` value 'hello-world' in "
            r'octocat/settings:\.github/config\.yml$',
            id='recursion',
        ),
        pytest.param(
            {REPO_CONFIG_URL: '- greeting\n'},
            r'^The config in \.github/config\.yml is not a mapping$',
            id='non-mapping',
        ),
    ),
)
async def test_invalid_config(repo_files, expected_error):
    """Test that malformed configs are reported."""
    _set_up_runtime_context(repo_files)

    with pytest.raises(ValueError, match=expected_error):
        await get_installation_config()


@pytest.mark.anyio
async def test_github_action_reads_checkout(monkeypatch, tmp_path):
    """Test that Actions don't need the event repository for local config."""
    (tmp_path / '.github').mkdir()
    (tmp_path / '.github' / 'config.yml').write_text('greeting: hello\n')
    monkeypatch.chdir(tmp_path)
    github_api = _set_up_runtime_context({}, is_github_action=True)
    RUNTIME_CONTEXT.github_event = SimpleNamespace()

    assert await get_installation_config() == {'greeting': 'hello'}
    assert not github_api.requested_urls


@pytest.mark.anyio
async def test_github_action_falls_back_to_org_config(monkeypatch, tmp_path):
    """Test that Actions without a local config read the org one."""
    monkeypatch.chdir(tmp_path)
    github_api = _set_up_runtime_context(
        {ORG_CONFIG_URL: 'greeting: hi\n'},
        is_github_action=True,
    )

    assert await get_installation_config() == {'greeting': 'hi'}
    assert github_api.requested_urls == [ORG_CONFIG_URL]
