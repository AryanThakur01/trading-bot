# import time
import asyncio
# from binance.api import getCurrentPrice
from services.binance.websocket_client import BinanceWebSocketClient
from services.strategies.brahmastra import Brahmastra


async def main():
    # while True:
    #     price = getCurrentPrice()
    #     print(f"[BTC/USDT] Current price: {price}")
    #     time.sleep(5)
    client = BinanceWebSocketClient("btcusdt")
    brahmastra = Brahmastra()
    await client.connect()
    await client.listen(brahmastra.processKLineData)


if __name__ == "__main__":
    asyncio.run(main())
