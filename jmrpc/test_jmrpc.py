"""
Test JSON-RPC client against a real JoinMarket server. For now really basic
and we manually have to delete `test_wallet.jmdat` each time.
"""

from jmrpc.jmdata import ListWallets, CreateWallet, LockWallet, \
    UnlockWallet, DisplayWallet, GetAddress, ListUtxos, GetSession


def test_list_wallets(jmrpc):
    response = jmrpc.list_wallets()
    assert isinstance(response, ListWallets)
    assert isinstance(response.dict, dict)
    assert isinstance(response.wallets, list)


def test_create_wallet(jmrpc):
    # TODO: for now the test wallet has to be deleted manually
    response = jmrpc.create_wallet('test_wallet.jmdat', 'password', 'sw')
    assert isinstance(response, CreateWallet)
    assert isinstance(response.dict, dict)
    assert jmrpc.token is True


def test_lock_wallet(jmrpc):
    response = jmrpc.lock_wallet('test_wallet.jmdat')
    assert isinstance(response, LockWallet)
    assert isinstance(response.dict, dict)


def test_unlock_wallet(jmrpc):
    response = jmrpc.unlock_wallet('test_wallet.jmdat', 'password')
    assert isinstance(response, UnlockWallet)
    assert isinstance(response.dict, dict)


def test_display_wallet(jmrpc):
    response = jmrpc.display_wallet('test_wallet.jmdat')
    assert isinstance(response, DisplayWallet)
    assert isinstance(response.dict, dict)


def test_get_address(jmrpc):
    response = jmrpc.get_address('test_wallet.jmdat', 0)
    assert isinstance(response, GetAddress)
    assert isinstance(response.dict, dict)


def test_list_utxos(jmrpc):
    response = jmrpc.list_utxos('test_wallet.jmdat')
    assert isinstance(response, ListUtxos)
    assert isinstance(response.dict, dict)


def test_get_session(jmrpc):
    response = jmrpc.session()
    assert isinstance(response, GetSession)
    assert isinstance(response.dict, dict)
