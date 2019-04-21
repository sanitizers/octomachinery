#! /usr/bin/env python3
"""Octomachinery CLI entrypoint."""

import asyncio
from functools import wraps
import importlib
from io import TextIOWrapper
import os
import pathlib
from typing import Any, Callable, Iterable, Iterator, Set

from aiohttp.client import ClientSession
import click

# pylint: disable=relative-beyond-top-level
from ..app.config import BotAppConfig
# pylint: disable=relative-beyond-top-level
from ..app.routing.abc import OctomachineryRouterBase
# pylint: disable=relative-beyond-top-level
from ..app.routing.webhooks_dispatcher import route_github_event
# pylint: disable=relative-beyond-top-level
from ..github.api.app_client import GitHubApp
# pylint: disable=relative-beyond-top-level
from ..github.entities.action import GitHubAction
# pylint: disable=relative-beyond-top-level
from ..github.models.events import GitHubEvent
# pylint: disable=relative-beyond-top-level
from ..github.models.events import GitHubWebhookEvent


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:  # pylint: disable=unused-argument
    """Click CLI base."""


def run_async(orig_async_func: Callable[..., Any]):
    """Run the given async func in event loop."""
    @wraps(orig_async_func)
    def func_wrapper(*args: Any, **kwargs: Any):
        return asyncio.run(orig_async_func(*args, **kwargs))
    return func_wrapper


@cli.command()
@click.option('--event', '-e', prompt=False, type=str)
@click.option(
    '--payload-path', '-p',
    'event_payload',
    prompt=True,
    type=click.File(mode='r'),
)
@click.option('--token', '-t', prompt=False, type=str)
@click.option('--app', '-a', prompt=False, type=int)
@click.option('--private-key', '-P', prompt=False, type=click.File(mode='r'))
@click.option('--entrypoint-module', '-m', prompt=False, type=str)
@click.option(
    '--event-router', '-r',
    'event_routers',
    multiple=True,
    prompt=False,
    type=str,
)
@click.pass_context
@run_async
async def receive(  # pylint: disable=too-many-arguments,too-many-locals
        ctx: click.Context,
        event: str, event_payload: TextIOWrapper,
        token: str,
        app: int, private_key: TextIOWrapper,
        entrypoint_module: str,
        event_routers: Iterable[str],
) -> None:
    """Webhook event receive command."""
    app_missing_private_key = app is not None and not private_key
    if app_missing_private_key:
        ctx.fail(click.style('App requires a private key', fg='red'))

    creds_present = token or (app and private_key)
    if not creds_present:
        ctx.fail(click.style('GitHub auth credentials are missing', fg='red'))

    too_many_creds_present = token and (app or private_key)
    if too_many_creds_present:
        ctx.fail(
            click.style(
                'Please choose between a token or '
                'an app id with a private key',
                fg='red',
            ),
        )

    make_event = GitHubEvent if app is None else GitHubWebhookEvent
    try:
        gh_event = make_event.from_fixture_fd(event_payload, event=event)
    except ValueError as val_err:
        ctx.fail(click.style(str(val_err), fg='red'))

    os.environ.update(get_extra_env_vars(gh_event, token, app, private_key))

    try:
        target_routers = set(
            load_event_routers(entrypoint_module, event_routers),
        )
    except AttributeError as attr_err:
        ctx.fail(
            click.style(
                f'Could not find an event router: {attr_err!s}',
                fg='red',
            ),
        )
    except ImportError as imp_err:
        ctx.fail(
            click.style(f'Could not load a module: {imp_err!s}', fg='red'),
        )

    config = BotAppConfig.from_dotenv()
    gh_app_kwargs = {'config': config.github}
    make_gh_app = GitHubApp
    if app is None:
        make_gh_app = GitHubAction
        gh_app_kwargs['metadata'] = config.action
    async with ClientSession() as http_client_session:
        github_app = make_gh_app(
            http_session=http_client_session,
            event_routers=target_routers or None,
            **gh_app_kwargs,
        )
        await route_github_event(
            github_event=gh_event, github_app=github_app,
        )

    click.echo(
        click.style(
            f'Finished processing {gh_event.name!s} event!',
            fg='green',
        ),
    )


def load_event_routers(
        entrypoint_module: str = None,
        event_routers: Set[str] = frozenset(),
) -> Iterator[OctomachineryRouterBase]:
    """Yield event routers from strings."""
    if entrypoint_module is not None:
        importlib.import_module(entrypoint_module)

    for router_path in event_routers:
        target_sep = ':' if ':' in router_path else '.'
        module_path, _sep, target_router = router_path.rpartition(target_sep)
        yield getattr(importlib.import_module(module_path), target_router)


def get_extra_env_vars(
        gh_event: GitHubEvent, token: str, app: int,
        private_key: TextIOWrapper,
) -> dict:
    """Construct additional env vars for App or Action processing."""
    env = {}

    if app is not None:
        env['OCTOMACHINERY_APP_MODE'] = 'app'

        env['GITHUB_APP_IDENTIFIER'] = str(app)
        env['GITHUB_PRIVATE_KEY'] = private_key.read()
        return env

    env['OCTOMACHINERY_APP_MODE'] = 'action'

    env['GITHUB_ACTION'] = 'Fake CLI Action'
    env['GITHUB_ACTOR'] = gh_event.payload.get('sender', {}).get('login', '')
    env['GITHUB_EVENT_NAME'] = gh_event.name
    env['GITHUB_WORKSPACE'] = str(pathlib.Path('.').resolve())
    env['GITHUB_SHA'] = gh_event.payload.get('head_commit', {}).get('id', '')
    env['GITHUB_REF'] = gh_event.payload.get('ref', '')
    env['GITHUB_REPOSITORY'] = (
        gh_event.payload.
        get('repository', {}).
        get('full_name', '')
    )
    env['GITHUB_TOKEN'] = token
    env['GITHUB_WORKFLOW'] = 'Fake CLI Workflow'
    env['GITHUB_EVENT_PATH'] = '/dev/null'

    return env


def main():
    """CLI entrypoint."""
    kwargs = {
        'prog_name': f'python3 -m {__package__}',
    } if __name__ == '__main__' else {}

    return cli(  # pylint: disable=unexpected-keyword-arg
        auto_envvar_prefix='OCTOMACHINERY_CLI_',
        obj={},
        **kwargs,
    )


__name__ == '__main__' and main()  # pylint: disable=expression-not-assigned
