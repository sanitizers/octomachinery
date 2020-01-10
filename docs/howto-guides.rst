How-to guides
=============


Running a one-off task against GitHub API
-----------------------------------------

Sometimes you need to run a series of queries against GitHub API.
To do this, initialize a token (it's taken from the ``GITHUB_TOKEN`` env
var in the example below), constuct a GitHub API wrapper and you are
good to go.

:py:class:`~octomachinery.github.api.raw_client.RawGitHubAPI` is a
wrapper around interface provided by
:py:class:`~gidgethub.abc.GitHubAPI`, you can find the usage interface
on its documentation page. Don't forget to specify a ``user_agent``
string — it's mandatory!

API calls return native Python :py:class:`dict` or iterable objects.

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

To act as a bot, you should use a special kind of integration with
GitHub — Apps. They are reusable entities in the GitHub Platform
available to be installed into multiple accounts and organizations.

Classic GitHub App requires a web-sever part to be deployed somewhere on
the Internet in order to receive events GitHub Platform would send
there.

Yet, sometimes, you just want to act as a bot without any of that
deployment hustle. You may want to have a ``[bot]`` label next to
comments you'll post via API. You may want to manage rate limits better.
This will allow you to run one-off tasks like batch changes/migrations.

You'll still need to register a GitHub App and install it into the
target user account or organization. You'll also have to specify APIs
you'd like to access using this App.

Then, you'll need to get your App's ID and a private key.

Now, first, specify the App ID, the key path and the target account.
After that, create a
:py:class:`~octomachinery.github.config.app.GitHubAppIntegrationConfig`
instance also specifying app name, version and some URL (these will be
used to generate a ``User-Agent`` HTTP header for API queries).
Then, create a
:py:class:`~octomachinery.github.api.app_client.GitHubApp` instance from
that config. Retrieve a list of places where the App is installed,
filter out the target Installation and get an API client for it.
Finally, use
:py:class:`~octomachinery.github.api.raw_client.RawGitHubAPI` as usual.

.. code:: python

    import asyncio
    import pathlib

    from aiohttp.client import ClientSession

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
            user = await github_api.getitem(
                '/users/{account_name}',
                url_vars={'account_name': target_github_account_or_org},
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

Given that you've already got an instance of
:py:class:`~octomachinery.github.api.raw_client.RawGitHubAPI`
initialized, what's left is to pass ``preview_api_version`` argument
with the appropriate preview API code name when making query to the API
endpoint requiring that.

.. code:: python

    github_api: RawGitHubAPI

    repo_slug = 'sanitizers/octomachinery'
    issue_number = 15

    await github_api.post(
        f'/repos/{repo_slug}/issues/{issue_number}/reactions',
        preview_api_version='squirrel-girl',
        data={'content': 'heart'},
    )
