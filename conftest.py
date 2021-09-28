"""
Pytest helper classes and fixtures
"""
from pytest import fixture

from jmrpc.jmrpc import JmRpc


@fixture(scope='session')
def jmrpc() -> JmRpc:
    """
    Return jmrpc client shared across the entire test session
    """
    jmrpc = JmRpc()
    yield jmrpc
    jmrpc.close()
