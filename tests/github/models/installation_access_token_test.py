"""Tests for GitHub App installation access token model."""
from datetime import datetime, timedelta, timezone

import pytest

from octomachinery.github.models import GitHubInstallationAccessToken


@pytest.mark.parametrize(
    ('expires_in', 'is_expired'),
    (
        (timedelta(minutes=-1), True),
        (timedelta(seconds=30), True),
        (timedelta(minutes=5), False),
    ),
    ids=('already-expired', 'expiring-within-clock-skew', 'still-valid'),
)
def test_installation_access_token__expired(expires_in, is_expired):
    """Verify that tokens about to expire are treated as expired."""
    expires_at = datetime.now(timezone.utc) + expires_in
    access_token = GitHubInstallationAccessToken(
        token='ghs_test',
        expires_at=int(expires_at.timestamp()),
        permissions={},
        repository_selection='all',
    )
    assert access_token.expired is is_expired
