"""GitHub App runtime context helpers."""

import logging
import os


logger = logging.getLogger(__name__)


def detect_env_mode():
    """Figure out whether we're under GitHub Action environment."""
    for var_suffix in {
            'WORKFLOW',
            'ACTION', 'ACTOR',
            'REPOSITORY',
            'EVENT_NAME', 'EVENT_PATH',
            'WORKSPACE',
            'SHA', 'REF',
            'TOKEN',
    }:
        if f'GITHUB_{var_suffix}' not in os.environ:
            logger.info(
                'Detected GitHub App mode since '
                'GITHUB_%s is missing from the env',
                var_suffix,
            )
            return 'app'
    logger.info(
        'Detected GitHub Action mode since all the '
        'typical env vars are present in the env',
    )
    return 'action'
