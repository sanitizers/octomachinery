"""Utility helpers for CLI."""

import contextlib
import itertools
import json
from uuid import UUID, uuid4

import multidict
import yaml


def _probe_yaml(event_file_fd):
    try:
        http_headers, event, extra = itertools.islice(
            itertools.chain(
                yaml.safe_load_all(event_file_fd),
                (None, ) * 3,
            ),
            3,
        )
    except yaml.parser.ParserError as yaml_err:
        raise ValueError('YAML file is not valid') from yaml_err
    finally:
        event_file_fd.seek(0)

    if extra is not None:
        raise ValueError('YAML file must only contain 1–2 documents')

    if event is None:
        event = http_headers
        http_headers = ()

    if event is None:
        raise ValueError('YAML file must contain 1–2 non-empty documents')

    return http_headers, event


def _probe_jsonl(event_file_fd):
    event = None

    first_line = event_file_fd.readline()
    second_line = event_file_fd.readline()
    third_line = event_file_fd.readline()
    event_file_fd.seek(0)

    if third_line:
        raise ValueError('JSONL file must only contain 1–2 JSON lines')

    http_headers = json.loads(first_line)

    with contextlib.suppress(ValueError):
        event = json.loads(second_line)

    if event is None:
        event = http_headers
        http_headers = ()

    return http_headers, event


def _probe_json(event_file_fd):
    event = json.load(event_file_fd)
    event_file_fd.seek(0)

    if not isinstance(event, dict):
        raise ValueError('JSON file must only contain an object mapping')

    http_headers = ()

    return http_headers, event


def _parse_fd_content(event_file_fd):
    """Guess file content type and read event with HTTP headers."""
    for event_reader in _probe_yaml, _probe_jsonl, _probe_json:
        with contextlib.suppress(ValueError):
            return event_reader(event_file_fd)

    raise ValueError(
        'The input event VCR file has invalid structure. '
        'It must be either of YAML, JSONL or JSON.',
    )


def _transform_http_headers_list_to_multidict(headers):
    if isinstance(headers, dict):
        raise ValueError(
            'Headers must be a sequence of mappings because keys can repeat',
        )
    return multidict.CIMultiDict(next(iter(h.items()), ()) for h in headers)


def parse_event_stub_from_fd(event_file_fd):
    """Read event with HTTP headers as CIMultiDict instance."""
    http_headers, event = _parse_fd_content(event_file_fd)
    return _transform_http_headers_list_to_multidict(http_headers), event


def validate_http_headers(headers):
    """Verify that HTTP headers look sane."""
    if headers['content-type'] != 'application/json':
        raise ValueError("Content-Type must be 'application/json'")

    if not headers['user-agent'].startswith('GitHub-Hookshot/'):
        raise ValueError("User-Agent must start with 'GitHub-Hookshot/'")

    x_gh_delivery_exc = ValueError('X-GitHub-Delivery must be of type UUID4')
    try:
        x_gh_delivery_uuid = UUID(headers['x-github-delivery'])
    except ValueError as val_err:
        raise x_gh_delivery_exc from val_err
    if x_gh_delivery_uuid.version != 4:
        raise x_gh_delivery_exc

    if not isinstance(headers['x-github-event'], str):
        raise ValueError('X-GitHub-Event must be a string')


def augment_http_headers(headers):
    """Add fake HTTP headers for the missing positions."""
    fake_headers = make_http_headers_from_event(headers['x-github-event'])

    if 'content-type' not in headers:
        headers['content-type'] = fake_headers['content-type']

    if 'user-agent' not in headers:
        headers['user-agent'] = fake_headers['user-agent']

    if 'x-github-delivery' not in headers:
        headers['x-github-delivery'] = fake_headers['x-github-delivery']

    return headers


def make_http_headers_from_event(event_name):
    """Generate fake HTTP headers with the given event name."""
    return multidict.CIMultiDict({
        'content-type': 'application/json',
        'user-agent': 'GitHub-Hookshot/fallback-value',
        'x-github-delivery': str(uuid4()),
        'x-github-event': event_name,
    })
