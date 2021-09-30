"""
A simple and high level JSON-RPC client library for JoinMarket
"""
from collections import namedtuple
from enum import Enum
from logging import getLogger, DEBUG
from typing import Any, Dict, Optional

from requests import Session, Response

from jmrpc.jmdata import GetSession
from jmrpc.jmdata import ListWallets, CreateWallet, LockWallet, \
    UnlockWallet, DisplayWallet, GetAddress, ListUtxos, DirectSend, DoCoinjoin, MakerStartStop

HEADERS = {"User-Agent": "jmrpc",
           "Content-Type": "application/json",
           "Accept": "application/json"}

# TODO: Implement logging
LOGGER = getLogger('jmrpc')
LOGGER.setLevel(DEBUG)


class JmRpcError(Exception):
    """
    JoinMarket JSON-RPC custom exception
    """


class JmRpcErrorType(Enum):
    """
    Type of JoinMarket JSON-RPC error
    """
    NOT_AUTHORIZED = 'Invalid credentials.'
    NO_WALLET_FOUND = 'No wallet loaded.'
    BACKEND_NOT_READY = 'Backend daemon not available'
    INVALID_REQUEST_FORMAT = 'Invalid request format.'
    SERVICE_ALREADY_STARTED = 'Service already started.'
    WALLET_ALREADY_UNLOCKED = 'Wallet already unlocked.'
    SERVICE_NOT_STARTED = 'Service cannot be stopped as it is not running.'


class RpcMethod(Enum):
    """
    JoinMarket supported JSON-RPC method

    * **listwallets**: List currently available wallet files
    * **createwallet**: Make a new wallet
    * **unlockwallet**: Open an existing wallet using a password
    * **lockwallet**: Stop the wallet service for the current wallet
    * **displaywallet**: Get JSON representation of wallet contents for wallet named `walletname`
    * **getaddress**: Get a new address for deposits
    * **listutxos**: TODO
    * **directsend**: Make a bitcoin payment from the wallet, without coinjoin
    * **docoinjoin**: TODO
    * **session**: Check the status and liveness of the session
    * **maker-start**: Starts the yield generator/maker service for the given wallet
    * **maker-stop**: Stops the yieldgenerator/maker service if currently running for the given wallet
    """

    _METHOD_DATA = namedtuple('_METHOD_DATA', ('route', 'name'))

    LIST_WALLETS = _METHOD_DATA('/api/v1/wallet/all', 'listwallets')
    CREATE_WALLET = _METHOD_DATA('/api/v1/wallet/create', 'createwallet')
    UNLOCK_WALLET = _METHOD_DATA('/api/v1/wallet/{walletname}/unlock', 'unlockwallet')
    LOCK_WALLET = _METHOD_DATA('/api/v1/wallet/{walletname}/lock', 'lockwallet')
    DISPLAY_WALLET = _METHOD_DATA('/api/v1/wallet/{walletname}/display', 'displaywallet')
    GET_ADDRESS = _METHOD_DATA('/api/v1/wallet/{walletname}/address/new/{mixdepth}', 'getaddress')
    LIST_UTXOS = _METHOD_DATA('/api/v1/wallet/{walletname}/utxos', 'listutxos')
    DIRECT_SEND = _METHOD_DATA('/api/v1/wallet/{walletname}/taker/direct-send', 'directsend')
    DO_COINJOIN = _METHOD_DATA('/api/v1/wallet/{walletname}/taker/coinjoin', 'docoinjoin')
    SESSION = _METHOD_DATA('/api/v1/session', 'session')
    MAKER_START = _METHOD_DATA('/api/v1/wallet/{walletname}/maker/start', 'maker-start')
    MAKER_STOP = _METHOD_DATA('/api/v1/wallet/{walletname}/maker/stop', 'maker-stop')

    def __str__(self):
        return f'Name: {self.value.name}\nRoute: {self.value.route}'


