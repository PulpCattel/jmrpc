"""
Objects for JoinMarket JSON-RPC response content
"""
from json import loads, JSONDecodeError, dumps
from typing import Dict, List, Any


class JmDeserializeError(Exception):
    """
    Thrown when the content we got from JoinMarket server is not expected data.
    """


class JmResponse:
    """
    Base object for data returned by JoinMarket server.
    """

    __slots__ = ('succeed', 'status')

    def __init__(self, json: Dict[str, Any]):
        if not isinstance(json['succeed'], bool):
            raise JmDeserializeError
        if not isinstance(json['status'], int):
            raise JmDeserializeError
        # whatever the request was successful
        self.succeed: bool = json['succeed']
        # http status code
        self.status: int = json['status']

    def __getitem__(self, item):
        return getattr(self, item)

    def __str__(self):
        return dumps(self.dict)

    @property
    def dict(self) -> Dict:
        """
        Dictionary representation.
        """
        return {attr: self[attr] for attr in self.__slots__}


class ListWallets(JmResponse):
    """
    `listwallet` :class:`RpcMethod` response content
    """

    __slots__ = ('wallets',)

    def __init__(self, json):
        super().__init__(json)
        if not isinstance(json['wallets'], list):
            raise JmDeserializeError
        # each filenames in `datadir/wallets` (filename only, including `.jmdat`, not full path).
        self.wallets: List[str] = json['wallets']


class CreateWallet(JmResponse):
    """
    `createwallet` :class:`RpcMethod` response content
    """

    __slots__ = ('wallet_name', 'already_loaded', 'token', 'seedphrase')

    def __init__(self, json):
        super().__init__(json)
        if not isinstance(json['walletname'], str):
            raise JmDeserializeError
        if not isinstance(json['already_loaded'], bool):
            raise JmDeserializeError
        if not isinstance(json['token'], str):
            raise JmDeserializeError
        if not isinstance(json['seedphrase'], str):
            raise JmDeserializeError
        # The filename for the wallet created on disk in `datadir/wallets`.
        self.wallet_name: str = json['walletname']
        # False for successful creation.
        self.already_loaded: bool = json['already_loaded']
        # the created JWT token.
        self.token: str = json['token']
        # The BIP39 12 word seedphrase of the newly created JoinMarket wallet.
        self.seedphrase: str = json['seedphrase']


class UnlockWallet(JmResponse):
    """
    `unlockwallet` :class:`RpcMethod` response content
    """

    __slots__ = ('wallet_name', 'already_loaded', 'token')

    def __init__(self, json):
        super().__init__(json)
        if not isinstance(json['walletname'], str):
            raise JmDeserializeError
        if not isinstance(json['already_loaded'], bool):
            raise JmDeserializeError
        if not isinstance(json['token'], str):
            raise JmDeserializeError
        # The filename for the wallet created on disk in `datadir/wallets`.
        self.wallet_name: str = json['walletname']
        # False in case there is no currently unlocked wallet,
        # and this wallet is unlocked successfully.
        # True in case the same wallet is already unlocked,
        # or another wallet is currently unlocked (note that this is not an error response).
        self.already_loaded: bool = json['already_loaded']
        # The created JWT token.
        self.token: str = json['token']


class LockWallet(JmResponse):
    """
    lockwallet` :class:`RpcMethod` response content
    """

    __slots__ = ('walletname', 'already_locked')

    def __init__(self, json: Dict[str, Any]):
        super().__init__(json)
        if not isinstance(json['walletname'], str):
            raise JmDeserializeError
        if not isinstance(json['already_locked'], bool):
            raise JmDeserializeError
        # The filename for the wallet created on disk in `datadir/wallets`.
        self.walletname: str = json['walletname']
        # False if there was an unlocked wallet, and we locked it, otherwise true.
        self.already_locked: bool = json['already_locked']


class DisplayWallet(JmResponse):
    """
    `displaywallet` :class:`RpcMethod` response content
    """

    __slots__ = ('wallet_name', 'wallet_info')

    def __init__(self, json: Dict[str, Any]):
        super().__init__(json)
        if not isinstance(json['walletname'], str):
            raise JmDeserializeError
        if not isinstance(json['walletinfo'], dict):
            raise JmDeserializeError
        self.wallet_name = json['walletname']
        self.wallet_info = json['walletinfo']


class GetAddress(JmResponse):
    """
    `getaddress` :class:`RpcMethod` response content
    """

    __slots__ = ('address',)

    def __init__(self, json: Dict[str, Any]):
        super().__init__(json)
        if not isinstance(json['address'], str):
            raise JmDeserializeError
        # The first unused address in the *external* branch of the given account/mixdepth.
        self.address: str = json['address']


class ListUtxos(JmResponse):
    """
    `listutxos` :class:`RpcMethod` response content
    """

    __slots__ = ('utxos',)

    def __init__(self, json: Dict[str, Any]):
        super().__init__(json)
        if not isinstance(json['utxos'], dict):
            raise JmDeserializeError
        # All utxos currently owned by the wallet.
        self.utxos: Dict = json['utxos']


class DirectSend(JmResponse):
    """
    `directsend` :class:`RpcMethod` response content
    """

    __slots__ = ('walletname', 'txinfo')

    def __init__(self, json: Dict[str, Any]):
        super().__init__(json)
        if not isinstance(json['walletname'], str):
            raise JmDeserializeError
        if not isinstance(json['txinfo'], str):
            raise JmDeserializeError
        try:
            txinfo: Dict = loads(json['txinfo'])
        except JSONDecodeError as err:
            raise JmDeserializeError from err
        if not isinstance(txinfo, dict):
            raise JmDeserializeError
        # The filename for the wallet created on disk in `datadir/wallets`.
        self.walletname: str = json['walletname']
        self.txinfo: Dict = txinfo


class DoCoinjoin(JmResponse):
    """
    `docoinjoin` :class:`RpcMethod` response content
    """

    __slots__ = ('coinjoin_started',)

    def __init__(self, json: Dict[str, Any]):
        super().__init__(json)
        if not isinstance(json['coinjoin_started'], bool):
            raise JmDeserializeError
        # This only indicates start OK, not completion.
        self.coinjoin_started: bool = json['coinjoin_started']


class GetSession(JmResponse):
    """
    `session` :class:`RpcMethod` response content
    """

    __slots__ = ('session', 'maker_running', 'coinjoin_in_process', 'wallet_name')

    def __init__(self, json: Dict[str, Any]):
        super().__init__(json)
        if not isinstance(json['session'], bool):
            raise JmDeserializeError
        if not isinstance(json['maker_running'], bool):
            raise JmDeserializeError
        if not isinstance(json['coinjoin_in_process'], bool):
            raise JmDeserializeError
        if not isinstance(json['wallet_name'], str):
            raise JmDeserializeError
        # True if and only if there is an active authentication and unlocked wallet.
        self.session: bool = json['session']
        self.maker_running: bool = json['maker_running']
        self.coinjoin_in_process: bool = json['coinjoin_in_process']
        # Joinmarket internal wallet name, `joinmarket-<hex encoded 3 byte hash identifier>`.
        self.wallet_name: str = json['wallet_name']


class MakerStartStop(JmResponse):
    """
    `maker-start` and `maker-stop` :class:`RpcMethod` response content
    """

    __slots__ = ('walletname',)

    def __init__(self, json: Dict[str, Any]):
        super().__init__(json)
        if not isinstance(json['walletname'], str):
            raise JmDeserializeError
        # Joinmarket internal wallet name, `joinmarket-<hex encoded 3 byte hash identifier>`.
        self.walletname: str = json['walletname']
