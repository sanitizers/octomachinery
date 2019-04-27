Getting started
===============

The documentation isn't ready yet so I suggest you going through the
:doc:`How-to create a GitHub Bot tutorial <why-github-bots>`
which should give you basic understanding of GitHub Apps and how to
write them with octomachinery.

Runtime pre-requisites
----------------------

* Python 3.7+ as octomachinery relies on :py:mod:`contextvars` which
  doesn't have a backport.
* GitHub App credentials and GitHub Action events are supplied via
  environment variables. They are also loaded from a ``.env`` file if it
  exists in a development environment.

  .. warning::

     Be aware that some tools in your environment may conflict with
     autoloading vars from a ``.env`` file. It is recommended to disable
     those. One example of such tool is `Pipenv`_.

     .. _`Pipenv`:
        https://pipenv.readthedocs.io/en/latest/advanced/
        #automatic-loading-of-env

  For the production deployments, please use a way of supplying env vars
  via tools provided by the application orchestration software of your
  choice.