class JmRpc:
    """
    Client object to interact with JoinMarket JSON-RPC server

    Can be used with context manager to cleanly close the session.

    >>> with JmRpc() as jmrpc:
    ...    jmrpc._get(RpcMethod.LIST_WALLETS)
    """

    __slots__ = ('_id_count', '_session', '_endpoint')

    def __init__(self,
                 session: Optional[Session] = None,
                 endpoint: str = 'https://127.0.0.1:28183') -> None:
        """
        Initialize JSON-RPC client, if no `session` is provided, requests.Session() is used.
        If no `endpoint` is provided, JoinMarket default one is used.
        """
        self._id_count = 0
        if session:
            self._session = session
        else:
            self._session = Session()
            self._session.headers.update(HEADERS)
            # SSL verification hardcoded here for now, or use a custom session
            self._session.verify = '/home/user/.joinmarket/ssl/cert.pem'
        self._endpoint = endpoint

    def __enter__(self) -> 'JmRpc':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        """
        Close the session.
        """
        self._session.close()

    @staticmethod
    def _validate_method_type(method: RpcMethod) -> None:
        """
        Given a :class:`RpcMethod`, raises exception if it's of different type.
        """
        if not isinstance(method, RpcMethod):
            raise TypeError(f'Expected RpcMethod instance, got {type(method)} instead')

    @property
    def id_count(self) -> int:
        """
        Return current :class:`JmRpc` ID count.
        """
        return self._id_count

    @property
    def endpoint(self) -> str:
        """
        :return: :class:`JmRpc` endpoint
        """
        return self._endpoint

    @property
    def token(self) -> bool:
        """
        :return: True if we currently have a token, False otherwise.
        """
        return 'Authorization' in self._session.headers.keys()

    def _cache_token(self, token: str) -> None:
        """
        Cache token for the session.

        Server maintains the token for as long as the daemon is active (i.e.
        no expiry currently implemented), or until the user switches
        to a new wallet.
        """
        self._session.headers.update({'Authorization': f'Bearer {token}'})

    def _build_payload(self, body: Dict) -> Dict[str, Any]:
        """
        Build payload for JSON-RPC request.
        """
        return {'jsonrpc': '2.0',
                'id': self._id_count,
                **body}

    def _get_complete_url(self, method: RpcMethod, route_args: Optional[Dict]) -> str:
        """
        Given a :class:`RpcMethod` return complete url for RPC request
        """
        if route_args is None:
            return self._endpoint + method.value.route
        return self._endpoint + method.value.route.format(**route_args)

    def _handle_response(self, response: Response) -> Dict:
        """
        Raise exception for any status code different than 200.
        Return JSON response.
        """
        self._id_count += 1
        if response.status_code != 200:
            content = response.content.decode('utf-8')
            for member in JmRpcErrorType:
                if content != member.value:
                    continue
                raise JmRpcError(response.status_code, content)
            response.raise_for_status()
        return response.json()

    def _get(self,
             method: RpcMethod,
             route_args: Optional[Dict] = None,
             **kwargs) -> Dict:
        """
        Perform GET request and return response.

        :param method: :class:`RpcMethod` to request
        :param route_args: Arguments to complete the :class:`RpcMethod` route
        :param kwargs: Extra arguments for session.get()
        """
        self._validate_method_type(method)
        with self._session.get(self._get_complete_url(method, route_args),
                               **kwargs) as response:
            return self._handle_response(response)

    def _post(self,
              method: RpcMethod,
              body: Dict,
              route_args: Optional[Dict] = None,
              **kwargs) -> Dict:
        """
        Perform POST request and return response converted into JSON.

        :param method: :class:`RpcMethod` to request
        :param body: Body of the post request
        :param route_args: Arguments to add to RpcMethod route
        :param kwargs: Extra arguments for session.post()
        """
        self._validate_method_type(method)
        with self._session.post(self._get_complete_url(method, route_args),
                                json=self._build_payload(body),
                                **kwargs) as response:
            return self._handle_response(response)

    def list_wallets(self, **kwargs) -> ListWallets:
        """
        Call `listwallets` :class:`RpcMethod`
        """
        return ListWallets(self._get(RpcMethod.LIST_WALLETS,
                                     **kwargs))

    def create_wallet(self,
                      wallet_name: str,
                      password: str,
                      wallet_type: str,
                      **kwargs) -> CreateWallet:
        """
        Call `createwallet` :class:`RpcMethod`
        """
        body = {'walletname': wallet_name,
                'password': password,
                'wallettype': wallet_type}
        response = CreateWallet(self._post(RpcMethod.CREATE_WALLET,
                                           body,
                                           **kwargs))
        self._cache_token(response.token)
        return response

    def unlock_wallet(self, wallet_name: str, pwd: str, **kwargs) -> UnlockWallet:
        """
        Call `unlockwallet` POST :class:`RpcMethod`
        """
        response = UnlockWallet(self._post(RpcMethod.UNLOCK_WALLET,
                                           {'password': pwd},
                                           {'walletname': wallet_name},
                                           **kwargs))
        self._cache_token(response.token)
        return response

    def lock_wallet(self, wallet_name: str, **kwargs) -> LockWallet:
        """
        Call `lockwallet` GET :class:`RpcMethod`
        """
        return LockWallet(self._get(RpcMethod.LOCK_WALLET,
                                    {'walletname': wallet_name},
                                    **kwargs))

    def display_wallet(self, wallet_name: str, **kwargs) -> DisplayWallet:
        """
        Call `displaywallet` GET :class:`RpcMethod`
        """
        return DisplayWallet(self._get(RpcMethod.DISPLAY_WALLET,
                                       {'walletname': wallet_name},
                                       **kwargs))

    def get_address(self, wallet_name: str, mixdepth: str, **kwargs) -> GetAddress:
        """
        Call `getaddress` GET :class:`RpcMethod`
        """
        return GetAddress(self._get(RpcMethod.GET_ADDRESS,
                                    {'walletname': wallet_name,
                                     'mixdepth': mixdepth},
                                    **kwargs))

    def list_utxos(self, wallet_name: str, **kwargs) -> ListUtxos:
        """
        Call `listutxos` GET :class:`RpcMethod`
        """
        return ListUtxos(self._get(RpcMethod.LIST_UTXOS,
                                   {'walletname': wallet_name},
                                   **kwargs))

    def direct_send(self,
                    wallet_name: str,
                    mixdepth: str,
                    amount_sats: int,
                    destination: str,
                    **kwargs) -> DirectSend:
        """
        Call `directsend` POST :class:`RpcMethod`
        """
        return DirectSend(self._post(RpcMethod.DIRECT_SEND,
                                     {'mixdepth': mixdepth,
                                      'amount_sats': amount_sats,
                                      'destination': destination},
                                     {'walletname': wallet_name},
                                     **kwargs
                                     ))

    def do_coinjoin(self,
                    wallet_name: str,
                    mixdepth: str,
                    amount: int,
                    counterparties: int,
                    destination: str,
                    **kwargs) -> DoCoinjoin:
        """
        Call `docoinjoin` POST :class:`RpcMethod`
        """
        return DoCoinjoin(self._post(RpcMethod.DO_COINJOIN,
                                     {'mixdepth': mixdepth,
                                      'amount': amount,
                                      'counterparties': counterparties,
                                      'destination': destination},
                                     {'walletname': wallet_name},
                                     **kwargs
                                     ))

    def session(self, **kwargs) -> GetSession:
        """
        Call `session` GET :class:`RpcMethod`
        """
        return GetSession(self._get(RpcMethod.SESSION,
                                    **kwargs))

    def maker_start(self,
                    wallet_name: str,
                    tx_fee: int,
                    cjfee_a: int,
                    cjfee_r: str,
                    order_type: str,
                    min_size: str,
                    **kwargs) -> MakerStartStop:
        """
        Call `maker-start` POST :class:`RpcMethod`
        """
        return MakerStartStop(self._post(RpcMethod.MAKER_START,
                                         {'txfee': tx_fee,
                                          'cjfee_a': cjfee_a,
                                          'cjfee_r': cjfee_r,
                                          'ordertype': order_type,
                                          'minsize': min_size},
                                         {'walletname': wallet_name},
                                         **kwargs
                                         ))

    def maker_stop(self, wallet_name: str, **kwargs) -> MakerStartStop:
        """
        Call `maker-stop` GET :class:`RpcMethod`
        """
        return MakerStartStop(self._get(RpcMethod.MAKER_STOP,
                                        {'walletname': wallet_name},
                                        **kwargs))
