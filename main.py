# import time
import pandas as pd
import json
from services.binance.api import getHistoricalData
import asyncio
# from binance.api import getCurrentPrice
from services.binance.websocket_client import BinanceWebSocketClient
from services.strategies.brahmastra import Brahmastra
from settings import settings


async def main():
    # while True:
    #     price = getCurrentPrice()
    #     print(f"[BTC/USDT] Current price: {price}")
    #     time.sleep(5)

    # BRAHMASTRA STRATEGY
    brahmastra = Brahmastra()
    if (settings.isBackTesting):
        data = getHistoricalData(symbol='BTCUSDT',
                                 interval=settings.binanceTimeFrame, limit=settings.backtestingCandleLimit)
        for i in range(len(data)):
            d = data[i]
            brahmastra.processKLineData(json.dumps(d))
            time = pd.to_datetime(
                d['k']['T']+settings.timeZoneOffsetms, unit="ms")
            print(
                f"[Backtesting] {i}: {time} - {d['k']['c']} - {d['k']['v']}")
    else:
        client = BinanceWebSocketClient("btcusdt", settings.binanceTimeFrame)
        await client.connect()
        await client.listen(brahmastra.processKLineData)


if __name__ == "__main__":
    asyncio.run(main())
