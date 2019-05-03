.. image:: https://img.shields.io/pypi/v/octomachinery.svg?logo=Python&logoColor=white
   :target: https://pypi.org/project/octomachinery
   :alt: octomachinery @ PyPI

.. DO-NOT-REMOVE-docs-badges-END

.. image:: https://img.shields.io/travis/com/sanitizers/octomachinery/master.svg?label=Linux%20builds&logo=travis&logoColor=white
   :target: https://travis-ci.com/sanitizers/octomachinery
   :alt: Travis CI build status

.. image:: https://img.shields.io/readthedocs/octomachinery/latest.svg?logo=Read%20The%20Docs&logoColor=white
   :target: https://docs.octomachinery.dev/en/latest/?badge=latest
   :alt: Documentation Status

octomachinery: Bots Without Boilerplate
=======================================

Invisible engine driving octobot machines. Simple, yet powerful.

Web-site @ https://octomachinery.dev. Stay tuned!

.. DO-NOT-REMOVE-docs-intro-START

**How-to create a GitHub Bot tutorial** is ready for preview
@ `tutorial.octomachinery.dev <https://tutorial.octomachinery.dev/en/latest/>`_

Elevator pitch
--------------

Here's how you 👍 a just-created comment:

.. code:: python

    from octomachinery.app.routing import process_event_actions
    from octomachinery.app.routing.decorators import process_webhook_payload
    from octomachinery.app.runtime.context import RUNTIME_CONTEXT
    from octomachinery.app.server.runner import run as run_app


    @process_event_actions('issue_comment', {'created'})
    @process_webhook_payload
    async def on_comment(
            *,
            action, issue, comment,
            repository=None, sender=None,
            installation=None,
            assignee=None, changes=None,
    ):
        github_api = RUNTIME_CONTEXT.app_installation_client
        comment_reactions_api_url = f'{comment["url"]}/reactions'
        await github_api.post(
            comment_reactions_api_url,
            preview_api_version='squirrel-girl',
            data={'content': '+1'},
        )


    run_app(
        name='Thumbs-Up-Bot',
        version='1.0.0',
        url='https://github.com/apps/thuuuuuuuuuuuuuumbs-uuuuuuuuuuuup',
    )

Prerequisites
-------------

Python 3.7+

License
-------

The source code and the documentation in this project are released under
the `GPL v3 license`_.

.. _`GPL v3 license`:
   https://github.com/sanitizers/octomachinery/blob/master/LICENSE
