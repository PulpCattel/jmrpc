# Jmrpc (WIP)

A simple, high-level and fully asynchronous JSON-RPC client for [JoinMarket](https://github.com/JoinMarket-Org/joinmarket-clientserver), for now mostly meant to test https://github.com/JoinMarket-Org/joinmarket-clientserver/pull/996.

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

```
>>> from jmrpc.jmrpc import JmRpc
>>> async with JmRpc() as jmrpc:
...    response = await jmrpc.list_wallets()
```
JoinMarket server uses HTTPS, and by default this library (for now) looks for cert.pem file in `/home/user/.joinmarket/ssl/`.

For easier testing you may want to skip SSL cert verification, e.g.:

```
>>> with JmRpc() as jmrpc:
...    response = await jmrpc.list_wallets(ssl=False)
```

For more info see [here](https://docs.aiohttp.org/en/stable/client_advanced.html#ssl-control-for-tcp-sockets).

`response` is a [model representation](https://github.com/schematics/schematics) of the response content from JoinMarket.

```
>>> response['wallets']
['wallet.jmdat', 'wallet1.jmdat', 'wallet2.jmdat']
>>> response.wallets
['wallet.jmdat', 'wallet1.jmdat', 'wallet2.jmdat']
>>> response.dict
{'wallets': ['wallet.jmdat', 'wallet1.jmdat', 'wallet2.jmdat']}
```
