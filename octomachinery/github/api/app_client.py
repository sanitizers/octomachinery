"""GitHub App API client."""

from collections import defaultdict
from contextlib import AbstractAsyncContextManager
import logging
import types
import typing

from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientConnectorError
import attr
from gidgethub.sansio import Event

# pylint: disable=relative-beyond-top-level
from ...utils.asynctools import (
    amap, dict_to_kwargs_cb,
)
# pylint: disable=relative-beyond-top-level
from ..config.app import GitHubAppIntegrationConfig
# pylint: disable=relative-beyond-top-level
from ..entities.app_installation import GitHubAppInstallation
# pylint: disable=relative-beyond-top-level
from ..models import GitHubAppInstallation as GitHubAppInstallationModel
from .raw_client import RawGitHubAPI
from .tokens import GitHubJWTToken


logger = logging.getLogger(__name__)


GH_INSTALL_EVENTS = {'integration_installation', 'installation'}


@attr.dataclass
class GitHubApp(AbstractAsyncContextManager):
    """GitHub API wrapper."""

    _config: GitHubAppIntegrationConfig
    _http_session: ClientSession

    def __attrs_post_init__(self):
        """Initialize installations store."""
        # pylint: disable=attribute-defined-outside-init
        self._installations = defaultdict(dict)

    async def event_from_request(self, request):
        """Get an event object out of HTTP request."""
        event = Event.from_http(
            request.headers,
            await request.read(),
            secret=self._config.webhook_secret,
        )
        await self.pre_process_webhook_event(event)
        return event

    async def pre_process_webhook_event(self, event):
        """Get an event object out of HTTP request."""
        action = event.data.get('action')
        if event.event in GH_INSTALL_EVENTS and action == 'created':
            await self.add_installation(event)

    async def __aenter__(self) -> 'GitHubApp':
        """Store all installations data before starting."""
        # pylint: disable=relative-beyond-top-level,import-outside-toplevel
        from ...app.runtime.context import RUNTIME_CONTEXT

        RUNTIME_CONTEXT.github_app = self
        # pylint: disable=attribute-defined-outside-init
        try:
            self._installations = await self.get_installations()
        except ClientConnectorError as client_error:
            logger.info('It looks like the GitHub API is offline...')
            logger.error(
                'The following error has happened while trying to grab '
                'installations list: %s',
                client_error,
            )
            self._installations = defaultdict(dict)

        logger.info('This GitHub App is installed into:')
        # pylint: disable=protected-access
        for install_id, install_val in self._installations.items():
            logger.info(
                '* Installation id %s (expires at %s, installed to %s)',
                install_id,
                install_val._token.expires_at,
                install_val._metadata.account['login'],
            )

        return self

    async def __aexit__(
            self,
            exc_type: typing.Optional[typing.Type[BaseException]],
            exc_val: typing.Optional[BaseException],
            exc_tb: typing.Optional[types.TracebackType],
    ) -> typing.Optional[bool]:
        """Wipe out the installation store."""
        # pylint: disable=attribute-defined-outside-init
        self._installations = defaultdict(dict)

    @property
    def gh_jwt(self):
        """Generate app's JSON Web Token, valid for 60 seconds."""
        token = self._config.private_key.make_jwt_for(
            app_id=self._config.app_id,
        )
        return GitHubJWTToken(token)

    @property
    def api_client(self):  # noqa: D401
        """The GitHub App client with an async CM interface."""
        return RawGitHubAPI(
            token=self.gh_jwt,
            session=self._http_session,
            user_agent=self._config.user_agent,
        )

    async def add_installation(self, event):
        """Retrieve an installation creds from store."""
        install = event.data['installation']
        install_id = install['id']
        self._installations[install_id] = GitHubAppInstallation(
            GitHubAppInstallationModel(**install),
            self,
        )
        await self._installations[install_id].retrieve_access_token()
        return self._installations[install_id]

    async def get_installation(self, event):
        """Retrieve an installation creds from store."""
        # pylint: disable=relative-beyond-top-level,import-outside-toplevel
        from ...app.runtime.context import RUNTIME_CONTEXT

        if event.event == 'ping':
            return GitHubAppInstallation(None, self)

        install_id = event.data['installation']['id']
        app_installation = self._installations.get(install_id)

        if app_installation is not None:
            await app_installation.retrieve_access_token()

        # pylint: disable=assigning-non-slot
        RUNTIME_CONTEXT.app_installation = (
            app_installation
        )

        return app_installation

    async def get_installations(self):
        """Retrieve all installations with access tokens via API."""
        installations = defaultdict(dict)
        async for install in amap(
                dict_to_kwargs_cb(GitHubAppInstallationModel),
                self.api_client.getiter(
                    '/app/installations',
                    preview_api_version='machine-man',
                ),
        ):
            installations[install.id] = GitHubAppInstallation(
                install, self,
            )
            await installations[install.id].retrieve_access_token()
        return installations
