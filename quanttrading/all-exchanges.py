# -*- coding: utf-8 -*-

from asyncio import gather, run, sleep
import pandas_ta as ta
import pandas as pd
from abc import ABC

import os
import sys
from pprint import pprint
from datetime import datetime
import time

root = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(root + "/python")


import ccxt.async_support as ccxt  # noqa: E402


async def show_exchanges():
    """
    """
    print("CCXT Version:", ccxt.__version__)

    for exchange_id in ccxt.exchanges:
        try:
            exchange = getattr(ccxt, exchange_id)()
            print(exchange_id)
            # do what you want with this exchange
            # pprint(dir(exchange))
        except Exception as e:
            pprint(e)


class ExchangeBase(ABC):

    def __init__(self, exchange) -> None:
        super().__init__()
        self.exchange = exchange
        
    async def fetch_ohlcv(self, symbol="BTC/USDT", timeframe="1m",
                        since=None, limit=None):

        # since = exchange.milliseconds() - 1000000
        seconds = self.exchange.seconds() - 600
        since = seconds * 1000
        print(f"since is {since}")

        try:
            # Max 300 Candles
            candles = await self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
            pprint(candles)
        except Exception as err:
            print(err)

    async def fetch_ticker(self, symbol='BTC/USDT'):
        """
        """
        try:
            # tickers = exchange.fetch_tickers(symbols)
            ticker = await self.exchange.fetch_ticker(symbol)
            pprint(ticker)
        except Exception as err:
            print(err)

    async def fetch_trades(self, symbol='BTC/USDT', since=None, limit=3):
        """
        
        """
        try:
            # trades = await self.exchange.fetch_trades(symbol, since, limit)
            my_trades = await self.exchange.fetch_my_trades(symbol, since, limit)
            # print(f"****** trades: {'******' * 10}")
            # pprint(trades)

            print(f"****** my trades: {'******' * 10}")
            pprint(my_trades)
        except Exception as err:
            print(err)


    async def run_ohlcv_loop(self, symbol, timeframe, limit):
        since = None
        fast = 12
        slow = 26
        signal = 9
        while True:
            try:
                ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
                await sleep(2)
                if len(ohlcv):
                    df = pd.DataFrame(ohlcv, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                    print('---------- df before cat------------------------------------------------')
                    pprint(df)
                    macd = df.ta.macd(fast=fast, slow=slow, signal=signal)

                    df = pd.concat([df, macd], axis=1)
                    print('---------- df after cat------------------------------------------------')
                    pprint(df)
                    if (len(df) >= signal):
                        print('----------------------------------------------------------')
                        print(self.exchange.iso8601(self.exchange.milliseconds()), symbol, timeframe)
                        print(df[-signal:])
            except Exception as e:
                print(type(e).__name__, str(e))


async def main():
    coin = ccxt.coinbase(
        {'apiKey': 'organizations/710b94f4-6e8e-46c2-a345-5481fdc4a45a/apiKeys/5d1868d2-dc03-4456-9f88-35ccad267acd',
         'secret': '-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEICgEnZ5eud83hrxQRWBBmB9O9ChWiHOrXWJxrkHdhmG1oAoGCCqGSM49\nAwEHoUQDQgAEm67hHTooKFPMz38PkeIwoNpfVHNzw1Cu2ZQa3KCg5jT3dH/BXNS0\nAANb2A4J/7a5vHgIQpB9T/l+jez9W/RoQw==\n-----END EC PRIVATE KEY-----\n',
        # 'verbose': True,  # for debug output
        })

    coin_exchange = ExchangeBase(coin)
    timeframe = '1m'
    limit = 50
    symbols = [
        'BTC/USDT',
        'ETH/USDT',
    ]
    loops = [coin_exchange.run_ohlcv_loop(symbol, timeframe, limit) for symbol in symbols]
    await gather(*loops)

    await coin.close()

run(main())
