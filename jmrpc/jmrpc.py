"""
A simple and high level JSON-RPC client library for JoinMarket
"""
from asyncio import sleep
from collections import namedtuple
from enum import Enum
from logging import getLogger, DEBUG
from ssl import create_default_context
from typing import Any, Dict, Optional, AsyncGenerator

from aiohttp import ClientSession, ClientResponse, TCPConnector, ClientWebSocketResponse
from ujson import loads, dumps

from jmrpc.jmdata import ListWallets, CreateWallet, LockWallet, \
    UnlockWallet, DisplayWallet, GetAddress, ListUtxos, DirectSend, DoCoinjoin
from jmrpc.jmdata import Session

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
    JoinMarket supported JSON-RPC methods:

    * **listwallets**: List currently available wallet files
    * **createwallet**: Make a new wallet
    * **unlockwallet**: Open an existing wallet using a password
    * **lockwallet**: Stop the wallet service for the current wallet
    * **displaywallet**: Get JSON representation of wallet contents
    * **getaddress**: Get a new address for deposits
    * **listutxos**: List details of all utxos currently in the wallet.
    * **directsend**: Make a bitcoin payment from the wallet, without coinjoin
    * **docoinjoin**: Initiate a coinjoin as taker
    * **session**: Check the status and liveness of the session
    * **maker-start**: Starts the yield generator/maker service for the given wallet
    * **maker-stop**: Stops the yield generator/maker service if currently running for the given wallet
    """

    _METHOD_DATA = namedtuple('_METHOD_DATA', ('route', 'name'))
    _API_VERSION_STRING = "/api/v1"

    LIST_WALLETS = _METHOD_DATA(_API_VERSION_STRING + '/wallet/all', 'listwallets')
    CREATE_WALLET = _METHOD_DATA(_API_VERSION_STRING + '/wallet/create', 'createwallet')
    UNLOCK_WALLET = _METHOD_DATA(_API_VERSION_STRING + '/wallet/{walletname}/unlock', 'unlockwallet')
    LOCK_WALLET = _METHOD_DATA(_API_VERSION_STRING + '/wallet/{walletname}/lock', 'lockwallet')
    DISPLAY_WALLET = _METHOD_DATA(_API_VERSION_STRING + '/wallet/{walletname}/display', 'displaywallet')
    GET_ADDRESS = _METHOD_DATA(_API_VERSION_STRING + '/wallet/{walletname}/address/new/{mixdepth}', 'getaddress')
    LIST_UTXOS = _METHOD_DATA(_API_VERSION_STRING + '/wallet/{walletname}/utxos', 'listutxos')
    DIRECT_SEND = _METHOD_DATA(_API_VERSION_STRING + '/wallet/{walletname}/taker/direct-send', 'directsend')
    DO_COINJOIN = _METHOD_DATA(_API_VERSION_STRING + '/wallet/{walletname}/taker/coinjoin', 'docoinjoin')
    SESSION = _METHOD_DATA(_API_VERSION_STRING + '/session', 'session')
    MAKER_START = _METHOD_DATA(_API_VERSION_STRING + '/wallet/{walletname}/maker/start', 'maker-start')
    MAKER_STOP = _METHOD_DATA(_API_VERSION_STRING + '/wallet/{walletname}/maker/stop', 'maker-stop')

    def __str__(self):
        return f'Name: {self.value.name}\nRoute: {self.value.route}'


class JmRpc:
    """
    Client object to interact with JoinMarket JSON-RPC server

    Can be used with context manager to cleanly close the session.

    >>> async with JmRpc() as jmrpc:
    ...     print(await jmrpc.session())
    ...
    {"session": false, "maker_running": false, "coinjoin_in_process": false, "wallet_name": "None"}
    """

    __slots__ = ('_id_count', '_session', '_endpoint', '_ws')

    def __init__(self,
                 session: Optional[ClientSession] = None,
                 endpoint: str = 'https://127.0.0.1:28183',
                 ssl_verify: str = '/home/user/.joinmarket/ssl') -> None:
        """
        Initialize JSON-RPC client, if no `session` is provided, aiohttp.ClientSession() is used.

        If no `endpoint` is provided, JoinMarket default one is used.

        `ssl_verify` should be a path that points to {cert, key}.pem directory,
        by default uses JoinMarket default datadir.
        """

        self._id_count = 0
        if session:
            self._session = session
        else:
            ssl_context = create_default_context(cafile=f'{ssl_verify}/cert.pem')
            ssl_context.load_cert_chain(f'{ssl_verify}/cert.pem',
                                        f'{ssl_verify}/key.pem')
            self._session = ClientSession(json_serialize=dumps,
                                          headers=HEADERS,
                                          connector=TCPConnector(ssl=ssl_context))
        self._endpoint = endpoint
        self._ws: Optional[ClientWebSocketResponse] = None

    async def __aenter__(self) -> 'JmRpc':
        await self.start_ws()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start_ws(self) -> None:
        self._ws = await self._session.ws_connect('wss://127.0.0.1:28283')

    async def close(self) -> None:
        """
        Close the session and waits 250ms for graceful shutdown.

        https://docs.aiohttp.org/en/stable/client_advanced.html#graceful-shutdown
        """
        await self._ws.close()
        await self._session.close()
        await sleep(0.25)

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

    async def ws_read(self) -> AsyncGenerator[Any, Any]:
        """
        Read from websocket and yields each message.
        """
        if self._ws is None:
            raise JmRpcError('Websocket is not initialized, if you are not using a context manager'
                             'you have to await jmrpc.start_ws() manually')
        async for msg in self._ws:
            yield msg

    async def ws_send(self, msg: str) -> None:
        if self._ws is None:
            raise JmRpcError('Websocket is not initialized, if you are not using a context manager'
                             'you have to call jmrpc.start_ws() manually')
        if not isinstance(msg, str):
            raise TypeError(f'Expecting string, got {type(msg)}')
        await self._ws.send_str(msg)

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

    @staticmethod
    async def _handle_response(response: ClientResponse) -> Dict:
        """
        Raise exception for any status code different than 200.
        Return JSON response.
        """
        if response.status != 200:
            content = await response.text('utf-8')
            for member in JmRpcErrorType:
                if content != member.value:
                    continue
                raise JmRpcError(response.status, content)
            response.raise_for_status()
        return await response.json(encoding='utf-8', loads=loads)

    async def _get(self,
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
        self._id_count += 1
        async with self._session.get(self._get_complete_url(method, route_args),
                                     **kwargs) as response:
            return await self._handle_response(response)

    async def _post(self,
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
        self._id_count += 1
        async with self._session.post(self._get_complete_url(method, route_args),
                                      json=self._build_payload(body),
                                      **kwargs) as response:
            return await self._handle_response(response)

    async def list_wallets(self, **kwargs) -> ListWallets:
        """
        Call `listwallets` :class:`RpcMethod`
        """
        return ListWallets(await self._get(RpcMethod.LIST_WALLETS,
                                           **kwargs))

    async def create_wallet(self,
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
        response = CreateWallet(await self._post(RpcMethod.CREATE_WALLET,
                                                 body,
                                                 **kwargs))
        self._cache_token(response.token)
        await self.ws_send(response.token)
        return response

    async def unlock_wallet(self, wallet_name: str, pwd: str, **kwargs) -> UnlockWallet:
        """
        Call `unlockwallet` POST :class:`RpcMethod`
        """
        response = UnlockWallet(await self._post(RpcMethod.UNLOCK_WALLET,
                                                 {'password': pwd},
                                                 {'walletname': wallet_name},
                                                 **kwargs))
        self._cache_token(response.token)
        await self.ws_send(response.token)
        return response

    async def lock_wallet(self, wallet_name: str, **kwargs) -> LockWallet:
        """
        Call `lockwallet` GET :class:`RpcMethod`
        """
        return LockWallet(await self._get(RpcMethod.LOCK_WALLET,
                                          {'walletname': wallet_name},
                                          **kwargs))

    async def display_wallet(self, wallet_name: str, **kwargs) -> DisplayWallet:
        """
        Call `displaywallet` GET :class:`RpcMethod`
        """
        return DisplayWallet(await self._get(RpcMethod.DISPLAY_WALLET,
                                             {'walletname': wallet_name},
                                             **kwargs))

    async def get_address(self, wallet_name: str, mixdepth: str, **kwargs) -> GetAddress:
        """
        Call `getaddress` GET :class:`RpcMethod`
        """
        return GetAddress(await self._get(RpcMethod.GET_ADDRESS,
                                          {'walletname': wallet_name,
                                           'mixdepth': mixdepth},
                                          **kwargs))

    async def list_utxos(self, wallet_name: str, **kwargs) -> ListUtxos:
        """
        Call `listutxos` GET :class:`RpcMethod`
        """
        return ListUtxos(await self._get(RpcMethod.LIST_UTXOS,
                                         {'walletname': wallet_name},
                                         **kwargs))

    async def direct_send(self,
                          wallet_name: str,
                          mixdepth: str,
                          amount_sats: int,
                          destination: str,
                          **kwargs) -> DirectSend:
        """
        Call `directsend` POST :class:`RpcMethod`
        """
        return DirectSend(await self._post(RpcMethod.DIRECT_SEND,
                                           {'mixdepth': mixdepth,
                                            'amount_sats': amount_sats,
                                            'destination': destination},
                                           {'walletname': wallet_name},
                                           **kwargs
                                           ))

    async def do_coinjoin(self,
                          wallet_name: str,
                          mixdepth: str,
                          amount: int,
                          counterparties: int,
                          destination: str,
                          **kwargs) -> DoCoinjoin:
        """
        Call `docoinjoin` POST :class:`RpcMethod`
        """
        return DoCoinjoin(await self._post(RpcMethod.DO_COINJOIN,
                                           {'mixdepth': mixdepth,
                                            'amount': amount,
                                            'counterparties': counterparties,
                                            'destination': destination},
                                           {'walletname': wallet_name},
                                           **kwargs
                                           ))

    async def session(self, **kwargs) -> Session:
        """
        Call `session` GET :class:`RpcMethod`
        """
        return Session(await self._get(RpcMethod.SESSION,
                                       **kwargs))

    async def maker_start(self,
                          wallet_name: str,
                          tx_fee: int,
                          cjfee_a: int,
                          cjfee_r: str,
                          order_type: str,
                          min_size: str,
                          **kwargs) -> None:
        """
        Call `maker-start` POST :class:`RpcMethod`
        """
        await self._post(RpcMethod.MAKER_START,
                         {'txfee': tx_fee,
                          'cjfee_a': cjfee_a,
                          'cjfee_r': cjfee_r,
                          'ordertype': order_type,
                          'minsize': min_size},
                         {'walletname': wallet_name},
                         **kwargs
                         )

    async def maker_stop(self, wallet_name: str, **kwargs) -> None:
        """
        Call `maker-stop` GET :class:`RpcMethod`
        """
        await self._get(RpcMethod.MAKER_STOP,
                        {'walletname': wallet_name},
                        **kwargs)
