"""
Pytest helper classes and fixtures
"""
from asyncio import get_event_loop

from pytest import fixture, mark

from jmrpc.jmrpc import JmRpc


@fixture(scope="session")
def event_loop():
    loop = get_event_loop()
    yield loop
    loop.close()


@fixture(scope='session')
@mark.asyncio
async def jmrpc() -> JmRpc:
    """
    Return jmrpc client shared across the entire test session
    """
    async with JmRpc() as jmrpc:
        yield jmrpc
