.. image:: https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner-direct.svg
   :target: https://github.com/vshymanskyy/StandWithUkraine/blob/main/docs/README.md
   :alt: SWUbanner

.. image:: https://img.shields.io/pypi/v/octomachinery.svg?logo=Python&logoColor=white
   :target: https://pypi.org/project/octomachinery
   :alt: octomachinery @ PyPI

.. image:: https://tidelift.com/badges/package/pypi/octomachinery
   :target: https://tidelift.com/subscription/pkg/pypi-octomachinery?utm_source=pypi-octomachinery&utm_medium=readme
   :alt: octomachinery is available as part of the Tidelift Subscription

.. image:: https://github.com/sanitizers/octomachinery/actions/workflows/ci-cd.yml/badge.svg?event=push
   :target: https://github.com/sanitizers/octomachinery/actions/workflows/ci-cd.yml?query=event:push
   :alt: GitHub Actions CI/CD workflows status

.. image:: https://img.shields.io/matrix/octomachinery:matrix.org?label=Discuss%20on%20Matrix%20at%20%23octomachinery%3Amatrix.org&logo=matrix&server_fqdn=matrix.org&style=flat
   :target: https://matrix.to/#/%23octomachinery:matrix.org
   :alt: Matrix Room — #octomachinery:matrix.org

.. image:: https://img.shields.io/matrix/pyba:matrix.org?label=Discuss%20on%20Matrix%20at%20%23pyba%3Amatrix.org&logo=matrix&server_fqdn=matrix.org&style=flat
   :target: https://matrix.to/#/%23pyba:matrix.org
   :alt: Matrix Space — #pyba:matrix.org

.. DO-NOT-REMOVE-docs-badges-END

.. image:: https://img.shields.io/readthedocs/octomachinery/latest.svg?logo=Read%20The%20Docs&logoColor=white
   :target: https://docs.octomachinery.dev/en/latest/?badge=latest
   :alt: Documentation Status

octomachinery: Bots Without Boilerplate
=======================================

Invisible engine driving octobot machines. Simple, yet powerful.

Web-site @ https://octomachinery.dev. Stay tuned!

.. DO-NOT-REMOVE-docs-intro-START

**How-to create a GitHub Bot tutorial** is ready for preview
@ `tutorial.octomachinery.dev
<https://tutorial.octomachinery.dev/en/latest/>`_

Elevator pitch
--------------

Here's how you 👍 a just-created comment:

.. code:: python

    from octomachinery.app.server.runner import run as run_app
    from octomachinery.routing import process_event_actions
    from octomachinery.routing.decorators import process_webhook_payload
    from octomachinery.runtime.context import RUNTIME_CONTEXT


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

Contribute octomachinery
------------------------

**Want to add something to upstream?** Feel free to submit a PR or file
an issue if unsure.
Note that PR is more likely to be accepted if it includes tests and
detailed description helping maintainers to understand it better 🎉

Oh, and be pythonic, please 🐍

**Don't know how?** Check out `How to Contribute to Open Source
<https://opensource.guide/how-to-contribute/>`_ article by GitHub 🚀

License
-------

The source code and the documentation in this project are released under
the `GPL v3 license`_.

.. _`GPL v3 license`:
   https://github.com/sanitizers/octomachinery/blob/master/LICENSE

For Enterprise
--------------

octomachinery is available as part of the Tidelift Subscription.

The octomachinery maintainers and the maintainers of thousands of other packages
are working with Tidelift to deliver one enterprise subscription that covers
all of the open source you use.

`Learn more <https://tidelift.com/subscription/pkg/pypi-octomachinery?utm_source=pypi-octomachinery&utm_medium=referral&utm_campaign=github>`_.
