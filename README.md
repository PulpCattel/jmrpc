# Jmrpc (WIP)

A simple, high-level, and fully asynchronous JSON-RPC client for [JoinMarket](https://github.com/JoinMarket-Org/joinmarket-clientserver), for now mostly meant to test https://github.com/JoinMarket-Org/joinmarket-clientserver/pull/996.

# Requirements

* This JoinMarket [branch](https://github.com/abhishek0405/joinmarket-clientserver/tree/rpc-api-2).
* A configured JoinMarket [JSON-RPC server](https://github.com/abhishek0405/joinmarket-clientserver/blob/rpc-api-2/docs/JSON-RPC-API-using-jmwalletd.md).
* Python >= 3.7

# Installation

```bash
git clone https://github.com/PulpCattel/jmrpc
cd jmrpc
pip3 install -e .
```

# Usage

```python3
from asyncio import run
from jmrpc import JmRpc

async def main() -> None:
    async with JmRpc() as jmrpc:
        response = await jmrpc.list_wallets()

if __name__ == '__main__':
    run(main())
```

JoinMarket server uses HTTPS, and by default this library (for now) looks for cert.pem file in `/home/user/.joinmarket/ssl/`.

For easier testing you may want to skip SSL cert verification, e.g.:

```python3
response = await jmrpc.list_wallets(ssl=False)
```

For more info see [here](https://docs.aiohttp.org/en/stable/client_advanced.html#ssl-control-for-tcp-sockets).

`response` is a [model representation](https://github.com/schematics/schematics) of the response content from JoinMarket.

```python3
print(response['wallets'])
print(response.wallets)
print(response.dict)
```

Output:

```bash
['wallet.jmdat', 'wallet1.jmdat', 'wallet2.jmdat']
['wallet.jmdat', 'wallet1.jmdat', 'wallet2.jmdat']
{'wallets': ['wallet.jmdat', 'wallet1.jmdat', 'wallet2.jmdat']}
```

JoinMarket offers a websocket, which serves notifications to all authenticated clients.

```python3
from asyncio import run
from jmrpc import JmRpc

async def main() -> None:
    # Websocket automatically connected when using a context manager.
    async with JmRpc() as jmrpc:
        # Unlock and Create both automatically authenticate to the websocket.
        await jmrpc.unlock_wallet('wallet.jmdat', 'password')
        # Now we can wait for notifications.
        async for msg in jmrpc.ws_read():
            # Like the HTTP response, `msg` here is an object representation
            # of the data read from the websocket.
            print(msg)
            print(msg.dict)

if __name__ == '__main__':
    run(main())
```