# Jmrpc (WIP)

A simple and high-level JSON-RPC client for [JoinMarket](https://github.com/JoinMarket-Org/joinmarket-clientserver), for now mostly meant to test https://github.com/JoinMarket-Org/joinmarket-clientserver/pull/996.

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
>>> with JmRpc() as jmrpc:
...    response = jmrpc.list_wallets()
```
JoinMarket server uses HTTPS, and by default this library (for now) looks for cert.pem file in `/home/user/.joinmarket/ssl/cert.pem`.

For easier testing you may want to skip SSL cert verification, e.g.:

```
>>> with JmRpc() as jmrpc:
...    response = jmrpc.list_wallets(verify=False)
```

For more info see [here](https://docs.python-requests.org/en/latest/user/advanced/#client-side-certificates).

`response` is an object representation of the response content from JoinMarket.

```
>>> response['wallets']
['wallet.jmdat', 'wallet1.jmdat', 'wallet2.jmdat']
>>> response.wallets
['wallet.jmdat', 'wallet1.jmdat', 'wallet2.jmdat']
>>> response.status
200
>>> response.dict
{'wallets': ['wallet.jmdat', 'wallet1.jmdat', 'wallet2.jmdat']}
```
