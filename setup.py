from setuptools import setup

setup(name='jmrpc',
      version='0.1',
      description='A simple and high-livel JSON-RPC client library for JoinMarket.',
      url='https://github.com/PulpCattel/jmrpc',
      zip_safe=False,
      packages=['jmrpc'],
      install_requires=['aiohttp[speedups]>=3.7.3', 'schematics>=2.1.1', 'ujson>=4.2.0'],
      python_requires=">=3.7",
      extras_require={
          'dev': ['pytest', 'pytest-asyncio', 'mypy', 'pylint', 'types-requests']})
