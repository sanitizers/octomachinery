"""Asynchronous tools set."""

from functools import wraps
from operator import itemgetter

from anyio import create_queue, create_task_group as all_subtasks_awaited


def auto_cleanup_aio_tasks(async_func):
    """Ensure all subtasks finish."""
    @wraps(async_func)
    async def async_func_wrapper(*args, **kwargs):
        async with all_subtasks_awaited():
            return await async_func(*args, **kwargs)
    return async_func_wrapper


async def _send_task_res_to_q(res_q, task_id, aio_task):
    """Await task and put its result to the queue."""
    try:
        task_res = await aio_task
    except (BaseException, Exception) as exc:
        task_res = exc
        raise
    finally:
        await res_q.put((task_id, task_res))


async def _aio_gather_iter_pairs(*aio_tasks):
    """Spawn async tasks and yield with pairs of ids with results."""
    aio_tasks_num = len(aio_tasks)
    task_res_q = create_queue(aio_tasks_num)

    async with all_subtasks_awaited() as task_group:
        for task_id, task in enumerate(aio_tasks):
            await task_group.spawn(
                _send_task_res_to_q,
                task_res_q,
                task_id, task,
            )

        for _ in range(aio_tasks_num):
            yield await task_res_q.get()


async def aio_gather_iter(*aio_tasks):
    """Spawn async tasks and yield results."""
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
    """Map asyncronous generator with a coroutine or a function."""
    async for async_value in async_iterable:
        yield await try_await(callback(async_value))


def dict_to_kwargs_cb(callback):
    """Return a callback mapping dict to keyword arguments."""
    async def callback_wrapper(args_dict):
        return await try_await(callback(**args_dict))
    return callback_wrapper
