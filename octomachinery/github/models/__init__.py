"""Models representing objects in GitHub API."""

from datetime import datetime, timezone
import typing

import attr

from .utils import convert_datetime, SecretStr


@attr.dataclass
class GitHubAppInstallation:  # pylint: disable=too-few-public-methods
    """
    Represents a GitHub App installed into a user or an organization profile.

    It has its own ID for installation which is a unique combo of an app
    and a profile (user or org).
    """

    id: int = attr.ib(converter=int)
    """Installation ID."""
    app_id: int = attr.ib(converter=int)
    """GitHub App ID."""
    app_slug: str = attr.ib(converter=str)
    """GitHub App slug."""

    # FIXME: unignore once this is solved:  # pylint: disable=fixme
    # https://github.com/python/mypy/issues/6172#issuecomment-515718727
    created_at: datetime = attr.ib(converter=convert_datetime)  # type: ignore
    """Date time when the installation has been installed."""
    updated_at: datetime = attr.ib(converter=convert_datetime)  # type: ignore
    """Date time when the installation was last updated."""

    account: typing.Dict[str, typing.Any]
    """Target account (org or user) where this GitHub App is installed into."""
    events: typing.List[str]
    """List of webhook events the app will be receiving from the account."""
    permissions: typing.Dict[str, typing.Any]
    """Permission levels of access to API endpoints types."""
    repository_selection: str = attr.ib(converter=str)
    """Repository selection mode."""
    single_file_name: typing.Optional[str]
    """File path the GitHub app controls."""

    target_id: int = attr.ib(converter=int)
    """Target account ID where this GitHub App is installed into."""
    target_type: str = attr.ib(
        validator=attr.validators.in_(('Organization', 'User')),
    )
    """Target account type where this GitHub App is installed into."""

    access_tokens_url: str = attr.ib(converter=str)
    """API endpoint to retrieve access token from."""
    html_url: str = attr.ib(converter=str)
    """URL for controlling the GitHub App Installation."""
    repositories_url: str = attr.ib(converter=str)
    """API endpoint listing repositories accissible by this Installation."""

    suspended_at: typing.Optional[str]
    suspended_by: typing.Optional[str]


@attr.dataclass
class GitHubInstallationAccessToken:  # pylint: disable=too-few-public-methods
    """Struct for installation access token response from GitHub API."""

    token: SecretStr = attr.ib(converter=SecretStr)
    """Access token for GitHub App Installation."""
    expires_at: datetime = attr.ib(converter=convert_datetime)  # type: ignore
    """Token expiration time."""
    permissions: typing.Dict[str, str]
    """Permission levels of access to API endpoints types."""
    repository_selection: str = attr.ib(converter=str)
    """Repository selection mode."""
    repositories: typing.List[typing.Dict[str, typing.Any]] = attr.ib(
        default=[],
        converter=list,
    )
    """List of accessible repositories."""

    @property
    def expired(self):
        """Check whether this token has expired already."""
        return datetime.now(timezone.utc) > self.expires_at
