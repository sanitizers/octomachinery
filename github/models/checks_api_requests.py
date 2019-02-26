from functools import partial
from typing import List, Optional

import attr


__all__ = 'NewCheckRequest', 'UpdateCheckRequest', 'to_gh_query'


str_attrib = partial(attr.ib, converter=lambda s: str(s) if s is not None else '')

int_attrib = partial(attr.ib, converter=int)

optional_attrib = partial(
    attr.ib,
    default=None,
)

optional_int_attrib = partial(
    optional_attrib,
    validator=attr.validators.optional(lambda *_: int(_[-1])),
)

optional_str_attrib = partial(
    optional_attrib,
    validator=attr.validators.optional(lambda *_: str(_[-1])),
)

optional_list_attrib = partial(
    attr.ib,
    default=[],
    validator=attr.validators.optional(lambda *_: list(_[-1])),
)

def optional_converter(kwargs_dict, convert_to_cls):
    if kwargs_dict is not None and not isinstance(kwargs_dict, convert_to_cls):
        return convert_to_cls(**kwargs_dict)
    return kwargs_dict

def optional_list_converter(args_list, convert_to_cls):
    if args_list is not None and isinstance(args_list, list):
        return [optional_converter(kwargs_dict, convert_to_cls) for kwargs_dict in args_list]
    return args_list


@attr.dataclass
class CheckAnnotation:
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


@attr.dataclass
class CheckImage:
    alt: str = str_attrib()
    image_url: str = str_attrib()
    caption: Optional[str] = optional_str_attrib()


@attr.dataclass
class CheckActions:
    label: str = str_attrib()
    description: str = str_attrib()
    identifier: str = str_attrib()

    @label.validator
    def label_up_to_20(self, attribute, value):
        if len(value) > 20:
            raise ValueError(f'`{attribute.name}` must not exceed 20 characters.')

    @description.validator
    def description_up_to_40(self, attribute, value):
        if len(value) > 40:
            raise ValueError(f'`{attribute.name}` must not exceed 40 characters.')

    @identifier.validator
    def identifier_up_to_20(self, attribute, value):
        if len(value) > 20:
            raise ValueError(f'`{attribute.name}` must not exceed 20 characters.')


@attr.dataclass
class CheckOutput:
    title: str = str_attrib()
    summary: str = str_attrib()
    text: str = str_attrib(default='')
    annotations: List[CheckAnnotation] = optional_list_attrib(converter=partial(optional_list_converter, convert_to_cls=CheckAnnotation))
    images: List[CheckImage] = optional_list_attrib(converter=partial(optional_list_converter, convert_to_cls=CheckImage))


@attr.dataclass
class BaseCheckRequestMixin:
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
    started_at: Optional[str] = optional_str_attrib()  # '2018-05-27T14:30:33Z', datetime.isoformat()
    conclusion: Optional[str] = attr.ib(
        # [required] if 'status' is set to 'completed', should be missing if it's unset
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
    completed_at: Optional[str] = optional_str_attrib()  # [required] if 'conclusion' is set  # '2018-05-27T14:30:33Z',
    output: Optional[CheckOutput] = optional_attrib(converter=partial(optional_converter, convert_to_cls=CheckOutput))
    actions: List[CheckActions] = optional_list_attrib(converter=partial(optional_list_converter, convert_to_cls=CheckActions))

    @conclusion.validator
    def depends_on_status(self, attribute, value):
        if self.status == 'completed' and not value:
            raise ValueError(f'`{attribute.name}` must be provided if status is completed')

    @completed_at.validator
    def depends_on_conclusion(self, attribute, value):
        if self.conclusion is not None and not value:
            raise ValueError(f'`{attribute.name}` must be provided if conclusion is present')

    @actions.validator
    def actions_up_to_3(self, attribute, value):
        if value is not None and len(value) > 3:
            raise ValueError(f'`{attribute.name}` must not exceed 3 items.')


@attr.dataclass
class NewCheckRequestMixin:
    head_branch: str = str_attrib()
    head_sha: str = str_attrib()


@attr.dataclass
class NewCheckRequest(NewCheckRequestMixin, BaseCheckRequestMixin):
    pass


@attr.dataclass
class UpdateCheckRequest(BaseCheckRequestMixin):
    pass


def conditional_to_gh_query(req):
    if hasattr(req, '__attrs_attrs__'):
        return to_gh_query(req)
    if isinstance(req, list):
        return list(map(conditional_to_gh_query, req))
    if isinstance(req, dict):
        return {
            k: conditional_to_gh_query(v) for k, v in req.items()
            if v is not None or (isinstance(v, (list, dict)) and not len(v))
        }
    return req


def to_gh_query(req):
    return {
        k: conditional_to_gh_query(v)  # recursive if dataclass or list
        for k, v in attr.asdict(req).items()
        if v is not None or (isinstance(v, (list, dict)) and not len(v))
    }
