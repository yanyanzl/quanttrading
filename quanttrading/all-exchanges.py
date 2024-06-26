# -*- coding: utf-8 -*-

from asyncio import gather, run, sleep
import pandas_ta as ta
import pandas as pd
from abc import ABC

import os
import sys
from pprint import pprint
# from datetime import datetime
# import time
from utility import encrypt, decrypt

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

    cipher_api = "VOTON+K0WmP4YrAGc7LJeS6HoXud88OY5N1/RUSvK6cvfazIdbHjhHyaElGFziY+PYIjuuQhxJydUf3N/hwmkJTHytsr7DRMOlFhFMWx76h5LY2XTjoJEPkAjcC1httZbslqhhsOqIuglBmlZOFBMg=="
    apikey = decrypt(b"080802", cipher_api).decode()

    cipher_secret = "GXFcQQ3U8vwUS6zqlomc7i2O6Aq5od3NpoDP2v42CccmnUiEKoKFlM7Yw45mI/zvM+puXXmylkPImL/51lxCxrVAnCwQpZGArX1fJllvDlSAQuotPxuDSL5OMQl14OFGlUcSJgprzaogei3AnXfns/uy+TqEW3bnlhyJQez5JJ6K9VGrXZUIX6dADwm2DL4w2vsnSkLafaX/i7dpLoxvKcGpEV75p1CJYElKJ4Ir1Iq/JumUMDLJ7Sgf9mP5Ece5qKymD81Xxewm7lqTW1KvnWnf6AA0FRIcYExRBKkFq9yPiFG+IY0S09i4KuBCErhee5xeqn3ooDY2x08w3AiyNg=="
    secret = decrypt(b"080802", cipher_secret).decode()
  
    print(f"apikey is {apikey}")
    print(f"secret is {secret}")

    coin = ccxt.coinbase(
        {'apiKey': apikey,
         'secret': secret,
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
