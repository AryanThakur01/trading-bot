import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


@dataclass
class Config:
    binanceEndpoint: str
    binanceWSSEndpoint: str
    timeZoneOffsetms: int
    binanceTimeFrame: str
    supertrendMultiplier: int
    supertrendPeriod: int
    minDataFrameLen: int

    startDate: str
    isBackTesting: bool = False
    backtestingCandleLimit: int = 1000


settings = Config(
    binanceEndpoint=os.getenv("BINANCE_ENDPOINT", "https://api.binance.com/"),
    binanceWSSEndpoint=os.getenv(
        "BINANCE_WSS_ENDPOINT", "wss://stream.binance.com:9443/ws"),
    binanceTimeFrame=os.getenv("BINANCE_TIME_FRAME", "1s"),

    timeZoneOffsetms=eval(
        os.getenv("TIME_ZONE_OFFSET_MS", '0')
    ),
    supertrendMultiplier=eval(
        os.getenv("SUPERTREND_MULTIPLIER", '2')
    ),
    supertrendPeriod=eval(
        os.getenv("SUPERTREND_PERIOD", '20')
    ),
    minDataFrameLen=eval(
        os.getenv("MIN_DATA_FRAME_LEN", '50')
    ),
    isBackTesting=eval(
        os.getenv("IS_BACK_TESTING", 'False')
    ),
    backtestingCandleLimit=eval(
        os.getenv("BACKTESTING_CANDLE_LIMIT", '1000')
    ),
    startDate=os.getenv("START_DATE")
)
