"""GitHub App API client."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, Iterable

from aiohttp.client import ClientSession
from aiohttp.client_exceptions import ClientConnectorError

import attr
import sentry_sdk

# pylint: disable=relative-beyond-top-level
from ...routing import WEBHOOK_EVENTS_ROUTER
# pylint: disable=relative-beyond-top-level
from ...utils.asynctools import amap, dict_to_kwargs_cb
# pylint: disable=relative-beyond-top-level
from ..config.app import GitHubAppIntegrationConfig
# pylint: disable=relative-beyond-top-level
from ..entities.app_installation import GitHubAppInstallation
# pylint: disable=relative-beyond-top-level
from ..models import (
    GitHubAppInstallation as GitHubAppInstallationModel,
    GitHubInstallationAccessToken,
)
# pylint: disable=relative-beyond-top-level
from ..models.events import GitHubEvent
from .raw_client import RawGitHubAPI
from .tokens import GitHubJWTToken


if TYPE_CHECKING:
    # pylint: disable=relative-beyond-top-level
    from ...routing.abc import OctomachineryRouterBase


logger = logging.getLogger(__name__)


GH_INSTALL_EVENTS = {'integration_installation', 'installation'}


@attr.dataclass
class GitHubApp:  # TODO: have ctx here?
    """GitHub API wrapper."""

    _config: GitHubAppIntegrationConfig
    _http_session: ClientSession
    _event_routers: Iterable[OctomachineryRouterBase] = attr.ib(
        default={WEBHOOK_EVENTS_ROUTER},
        converter=frozenset,
    )

    def __attrs_post_init__(self) -> None:
        """Initialize the Sentry SDK library."""
        # NOTE: Under the hood, it will set up the DSN from `SENTRY_DSN`
        # NOTE: env var. We don't need to care about it not existing as
        # NOTE: Sentry SDK helpers don't fail loudly and if not
        # NOTE: configured, it'll be ignored.
        # FIXME:  # pylint: disable=fixme
        sentry_sdk.init()  # pylint: disable=abstract-class-instantiated

    async def dispatch_event(self, github_event: GitHubEvent) -> Iterable[Any]:
        """Dispatch ``github_event`` into the embedded routers."""
        return await github_event.dispatch_via(
            *self._event_routers,  # pylint: disable=not-an-iterable
        )

    async def log_installs_list(self) -> None:
        """Store all installations data before starting."""
        try:
            installations = await self.get_installations()
        except ClientConnectorError as client_error:
            logger.info('It looks like the GitHub API is offline...')
            logger.error(
                'The following error has happened while trying to grab '
                'installations list: %s',
                client_error,
            )
            return

        logger.info('This GitHub App is installed into:')
        # pylint: disable=protected-access
        for install_id, install_val in installations.items():
            logger.info(
                '* Installation id %s (installed to %s)',
                install_id,
                install_val._metadata.account['login'],
            )

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

    async def get_token_for(
            self,
            installation_id: int,
    ) -> GitHubInstallationAccessToken:
        """Return an access token for the given installation."""
        return GitHubInstallationAccessToken(**(
            await self.api_client.post(
                '/app/installations/{installation_id}/access_tokens',
                url_vars={'installation_id': installation_id},
                data=b'',
                preview_api_version='machine-man',
            )
        ))

    async def get_installation(self, event):
        """Retrieve an installation creds from store."""
        if 'installation' not in event.payload:
            raise LookupError('This event occurred outside of an installation')

        install_id = event.payload['installation']['id']
        return await self.get_installation_by_id(install_id)

    async def get_installation_by_id(self, install_id):
        """Retrieve an installation with access tokens via API."""
        return GitHubAppInstallation(
            GitHubAppInstallationModel(
                **(
                    await self.api_client.getitem(
                        '/app/installations/{installation_id}',
                        url_vars={'installation_id': install_id},
                        preview_api_version='machine-man',
                    )
                ),
            ),
            self,
        )

    async def get_installations(self):
        """Retrieve all installations with access tokens via API."""
        installations: Dict[
                int, GitHubAppInstallation,
        ] = defaultdict(dict)  # type: ignore[arg-type]
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
        return installations
