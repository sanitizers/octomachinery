"""Tests for CLI utility functions."""

from io import StringIO
from textwrap import dedent
from uuid import uuid1, uuid4

import multidict
import pytest

from octomachinery.github.utils.event_utils import (
    _probe_json,
    _transform_http_headers_list_to_multidict,
    augment_http_headers,
    make_http_headers_from_event,
    parse_event_stub_from_fd,
    validate_http_headers,
)


UNCHANGED_UUID4_STR = str(uuid4())


@pytest.mark.parametrize(
    'vcr_contents, vcr_headers',
    (
        pytest.param(
            dedent(
                """
                ---
                # This needs to be a sequence of mappings;
                # it cannot be just a mapping because headers
                # may occur multiple times
                - Content-Type: application/json
                - X-GitHub-Delivery: 2791443c-641a-40fa-836d-031a26f0d45f
                - X-GitHub-Event: ping
                ---
                {
                  "hook": {"app_id": 0},
                  "hook_id": 0,
                  "zen": "Hey zen!"
                }
                """,
            ),
            multidict.CIMultiDict({
                'Content-Type': 'application/json',
                'X-GitHub-Delivery': '2791443c-641a-40fa-836d-031a26f0d45f',
                'X-GitHub-Event': 'ping',
            }),
            id='YAML',
        ),
        pytest.param(
            # pylint: disable=line-too-long
            """
            [{"Content-Type": "application/json"}, {"X-GitHub-Delivery": "2791443c-641a-40fa-836d-031a26f0d45f"}, {"X-GitHub-Event": "ping"}]
            {"hook": {"app_id": 0}, "hook_id": 0, "zen": "Hey zen!"}
            """.strip(),  # noqa: E501
            multidict.CIMultiDict({
                'Content-Type': 'application/json',
                'X-GitHub-Delivery': '2791443c-641a-40fa-836d-031a26f0d45f',
                'X-GitHub-Event': 'ping',
            }),
            id='JSONL',
        ),
        pytest.param(
            '{\n"hook": {\n"app_id": 0}, "hook_id": 0, "zen": "Hey zen!"}',
            multidict.CIMultiDict(),
            id='JSON',
        ),
        pytest.param(
            """
            {"hook": {"app_id": 0}, "hook_id": 0, "zen": "Hey zen!"}
            {
            """.strip(),
            multidict.CIMultiDict(),
            id='JSONL with the broken 2nd line',
        ),
    ),
)
def test_parse_event_stub_from_fd(vcr_contents, vcr_headers):
    """Check that all of YAML, JSONL and JSON VCR modes are loadable."""
    vcr_event = {
        'hook': {
            'app_id': 0,
        },
        'hook_id': 0,
        'zen': 'Hey zen!',
    }
    with StringIO(vcr_contents) as event_file_fd:
        actual_parsed_vcr = parse_event_stub_from_fd(event_file_fd)

    expected_parsed_vcr = vcr_headers, vcr_event
    assert actual_parsed_vcr == expected_parsed_vcr


@pytest.mark.parametrize(
    'vcr_contents',
    (
        pytest.param(
            dedent(
                """
                ---
                - X-GitHub-Event: ping
                ---
                {}
                ---
                - extra document
                """,
            ),
            id='broken 3-document YAML (must be 2 documents)',
        ),
        pytest.param(
            dedent(
                """
                ---
                """,
            ),
            id='broken empty-document YAML',
        ),
        pytest.param(
            """
            [{"X-GitHub-Event": "ping"}]
            {"hook": {"app_id": 0}, "hook_id": 0, "zen": "Hey zen!"}
            {}
            """,
            id='broken 3-line JSONL (must be 2 lines)',
        ),
        pytest.param(
            '1{"hook": {"app_id": 0}, "hook_id": 0, "zen": "Hey zen!"}',
            id='broken JSON syntax (leading garbage)',
        ),
    ),
)
def test_parse_event_stub_from_fd__invalid(vcr_contents):
    """Verify that feeding unconventional VCRs raises ValueError."""
    expected_error_message = (
        r'^The input event VCR file has invalid structure\. '
        r'It must be either of YAML, JSONL or JSON\.$'
    )
    with StringIO(vcr_contents) as file_descr, pytest.raises(
            ValueError,
            match=expected_error_message,
    ):
        parse_event_stub_from_fd(file_descr)


@pytest.mark.parametrize(
    'http_headers',
    (
        pytest.param(
            multidict.CIMultiDict({
                'Content-Type': 'application/json',
                'User-Agent': 'GitHub-Hookshot/dict-test',
                'X-GitHub-Delivery': str(uuid4()),
                'X-GitHub-Event': 'issue',
            }),
            id='multidict',
        ),
        pytest.param(
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-delivery': str(uuid4()),
                'x-github-event': 'pull_request',
            },
            id='dict',
        ),
        pytest.param(
            make_http_headers_from_event('ping'),
            id='make_http_headers_from_event constructor',
        ),
    ),
)
def test_validate_http_headers(http_headers):
    """Verify that valid headers collections don't raise exceptions."""
    assert validate_http_headers(http_headers) is None  # no exceptions raised


