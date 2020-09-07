import asyncio
import pathlib

from aiohttp.client import ClientSession

from octomachinery.github.api.app_client import GitHubApp
from octomachinery.github.config.app import GitHubAppIntegrationConfig


target_github_account_or_org = 'sanitizers'  # where the app is installed to

github_app_id = 28012
github_app_private_key_path = pathlib.Path(
    '~/Downloads/diactoros.2019-03-30.private-key.pem',
).expanduser().resolve()

github_app_config = GitHubAppIntegrationConfig(
    app_id=github_app_id,
    private_key=github_app_private_key_path.read_text(),

    app_name='MyGitHubClient',
    app_version='1.0',
    app_url='https://awesome-app.dev',
)


async def get_github_client(github_app, account):
    github_app_installations = await github_app.get_installations()
    target_github_app_installation = next(  # find the one
        (
            i for n, i in github_app_installations.items()
            if i._metadata.account['login'] == account
        ),
        None,
    )
    return target_github_app_installation.api_client


async def main():
    async with ClientSession() as http_session:
        github_app = GitHubApp(github_app_config, http_session)
        github_api = await get_github_client(
            github_app, target_github_account_or_org,
        )
        org = await github_api.getitem(
            '/orgs/{account_name}',
            url_vars={'account_name': target_github_account_or_org},
        )
    print(f'Org found: {org["login"]}')
    print(f'Rate limit stats: {github_api.rate_limit!s}')


asyncio.run(main())
