How-to guides
=============


Running a one-off task against GitHub API
-----------------------------------------

.. code:: python

    import asyncio
    import os

    from octomachinery.github.api.tokens import GitHubOAuthToken
    from octomachinery.github.api.raw_client import RawGitHubAPI


    async def main():
        access_token = GitHubOAuthToken(os.environ["GITHUB_TOKEN"])
        github_api = RawGitHubAPI(access_token, user_agent='webknjaz')
        await github_api.post(
            '/repos/mariatta/strange-relationship/issues',
            data={
                'title': 'We got a problem',
                'body': 'Use more emoji!',
            },
        )


    asyncio.run(main())


Authenticating as a bot (GitHub App)
------------------------------------

.. code:: python

    import asyncio
    import pathlib

    from octomachinery.github.api.app_client import GitHubApp
    from octomachinery.github.config.app import GitHubAppIntegrationConfig


    target_github_account_or_org = 'webknjaz'  # where the app is installed to

    github_app_id = 12345
    github_app_private_key_path = pathlib.Path(
        '~/Downloads/star-wars.2011-05-04.private-key.pem',
    ).expanduser().resolve()

    github_app_config = GitHubAppIntegrationConfig(
        app_id=github_app_id,
        private_key=github_app_private_key_path.read_text(),

        app_name='MyGitHubClient',
        app_version='1.0',
        app_url='https://awesome-app.dev',
    )
    github_app = GitHubApp(github_app_config)


    async def get_github_client(account):
        github_app_installations = await github_app.get_installations()
        target_github_app_installation = next(  # find the one
            (
                i for n, i in github_app_installations.items()
                if i._metadata.account['login'] == account
            ),
            None,
        )
        return target_github_app_installation.get_github_api_client()


    async def main():
        github_api = await get_github_client(target_github_account_or_org)
        user = await github_api.getitem(
            f'/users/{target_github_account_or_org}',
        )
        print(f'User found: {user["login"]}')
        print(f'Rate limit stats: {github_api.rate_limit!s}')


    asyncio.run(main())


Making API queries against preview endpoints
--------------------------------------------

Endpoints with stable interfaces in GitHub API are easy to hit. But some
are marked as preview API. For those, GitHub requires special Accept
headers to be passed along with a normal HTTP request. The exact strings
are documented at https://developers.github.com under specific endpoint
sections in their description.

Given that you've already got an instance of :py:class:`RawGitHubAPI
<octomachinery.github.api.raw_client.RawGitHubAPI>` initialized, what's
left is to pass ``preview_api_version`` argument with the appropriate
preview API code name when making query to the API endpoint requiring
that.

.. code:: python

    github_api: RawGitHubAPI

    repo_slug = 'sanitizers/octomachinery'
    issue_number = 15

    await github_api.post(
        f'/repos/{repo_slug}/issues/{issue_number}/reactions',
        preview_api_version='squirrel-girl',
        data={'content': 'heart'},
    )
