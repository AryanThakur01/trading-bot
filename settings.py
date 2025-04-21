import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


@dataclass
class Config:
    binanceEndpoint: str
    binanceWSSEndpoint: str
    timeZoneOffsetms: int
    brahmastraVWAPLen: int
    binanceTimeFrame: str
    brahmastraSupertrendMultiplier: int = 3
    brahmastraSupertrendPeriod: int = 7


settings = Config(
    binanceEndpoint=os.getenv("BINANCE_ENDPOINT"),
    binanceWSSEndpoint=os.getenv("BINANCE_WSS_ENDPOINT"),
    timeZoneOffsetms=eval(os.getenv("TIME_ZONE_OFFSET_MS", 0)),
    brahmastraVWAPLen=eval(os.getenv("BRAHMASTRA_VWAP_LEN", 10)),
    binanceTimeFrame=os.getenv("BINANCE_TIME_FRAME", "1s"),
    brahmastraSupertrendMultiplier=eval(
        os.getenv("BRAHMASTRA_SUPERTREND_MULTIPLIER", 2)),
    brahmastraSupertrendPeriod=eval(
        os.getenv("BRAHMASTRA_SUPERTREND_PERIOD", 20)),
)
