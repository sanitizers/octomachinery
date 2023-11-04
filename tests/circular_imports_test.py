"""Tests for circular imports in all local packages and modules.

This ensures all internal packages can be imported right away without
any need to import some other module before doing so.

This module is based on an idea that pytest uses for self-testing:
* https://github.com/pytest-dev/pytest/blob/d18c75b/testing/test_meta.py
* https://twitter.com/codewithanthony/status/1229445110510735361
"""
import os
import pkgutil
import subprocess
import sys
from itertools import chain
from pathlib import Path

import pytest

import octomachinery


def _find_all_importables(pkg):
    """Find all importables in the project.

    Return them in order.
    """
    return sorted(
        set(
            chain.from_iterable(
                _discover_path_importables(Path(p), pkg.__name__)
                for p in pkg.__path__
            ),
        ),
    )


def _discover_path_importables(pkg_pth, pkg_name):
    """Yield all importables under a given path and package."""
    for dir_path, _d, file_names in os.walk(pkg_pth):
        pkg_dir_path = Path(dir_path)

        if pkg_dir_path.parts[-1] == '__pycache__':
            continue

        if all(Path(_).suffix != '.py' for _ in file_names):
            continue

        rel_pt = pkg_dir_path.relative_to(pkg_pth)
        pkg_pref = '.'.join((pkg_name,) + rel_pt.parts)
        yield from (
            pkg_path
            for _, pkg_path, _ in pkgutil.walk_packages(
                (str(pkg_dir_path),), prefix=f'{pkg_pref}.',
            )
        )


@pytest.mark.parametrize(
    'import_path',
    _find_all_importables(octomachinery),
)
def test_no_warnings(import_path):
    """Verify that exploding importables doesn't explode.

    This is seeking for any import errors including ones caused
    by circular imports.
    """
    imp_cmd = (
        sys.executable,
        '-W', 'error',

        # NOTE: These are necessary for `tox -e old-deps`:
        '-W', "ignore:Using or importing the ABCs from 'collections' instead "
        "of from 'collections.abc' is deprecated since "
        'Python 3.3, and in 3.10 it will stop working:'
        'DeprecationWarning:jwt.api_jwt',
        '-W', "ignore:Using or importing the ABCs from 'collections' instead "
        "of from 'collections.abc' is deprecated since "
        'Python 3.3, and in 3.9 it will stop working:'
        'DeprecationWarning:jwt.api_jwt',
        # NOTE: This looks like the line above but has a typo
        # NOTE: (a whitespace is missing):
        '-W', "ignore:Using or importing the ABCs from 'collections' instead "
        "of from 'collections.abc' is deprecated since "
        'Python 3.3,and in 3.9 it will stop working:'
        'DeprecationWarning:jwt.api_jwt',

        # NOTE: Triggered by the `octomachinery.utils.versiontools`
        # NOTE: command via `tox -e old-deps`:
        '-W', 'ignore:pkg_resources is deprecated as an API:'
        'DeprecationWarning:pkg_resources',

        # NOTE: Triggered by the `octomachinery.utils.versiontools`
        # NOTE: command via `tox -e old-deps`:
        '-W', 'ignore:The distutils package is deprecated and slated for '
        'removal in Python 3.12. Use setuptools or check PEP 632 for '
        'potential alternatives:'
        'DeprecationWarning:',

        # NOTE: Triggered by the `octomachinery.utils.versiontools`
        # NOTE: command via `tox -e old-deps`:
        '-W', "ignore:module 'sre_constants' is deprecated:"
        'DeprecationWarning:',

        # NOTE: Triggered by the `octomachinery.utils.versiontools`
        # NOTE: command via `tox -e old-deps`:
        '-W', 'ignore:_SixMetaPathImporter.exec_module() not found; '
        'falling back to load_module():ImportWarning:',

        # NOTE: Triggered by the `octomachinery.utils.versiontools`
        # NOTE: command via `tox -e old-deps`:
        '-W', 'ignore:_SixMetaPathImporter.find_spec() not found; '
        'falling back to find_module():ImportWarning:',

        # NOTE: Triggered by the `octomachinery.utils.versiontools`
        # NOTE: command via `tox -e old-deps`:
        '-W', 'ignore:VendorImporter.exec_module() not found; '
        'falling back to load_module():ImportWarning:',

        # NOTE: Triggered by the `octomachinery.utils.versiontools`
        # NOTE: command via `tox -e old-deps`:
        '-W', 'ignore:VendorImporter.find_spec() not found; '
        'falling back to find_module():ImportWarning:',

        # NOTE: Triggered by the `octomachinery.routing.routers`
        # NOTE: command via `tox -e old-deps`:
        '-W', "ignore:'cgi' is deprecated and slated for removal "
        'in Python 3.13:'
        'DeprecationWarning:gidgethub.sansio',

        '-W', 'ignore:"@coroutine" decorator is deprecated '
        'since Python 3.8, use "async def" instead:'
        'DeprecationWarning:aiohttp.helpers',
        '-c', f'import {import_path!s}',
    )

    subprocess.check_call(imp_cmd)
