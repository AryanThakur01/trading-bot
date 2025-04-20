import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


@dataclass
class Config:
    binanceEndpoint: str


settings = Config(
    binanceEndpoint=os.getenv("BINANCE_ENDPOINT"),
)
