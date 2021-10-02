from setuptools import setup

setup(name='jmrpc',
      version='0.1',
      description='A simple and high-livel JSON-RPC client for JoinMarket.',
      url='https://github.com/PulpCattel/jmrpc',
      zip_safe=False,
      packages=['jmrpc'],
      install_requires=['requests', 'schematics'],
      python_requires=">=3.7",
      extras_require={
          'dev': ['pytest', 'mypy', 'pylint', 'types-requests']})
