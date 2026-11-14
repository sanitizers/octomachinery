"""Asynchronous tools set."""

import typing as _t
from inspect import signature as _inspect_signature
from logging import getLogger as _get_logger
from operator import itemgetter

from anyio import EndOfStream, WouldBlock, create_memory_object_stream
from anyio import create_task_group as all_subtasks_awaited
from anyio.streams.memory import (
    MemoryObjectReceiveStream, MemoryObjectSendStream,
)


logger = _get_logger(__name__)

_TaskOutcome = _t.Tuple[int, _t.Any, _t.Union[Exception, None]]


async def _send_task_res_to_q(
        res_q: MemoryObjectSendStream[_TaskOutcome],
        task_id: int,
        aio_task: _t.Awaitable[_t.Any],
) -> None:
    """Await task and send its outcome to the stream."""
    try:
        task_res = await aio_task
    except Exception as exc:  # pylint: disable=broad-except
        res_q.send_nowait((task_id, None, exc))
    else:
        res_q.send_nowait((task_id, task_res, None))


def _log_leftover_task_failures(
        res_q: MemoryObjectReceiveStream[_TaskOutcome],
) -> None:
    """Log the task failures that won't be re-raised."""
    while True:
        try:
            _task_id, _task_res, task_exc = res_q.receive_nowait()
        except (EndOfStream, WouldBlock):
            return

        if task_exc is not None:
            # NOTE: `logger.exception()` that G201 suggests implies
            # NOTE: `exc_info=True`, which reads the exception being
            # NOTE: currently handled. These ones are detached from
            # NOTE: their handlers, so they have to be passed in
            # NOTE: explicitly:
            logger.error(  # noqa: G201
                'Another gathered task failed', exc_info=task_exc,
            )


async def _aio_gather_iter_pairs(
        *aio_tasks: _t.Awaitable[_t.Any],
) -> _t.AsyncIterator[_t.Tuple[int, _t.Any]]:
    """Spawn async tasks and yield with pairs of ids with results.

    The first task failure cancels the rest of the tasks. It is then
    re-raised as is. Raising it from within the task group would get
    it wrapped into an exception group, making it impossible to catch
    by its own type.
    """
    aio_tasks_num = len(aio_tasks)
    task_res_send_q, task_res_recv_q = (
        create_memory_object_stream[_TaskOutcome](aio_tasks_num)
    )
    task_exc = None

    # NOTE: The streams must outlive the task group so that the
    # NOTE: children could still report their outcomes while it is
    # NOTE: unwinding. This is why they are entered first.
    async with task_res_send_q, task_res_recv_q:
        async with all_subtasks_awaited() as task_group:
            for task_id, task in enumerate(aio_tasks):
                task_group.start_soon(
                    _send_task_res_to_q,
                    task_res_send_q,
                    task_id, task,
                )

            for _ in range(aio_tasks_num):
                task_id, task_res, task_exc = await task_res_recv_q.receive()
                if task_exc is not None:
                    task_group.cancel_scope.cancel()
                    break
                yield task_id, task_res

        if task_exc is not None:
            _log_leftover_task_failures(task_res_recv_q)

    if task_exc is not None:
        raise task_exc


async def aio_gather_iter(*aio_tasks):
    """Spawn async tasks and yield results.

    The iterator must be consumed to exhaustion. Abandoning it early
    leaves the underlying task group to be closed by the async
    generator finalizer, which runs in a different task, making anyio
    reject the cancel scope exit.
    """
    async for _task_id, task_res in _aio_gather_iter_pairs(*aio_tasks):
        yield task_res


async def aio_gather(*aio_tasks):
    """Spawn async tasks and return results in the same order."""
    result_pairs_gen = [_r async for _r in _aio_gather_iter_pairs(*aio_tasks)]
    sorted_result_pairs = sorted(result_pairs_gen, key=itemgetter(0))
    all_task_results = map(itemgetter(1), sorted_result_pairs)
    return tuple(all_task_results)


async def try_await(potentially_awaitable):
    """Try awaiting the arg and return it regardless."""
    valid_exc_str = (
        "can't be used in 'await' expression"
    )

    try:
        return await potentially_awaitable
    except TypeError as type_err:
        type_err_msg = str(type_err)
        if not (
                type_err_msg.startswith('object ')
                and type_err_msg.endswith(valid_exc_str)
        ):
            raise

    return potentially_awaitable


async def amap(callback, async_iterable):
    """Map asynchronous generator with a coroutine or a function."""
    async for async_value in async_iterable:
        yield await try_await(callback(async_value))


def dict_to_kwargs_cb(callback):
    """Return a callback mapping dict to keyword arguments."""
    cb_arg_names = set(_inspect_signature(callback).parameters.keys())

    async def callback_wrapper(args_dict):
        excessive_arg_names = set(args_dict.keys()) - cb_arg_names
        filtered_args_dict = {
            arg_name: arg_value for arg_name, arg_value in args_dict.items()
            if arg_name not in excessive_arg_names
        } if excessive_arg_names else args_dict
        if excessive_arg_names:
            logger.warning(
                'Excessive arguments passed to callback %(callable)s',
                {'callable': callback},
                extra={
                    'callable': callback,
                    'excessive-arg-names': excessive_arg_names,
                    'passed-in-args': args_dict,
                    'forwarded-args': filtered_args_dict,
                },
            )
        return await try_await(callback(**filtered_args_dict))
    return callback_wrapper
