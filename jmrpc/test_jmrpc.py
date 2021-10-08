"""
Test JSON-RPC client against a real JoinMarket server. For now really basic.
"""

from pytest import mark

from jmrpc.jmdata import ListWallets, Session


@mark.asyncio
async def test_jmrpc(jmrpc):
    assert jmrpc.endpoint == 'https://127.0.0.1:28183'
    assert jmrpc.id_count == 0
    assert jmrpc.token is False
    # Context manager automatically starts the websocket
    assert jmrpc.websocket is True


@mark.require_server
@mark.asyncio
async def test_list_wallets(jmrpc):
    response = await jmrpc.list_wallets()
    assert isinstance(response, ListWallets)
    assert isinstance(response.dict, dict)
    assert isinstance(response.wallets, list)
    assert isinstance(response.wallets[0], str)


@mark.require_server
@mark.asyncio
async def test_session(jmrpc):
    response = await jmrpc.session()
    assert isinstance(response, Session)
    assert isinstance(response.dict, dict)
