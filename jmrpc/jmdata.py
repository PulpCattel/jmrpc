"""
Objects for JoinMarket JSON-RPC response content
"""
from typing import Dict

from schematics.models import Model
from schematics.types import StringType, ListType, IntType, BooleanType, ModelType, FloatType
from ujson import dumps


class JmResponse(Model):
    """
    Base object for data returned by JoinMarket server.
    """

    def __init__(self, *args, **kwargs):
        """
        Set partial to False so that any required key missing throws an exception.
        """
        super().__init__(*args, **kwargs, partial=False)

    def __getitem__(self, item):
        return getattr(self, item)

    def __repr__(self):
        return dumps(self.dict)

    @property
    def dict(self) -> Dict:
        """
        Return dict representation of the model.
        """
        return self.to_native()


class ListWallets(JmResponse):
    """
    `listwallet` :class:`RpcMethod` response content.

    Fields:

    * wallets: Current available wallets.
    """

    wallets = ListType(StringType, required=True)


class CreateWallet(JmResponse):
    """
    `createwallet` :class:`RpcMethod` response content.

    Fields:

    * wallet_name: The filename for the wallet created on disk in `datadir/wallets`.
    * already_loaded: False for successful creation.
    * token: The created JWT token.
    * seedphrase: The BIP39 12 word seedphrase of the newly created JoinMarket wallet.
    """

    wallet_name = StringType(required=True, deserialize_from='walletname')
    already_loaded = BooleanType(required=True)
    token = StringType()
    seed_phrase = StringType(deserialize_from='seedphrase')


class UnlockWallet(JmResponse):
    """
    `unlockwallet` :class:`RpcMethod` response content.

    Fields:

    * wallet_name: The filename for the wallet created on disk in `datadir/wallets`.
    * token: The created JWT token.
    """

    wallet_name = StringType(required=True, deserialize_from='walletname')
    token = StringType(required=True)


class LockWallet(JmResponse):
    """
    lockwallet` :class:`RpcMethod` response content.

    Fields:

    * wallet_name: The filename for the wallet created on disk in `datadir/wallets`.
    * already_locked: False if there was an unlocked wallet, and we locked it, otherwise true.
    """

    wallet_name = StringType(required=True, deserialize_from='walletname')
    already_locked = BooleanType(required=True)


class Coin(JmResponse):
    """
    Represent a single coin inside the wallet information returned by `displaywallet` :class:`RpcMethod`.
    """

    hd_path = StringType(required=True)
    address = StringType(required=True)
    amount = FloatType(required=True)
    labels = StringType(required=True)


class Branch(JmResponse):
    """
    Represent a single branch inside the wallet information returned by `displaywallet` :class:`RpcMethod`.
    """

    branch = StringType(required=True)
    balance = FloatType(required=True)
    entries = ListType(ModelType(Coin), required=True)


class Account(JmResponse):
    """
    Represent a single account inside the wallet information returned by `displaywallet` :class:`RpcMethod`.
    """
    account = IntType(required=True)
    account_balance = FloatType(required=True)
    branches = ListType(ModelType(Branch), required=True)


class WalletInfo(JmResponse):
    """
    Represent the wallet information returned by `displaywallet` :class:`RpcMethod`.
    """
    wallet_name = StringType(required=True)
    total_balance = FloatType(required=True)
    accounts = ListType(ModelType(Account), required=True)


class DisplayWallet(JmResponse):
    """
    `displaywallet` :class:`RpcMethod` response content.

    Fields:

    * wallet_name: The filename for the wallet created on disk in `datadir/wallets`.
    * wallet_info: Detailed breakdown of wallet contents by account.
    """

    wallet_name = StringType(required=True, deserialize_from='walletname')
    wallet_info = ModelType(WalletInfo, required=True, deserialize_from='walletinfo')


class GetAddress(JmResponse):
    """
    `getaddress` :class:`RpcMethod` response content.

    Fields:

    * address: The first unused address in the *external* branch of the given account/mixdepth.
    """

    address = StringType(required=True)


class Utxo(JmResponse):
    """
    Single JoinMarket UTXO as returned by `listutxos` method.
    """

    outpoint = StringType(required=True, deserialize_from='utxo')
    address = StringType(required=True)
    value = IntType(required=True)
    tries = IntType(required=True)
    tries_remaining = IntType(required=True)
    external = BooleanType(required=True)
    mixdepth = IntType(required=True)
    confirmations = IntType(required=True)
    frozen = BooleanType(required=True)


class ListUtxos(JmResponse):
    """
    `listutxos` :class:`RpcMethod` response content.

    Fields:

    * utxos: All utxos currently owned by the wallet.
    """

    utxos = ListType(ModelType(Utxo), required=True)


class Input(JmResponse):
    """
    Represent an input inside a transaction as returned by `directsend` :class:`RpcMethod`.
    """

    outpoint = StringType(required=True)
    scriptSig = StringType(required=True)
    nSequence = IntType(required=True)
    witness = StringType(required=True)


class Output(JmResponse):
    """
    Represent an output inside a transaction as returned by `directsend` :class:`RpcMethod`.
    """

    value_sats = IntType(required=True)
    scriptPubKey = StringType(required=True)
    address = StringType(required=True)


class Tx(JmResponse):
    """
    Represent a transaction as returned by `directsend` :class:`RpcMethod`.
    """

    hex = StringType(required=True)
    txid = StringType(required=True)
    inputs = ListType(ModelType(Input), required=True)
    outputs = ListType(ModelType(Output), required=True)
    nLockTime = IntType(required=True)
    nVersion = IntType(required=True)


class DirectSend(JmResponse):
    """
    `directsend` :class:`RpcMethod` response content.

    Fields:

    * tx_info: Information about the Bitcoin transaction.
    """

    tx_info = ModelType(Tx, required=True, deserialize_from='txinfo')


class Session(JmResponse):
    """
    `session` :class:`RpcMethod` response content.

    Fields:

    * session: True if and only if there is an active authentication and unlocked wallet.
    * maker_running: True if a yield generator is running, False otherwise.
    * coinjoin_in_process: True if a taker coinjoin is in progress, False otherwise.
    * wallet_name: Currently loaded wallet.
    """

    session = BooleanType(required=True)
    maker_running = BooleanType(required=True)
    coinjoin_in_process = BooleanType(required=True)
    wallet_name = StringType(required=True)


class ConfigGet(JmResponse):
    """
    `configget` :class:`RpcMethod` response content.
    """

    config_value = StringType(required=True, deserialize_from='configvalue')
