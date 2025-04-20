import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


@dataclass
class Config:
    binanceEndpoint: str
    binanceWSSEndpoint: str
    timeZoneOffsetms: int


settings = Config(
    binanceEndpoint=os.getenv("BINANCE_ENDPOINT"),
    binanceWSSEndpoint=os.getenv("BINANCE_WSS_ENDPOINT"),
    timeZoneOffsetms=eval(os.getenv("TIME_ZONE_OFFSET_MS", 0) or 0),
)