@pytest.mark.parametrize(
    'http_headers, error_message',
    (
        pytest.param(
            {
                'content-type': 'multipart/form-data',
            },
            r"^Content\-Type must be 'application\/json'$",
            id='Content-Type',
        ),
        pytest.param(
            {
                'content-type': 'application/json',
                'user-agent': 'Fake-GitHub-Hookshot/dict-test',
            },
            r"^User\-Agent must start with 'GitHub-Hookshot\/'$",
            id='User-Agent',
        ),
        pytest.param(
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-delivery': 'garbage',
            },
            r'^X\-GitHub\-Delivery must be of type UUID4$',
            id='garbage X-GitHub-Delivery',
        ),
        pytest.param(
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-delivery': str(uuid1()),
            },
            r'^X\-GitHub\-Delivery must be of type UUID4$',
            id='UUID1 X-GitHub-Delivery',
        ),
        pytest.param(
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-delivery': str(uuid4()),
                'x-github-event': None,
            },
            r'^X\-GitHub\-Event must be a string$',
            id='X-GitHub-Event',
        ),
    ),
)
def test_validate_http_headers__invalid(http_headers, error_message):
    """Check that invalid headers cause ValueError."""
    with pytest.raises(ValueError, match=error_message):
        validate_http_headers(http_headers)


@pytest.mark.parametrize(
    'incomplete_http_headers, expected_headers',
    (
        pytest.param(
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-delivery': UNCHANGED_UUID4_STR,
                'x-github-event': 'pull_request',
                'x-header': 'x_value',
            },
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-delivery': UNCHANGED_UUID4_STR,
                'x-github-event': 'pull_request',
                'x-header': 'x_value',
            },
            id='unchanged',
        ),
        pytest.param(
            {
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-delivery': str(uuid4()),
                'x-github-event': 'pull_request',
                'x-header': 'x_value',
            },
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-event': 'pull_request',
                'x-header': 'x_value',
            },
            id='Content-Type',
        ),
        pytest.param(
            {
                'content-type': 'application/json',
                'x-github-delivery': str(uuid4()),
                'x-github-event': 'pull_request',
                'x-header': 'x_value',
            },
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/fallback-value',
                'x-github-event': 'pull_request',
                'x-header': 'x_value',
            },
            id='User-Agent',
        ),
        pytest.param(
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-event': 'pull_request',
                'x-header': 'x_value',
            },
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/dict-test',
                'x-github-event': 'pull_request',
                'x-header': 'x_value',
            },
            id='X-GitHub-Delivery',
        ),
        pytest.param(
            {
                'x-github-event': 'ping',
            },
            {
                'content-type': 'application/json',
                'user-agent': 'GitHub-Hookshot/fallback-value',
                'x-github-event': 'ping',
            },
            id='X-GitHub-Event',
        ),
    ),
)
def test_augment_http_headers(incomplete_http_headers, expected_headers):
    """Check that mandatory headers are present after augmentation."""
    augmented_headers = augment_http_headers(incomplete_http_headers)

    assert validate_http_headers(augmented_headers) is None

    original_event = incomplete_http_headers['x-github-event']
    assert augmented_headers['x-github-event'] == original_event

    for header_name, header_value in expected_headers.items():
        assert augmented_headers[header_name] == header_value


def test_make_http_headers_from_event():
    """Smoke-test fake HTTP headers constructor."""
    event_name = 'issue_comment'
    http_headers = make_http_headers_from_event(event_name)

    assert http_headers['X-GitHub-Event'] == event_name
    assert http_headers['User-Agent'].endswith('/fallback-value')
    assert validate_http_headers(http_headers) is None


def test__transform_http_headers_list_to_multidict__invalid():
    """Check the headers format validation."""
    error_message = (
        '^Headers must be a sequence of mappings '
        'because keys can repeat$'
    )
    with pytest.raises(ValueError, match=error_message):
        _transform_http_headers_list_to_multidict({})


def test__probe_json():
    """Test that JSON probe loads mappings."""
    vcr_contents = (
        '{\n"hook": {\n"app_id": 0},'
        ' "hook_id": 0, '
        '"zen": "Hey zen!"}'
    )
    vcr_headers = ()
    vcr_event = {
        'hook': {
            'app_id': 0,
        },
        'hook_id': 0,
        'zen': 'Hey zen!',
    }
    with StringIO(vcr_contents) as event_file_fd:
        actual_parsed_vcr = _probe_json(event_file_fd)

    expected_parsed_vcr = vcr_headers, vcr_event
    assert actual_parsed_vcr == expected_parsed_vcr


def test__probe_json__invalid():
    """Verify that non-mapping objects crash pure JSON probe."""
    expected_error_message = '^JSON file must only contain an object mapping$'
    with StringIO('[]') as file_descr, pytest.raises(
            ValueError,
            match=expected_error_message,
    ):
        _probe_json(file_descr)
