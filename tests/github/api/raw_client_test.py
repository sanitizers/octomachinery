"""Tests for the low-level GitHub API client."""

import contextlib

from aiohttp.client_exceptions import (
    ClientConnectorError, ClientOSError, ServerDisconnectedError,
)

import pytest

from octomachinery.github.api.raw_client import RawGitHubAPI
from octomachinery.github.api.tokens import GitHubOAuthToken


class FakeResponse:  # pylint: disable=too-few-public-methods
    """A successful aiohttp response stub."""

    status = 200
    headers = {'content-type': 'application/json; charset=utf-8'}

    async def read(self):
        """Return an empty JSON object."""
        return b'{}'


class FlakySession:  # pylint: disable=too-few-public-methods
    """An aiohttp session stub raising given errors before succeeding."""

    def __init__(self, *errors):
        """Remember the errors to raise on consecutive requests."""
        self.errors = list(errors)
        self.requested_methods = []

    @contextlib.asynccontextmanager
    # pylint: disable-next=unused-argument
    async def request(self, method, url, *, headers, data):
        """Raise the next queued error or respond successfully."""
        self.requested_methods.append(method)
        if self.errors:
            raise self.errors.pop(0)
        yield FakeResponse()


def make_client(monkeypatch, session):
    """Create a client over ``session`` that records retry delays."""
    client = RawGitHubAPI(GitHubOAuthToken('token'), session=session)
    client.retry_delays = []

    async def record_sleep(seconds):
        client.retry_delays.append(seconds)
    monkeypatch.setattr(client, 'sleep', record_sleep)
    return client


@pytest.mark.parametrize(
    'transient_error',
    (
        ServerDisconnectedError(),
        ClientOSError(104, 'Connection reset by peer'),
    ),
)
@pytest.mark.anyio
async def test_idempotent_request_retried(monkeypatch, transient_error):
    """Test that a dropped idempotent request is sent again."""
    session = FlakySession(transient_error, transient_error)
    client = make_client(monkeypatch, session)

    assert await client.getitem('/app') == {}
    assert session.requested_methods == ['GET', 'GET', 'GET']
    assert client.retry_delays == [0.5, 1]


@pytest.mark.anyio
async def test_idempotent_request_retries_exhausted(monkeypatch):
    """Test that the last error propagates after all attempts fail."""
    session = FlakySession(*(ServerDisconnectedError() for _ in range(3)))
    client = make_client(monkeypatch, session)

    with pytest.raises(ServerDisconnectedError):
        await client.getitem('/app')
    assert session.requested_methods == ['GET', 'GET', 'GET']


@pytest.mark.anyio
async def test_non_idempotent_request_not_retried(monkeypatch):
    """Test that a dropped POST is not repeated."""
    session = FlakySession(ServerDisconnectedError())
    client = make_client(monkeypatch, session)

    with pytest.raises(ServerDisconnectedError):
        await client.post('/repos/org/repo/issues', data={'title': 'x'})
    assert session.requested_methods == ['POST']


@pytest.mark.anyio
async def test_connector_error_not_retried(monkeypatch):
    """Test that failing to establish a connection is not retried."""
    session = FlakySession(
        ClientConnectorError(
            connection_key=None, os_error=OSError(111, 'Refused'),
        ),
    )
    client = make_client(monkeypatch, session)

    with pytest.raises(ClientConnectorError):
        await client.getitem('/app')
    assert session.requested_methods == ['GET']
