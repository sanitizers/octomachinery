"""Models representing objects in GitHub Checks API."""

from functools import partial
from typing import List, Optional

import attr


__all__ = ('NewCheckRequest', 'UpdateCheckRequest', 'to_gh_query')


str_attrib = partial(  # pylint: disable=invalid-name
    attr.ib,
    converter=lambda s: str(s) if s is not None else '',
)

int_attrib = partial(attr.ib, converter=int)  # pylint: disable=invalid-name

optional_attrib = partial(  # pylint: disable=invalid-name
    attr.ib,
    default=None,
)

optional_int_attrib = partial(  # pylint: disable=invalid-name
    optional_attrib,
    validator=attr.validators.optional(lambda *_: int(_[-1])),
)

optional_str_attrib = partial(  # pylint: disable=invalid-name
    optional_attrib,
    validator=attr.validators.optional(lambda *_: str(_[-1])),
)

optional_list_attrib = partial(  # pylint: disable=invalid-name
    attr.ib,
    default=[],
    validator=attr.validators.optional(lambda *_: list(_[-1])),
)


def optional_converter(kwargs_dict, convert_to_cls):
    """Instantiate a class instances from dict."""
    if kwargs_dict is not None and not isinstance(kwargs_dict, convert_to_cls):
        return convert_to_cls(**kwargs_dict)
    return kwargs_dict


def optional_list_converter(args_list, convert_to_cls):
    """Convert list items to class instances."""
    if args_list is not None and isinstance(args_list, list):
        return [
            optional_converter(kwargs_dict, convert_to_cls)
            for kwargs_dict in args_list
        ]
    return args_list


@attr.dataclass  # pylint: disable=too-few-public-methods
class CheckAnnotation:
    """Checks API annotation struct."""

    path: str = str_attrib()
    start_line: int = int_attrib()
    end_line: int = int_attrib()
    annotation_level: str = str_attrib(
        validator=attr.validators.in_(
            (
                'notice',
                'warning',
                'failure',
            ),
        ),
    )
    message: str = str_attrib()
    start_column: Optional[int] = optional_int_attrib()
    end_column: Optional[int] = optional_int_attrib()
    title: Optional[str] = optional_str_attrib()
    raw_details: Optional[str] = optional_str_attrib()


@attr.dataclass  # pylint: disable=too-few-public-methods
class CheckImage:
    """Checks API image struct."""

    alt: str = str_attrib()
    image_url: str = str_attrib()
    caption: Optional[str] = optional_str_attrib()


@attr.dataclass
class CheckActions:
    """Checks API actions struct."""

    label: str = str_attrib()
    description: str = str_attrib()
    identifier: str = str_attrib()

    @label.validator
    def label_up_to_20(self, attribute, value):  # pylint: disable=no-self-use
        """Ensure that label is under 20."""
        if len(value) > 20:
            raise ValueError(
                f'`{attribute.name}` must not exceed 20 characters.',
            )

    @description.validator
    def description_up_to_40(self, attribute, value):
        """Ensure that description is under 40."""
        # pylint: disable=no-self-use
        if len(value) > 40:
            raise ValueError(
                f'`{attribute.name}` must not exceed 40 characters.',
            )

    @identifier.validator
    def identifier_up_to_20(self, attribute, value):
        """Ensure that identifier is under 20."""
        # pylint: disable=no-self-use
        if len(value) > 20:
            raise ValueError(
                f'`{attribute.name}` must not exceed 20 characters.',
            )


@attr.dataclass  # pylint: disable=too-few-public-methods
class CheckOutput:
    """Checks API output struct."""

    title: str = str_attrib()
    summary: str = str_attrib()
    text: str = str_attrib(default='')
    annotations: List[CheckAnnotation] = optional_list_attrib(
        converter=partial(
            optional_list_converter,
            convert_to_cls=CheckAnnotation,
        ),
    )
    images: List[CheckImage] = optional_list_attrib(
        converter=partial(optional_list_converter, convert_to_cls=CheckImage),
    )


@attr.dataclass
class BaseCheckRequestMixin:
    """Checks API base check request mixin."""

    name: str = str_attrib()
    details_url: Optional[str] = optional_str_attrib()
    external_id: Optional[str] = optional_str_attrib()
    status: Optional[str] = attr.ib(
        default='queued',
        validator=attr.validators.optional(
            attr.validators.in_(
                (
                    'queued',
                    'in_progress',
                    'completed',
                ),
            ),
        ),
    )
    # '2018-05-27T14:30:33Z', datetime.isoformat():
    started_at: Optional[str] = optional_str_attrib()
    conclusion: Optional[str] = attr.ib(
        # [required] if 'status' is set to 'completed',
        # should be missing if it's unset
        default=None,
        validator=attr.validators.optional(
            attr.validators.in_(
                (
                    'success',
                    'failure',
                    'neutral',
                    'cancelled',
                    'timed_out',
                    'action_required',
                ),
            ),
        ),
    )
    # [required] if 'conclusion' is set  # '2018-05-27T14:30:33Z':
    completed_at: Optional[str] = optional_str_attrib()
    output: Optional[CheckOutput] = optional_attrib(
        converter=partial(optional_converter, convert_to_cls=CheckOutput),
    )
    actions: List[CheckActions] = optional_list_attrib(
        converter=partial(
            optional_list_converter,
            convert_to_cls=CheckActions,
        ),
    )

    @conclusion.validator  # pylint: disable=no-self-use
    def depends_on_status(self, attribute, value):
        """Ensure that conclusion is present if there's status."""
        if self.status == 'completed' and not value:
            raise ValueError(
                f'`{attribute.name}` must be provided if status is completed',
            )

    @completed_at.validator  # pylint: disable=no-self-use
    def depends_on_conclusion(self, attribute, value):
        """Ensure that completed is present if there's conclusion."""
        if self.conclusion is not None and not value:
            raise ValueError(
                f'`{attribute.name}` must be provided '
                'if conclusion is present',
            )

    @actions.validator
    def actions_up_to_3(self, attribute, value):  # pylint: disable=no-self-use
        """Ensure that the number of actions is below 3."""
        if value is not None and len(value) > 3:
            raise ValueError(f'`{attribute.name}` must not exceed 3 items.')


@attr.dataclass  # pylint: disable=too-few-public-methods
class NewCheckRequestMixin:
    """Checks API new check request mixin."""

    head_branch: str = str_attrib()
    head_sha: str = str_attrib()


@attr.dataclass
class NewCheckRequest(NewCheckRequestMixin, BaseCheckRequestMixin):
    """Checks API new check request."""


@attr.dataclass
class UpdateCheckRequest(BaseCheckRequestMixin):
    """Checks API update check request."""


def conditional_to_gh_query(req):
    """Traverse Checks API request structure."""
    if hasattr(req, '__attrs_attrs__'):
        return to_gh_query(req)
    if isinstance(req, list):
        return list(map(conditional_to_gh_query, req))
    if isinstance(req, dict):
        return {
            k: conditional_to_gh_query(v) for k, v in req.items()
            if v is not None or (isinstance(v, (list, dict)) and not v)
        }
    return req


def to_gh_query(req):
    """Convert Checks API request object into a dict."""
    return {
        k: conditional_to_gh_query(v)  # recursive if dataclass or list
        for k, v in attr.asdict(req).items()
        if v is not None or (isinstance(v, (list, dict)) and not v)
    }
