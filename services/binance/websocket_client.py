# binance/websocket_client.py
from utils.logger import logger
import websockets
from settings import settings


class BinanceWebSocketClient:
    def __init__(self, symbol="btcusdt", timeframe="1s"):
        self.symbol = symbol
        self.url = f"{settings.binanceWSSEndpoint}/{symbol}@kline_{timeframe}"
        self.ws = None

    async def connect(self):
        logger.info(f"Connecting to {self.url}")
        self.ws = await websockets.connect(self.url)
        logger.info("Connected.")

    async def listen(self, onMessage: callable):
        while True:
            message = await self.ws.recv()
            onMessage(message)

    # Destructor
    def __del__(self):
        logger.critical("Stopped binance websocket")
        if self.ws:
            self.ws.close()
