import asyncio
from functools import wraps


class DreamError(Exception):
    pass


class YuriDream:
    def __init__(self, coro, name=None):
        self.coro   = coro
        self.name   = name or "unnamed dream"
        self.task   = None
        self.result = None
        self.done   = False

    def __repr__(self):
        if self.done:
            return f"@dream({self.name}) → {self.result}"
        return f"@dream({self.name}) → still dreaming..."


def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def make_async_ship(params, body, functions, variables_ref):
    async def async_wrapper(*args):
        from src.interpreter import run_node, evaluate, ReturnSignal

        old_vars = variables_ref.copy()
        for i, param in enumerate(params):
            if i < len(args):
                variables_ref[param] = args[i]

        result = None
        for child in body:
            ret = run_node(child)

            if isinstance(ret, ReturnSignal):
                result = ret.value
                break

            if asyncio.iscoroutine(ret):
                result = await ret
                break

        variables_ref.clear()
        variables_ref.update(old_vars)
        return result

    return async_wrapper


async def gather_dreams(dreams):
    if not isinstance(dreams, list):
        raise DreamError(
            "\n💔 @gather — expected an array of @dream values\n"
            " |> Hint: @bond dreams = [[@dream1, @dream2]]\n"
            "           @gather dreams\n"
        )

    coros = []
    for d in dreams:
        if isinstance(d, YuriDream):
            coros.append(d.coro)
        elif asyncio.iscoroutine(d):
            coros.append(d)
        else:
            raise DreamError(f"@gather: '{d}' is not a @dream")

    results = await asyncio.gather(*coros, return_exceptions=True)

    for i, r in enumerate(results):
        if isinstance(r, Exception):
            raise DreamError(
                f"\n💔 @gather — dream {i} failed\n"
                f"  {str(r)}\n"
            )

    return list(results)


def run_dream(dream):
    loop = get_event_loop()
    if isinstance(dream, YuriDream):
        return loop.run_until_complete(dream.coro)
    elif asyncio.iscoroutine(dream):
        return loop.run_until_complete(dream)
    return dream


def sleep_dream(seconds):
    return asyncio.sleep(seconds)
