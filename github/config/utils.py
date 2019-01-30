"""Helper vars with app version specs."""


import setuptools_scm


APP_NAME = 'Chronographer-Bot'
try:
    APP_VERSION = setuptools_scm.get_version()
except LookupError:
    APP_VERSION = 'unknown'
APP_URL = 'https://github.com/apps/chronographer'
USER_AGENT = f'{APP_NAME}/{APP_VERSION} (+{APP_URL})'
