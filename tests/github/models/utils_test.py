"""Tests for GitHub models utility functions."""

import pytest

from octomachinery.github.models.utils import (
    SecretStr, SuperSecretStr,
)


@pytest.mark.parametrize(
    'secret_class,secret_placeholder,visible_first_repr',
    (
        (SecretStr, '<SECRET>', True),
        (SuperSecretStr, '<SUPER_SECRET>', False),
    ),
)
def test_secret_sanitizers_first_repr(
        secret_class, secret_placeholder, visible_first_repr,
):
    """Check that immediate repr is rendered correctly."""
    secret_data = 'qwerty'
    super_secret_string = secret_class(secret_data)

    expected_repr = (
        repr(secret_data) if visible_first_repr
        else secret_placeholder
    )
    assert repr(super_secret_string) == expected_repr


@pytest.mark.parametrize(
    'secret_class,secret_placeholder',
    (
        (SecretStr, '<SECRET>'),
        (SuperSecretStr, '<SUPER_SECRET>'),
    ),
)
def test_secret_sanitizers(secret_class, secret_placeholder):
    """Check that sanitizer classes hide data when needed."""
    secret_data = 'qwerty'
    super_secret_string = secret_class(secret_data)
    assert str(super_secret_string) == str(secret_data)
    assert super_secret_string == secret_data

    class _DataStruct:  # pylint: disable=too-few-public-methods
        def __init__(self, s, o=None):
            self._s = s
            self._o = o

        def __repr__(self):
            return (
                f'{self.__class__.__name__}'
                f'(s={repr(self._s)}, o={repr(self._o)})'
            )

    open_data = 'gov'
    data_struct = _DataStruct(super_secret_string, open_data)

    expected_data_struct_repr = (
        f'_DataStruct(s={secret_placeholder}, o={repr(open_data)})'
    )
    assert repr(data_struct) == expected_data_struct_repr

    sub_data_struct = _DataStruct(data_struct, secret_class(None))

    expected_nested_data_struct_repr = (
        f'_DataStruct(s=_DataStruct(s={secret_placeholder}, '
        f'o={repr(open_data)}), o={secret_placeholder})'
    )
    assert repr(sub_data_struct) == expected_nested_data_struct_repr
