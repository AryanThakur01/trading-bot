import time as t
from utils.logger import logger
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

    if (settings.isForwardTesting):
        print('Forward testing mode')
        pass
    elif (settings.isBackTesting):
        data = getHistoricalData(symbol='BTCUSDT',
                                 interval=settings.binanceTimeFrame, limit=settings.backtestingCandleLimit)
        for i in range(len(data)):
            d = data[i]
            time = pd.to_datetime(
                d['k']['T']+settings.timeZoneOffsetms, unit="ms")

            logger.debug(
                f"[Backtesting{len(data)}] {i}: {time} - {d['k']['c']} - {d['k']['v']}")

            await brahmastra.processKLineData(json.dumps(d))

            if (i % 288 == 0 and i != 0):
                print(f"{(i / 288)} day(s) over 5 sec wait")
                t.sleep(5)
    else:
        client = BinanceWebSocketClient("btcusdt", settings.binanceTimeFrame)
        await client.connect()
        await client.listen(brahmastra.processKLineData)


if __name__ == "__main__":
    asyncio.run(main())
