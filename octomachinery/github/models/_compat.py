"""Compatibility shims for the models subpackage."""
from functools import wraps as _wraps_function

from jwt import encode as _compute_jwt


try:
    from jwt import __version__ as _pyjwt_version_str
except ImportError:
    _pyjwt_version_str = '0.0.0'


_pyjwt_version_info = tuple(map(int, _pyjwt_version_str.split('.')))
_is_pyjwt_above_v2_0 = _pyjwt_version_info >= (2, 0, 0)


@_wraps_function(_compute_jwt)
def _compute_jwt_below_v2_0(*args, **kwargs) -> str:
    return _compute_jwt(*args, **kwargs).decode('utf-8')


compute_jwt = _compute_jwt if _is_pyjwt_above_v2_0 else _compute_jwt_below_v2_0
