"""Processing outcomes for use from within GitHub Action env."""

import logging

import attr


__all__ = ('ActionSuccess', 'ActionNeutral', 'ActionFailure', )


logger = logging.getLogger(__name__)


@attr.dataclass  # pylint: disable=too-few-public-methods
class ActionOutcome:
    """GitHub Action processing outcome."""

    message: str
    return_code: int

    def raise_it(self):
        """Print the message and exit the program with current code."""
        logger.info(
            'Terminating the GitHub Action processing: %s',
            self.message,
        )
        raise SystemExit(self.return_code)


@attr.dataclass  # pylint: disable=too-few-public-methods
class ActionSuccess(ActionOutcome):
    """GitHub Action successful outcome."""

    return_code: int = attr.ib(default=0, init=False)


@attr.dataclass  # pylint: disable=too-few-public-methods
class ActionFailure(ActionOutcome):
    """GitHub Action failed outcome."""

    return_code: int = attr.ib(default=1)

    @return_code.validator
    def _validate_return_code(  # pylint: disable=no-self-use
            self,
            attribute,  # pylint: disable=unused-argument
            value,
    ):
        if value in NON_FAIL_MODELS:
            raise ValueError(
                f'Return code of `{value}` is illegal to use for failure '
                f'outcome. Use {NON_FAIL_MODELS[value]} instead',
            )


@attr.dataclass  # pylint: disable=too-few-public-methods
class ActionNeutral(ActionOutcome):
    """GitHub Action neutral outcome."""

    # NOTE: It's EX_CONFIG under BSD and EREMCHG under GNU/Linux
    # NOTE: that's why we are using just 78 conventional constant
    # NOTE: here...
    # NOTE: Ref:
    # https://developer.github.com/actions/creating-github-actions\
    # /accessing-the-runtime-environment/#exit-codes-and-statuses
    return_code: int = attr.ib(default=78, init=False)


NON_FAIL_MODELS = {
    0: 'ActionSuccess',
    78: 'ActionNeutral',
}
