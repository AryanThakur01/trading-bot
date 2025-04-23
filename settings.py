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
    brahmastraSupertrendMultiplier: int
    brahmastraSupertrendPeriod: int
    minDataFrameLen: int


settings = Config(
    binanceEndpoint=os.getenv("BINANCE_ENDPOINT", "https://api.binance.com/"),
    binanceWSSEndpoint=os.getenv(
        "BINANCE_WSS_ENDPOINT", "wss://stream.binance.com:9443/ws"),
    binanceTimeFrame=os.getenv("BINANCE_TIME_FRAME", "1s"),

    timeZoneOffsetms=eval(
        os.getenv("TIME_ZONE_OFFSET_MS", '0')
    ),
    brahmastraVWAPLen=eval(
        os.getenv("BRAHMASTRA_VWAP_LEN", '10')
    ),
    brahmastraSupertrendMultiplier=eval(
        os.getenv("BRAHMASTRA_SUPERTREND_MULTIPLIER", '2')
    ),
    brahmastraSupertrendPeriod=eval(
        os.getenv("BRAHMASTRA_SUPERTREND_PERIOD", '20')
    ),
    minDataFrameLen=eval(
        os.getenv("MIN_DATA_FRAME_LEN", '50')
    )
)
