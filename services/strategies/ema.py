import json
import time as t
import pandas_ta as ta
import pandas as pd
from services.indicators import Indicators
from utils.logger import logger
from settings import settings
from services.strategies.strategy import Strategy
from services.position import Position


class EmaCross(Strategy, Indicators):
    wait: bool = 0
    dataFrame: pd.DataFrame
    positionService: Position
    lastSignal: int = 0
    tradedDirection: int = None

    def __init__(self):
        self.dataFrame = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume"]
        )
        self.dataFrame.set_index("timestamp", inplace=True)
        self.dataFrame.sort_index(inplace=True)
        self.positionService = Position()

    def _parseCandle(self, kline):
        preferredTime = kline["T"] + settings.timeZoneOffsetms
        return {
            "timestamp": pd.to_datetime(preferredTime, unit="ms"),
            "open": float(kline["o"]),
            "high": float(kline["h"]),
            "low": float(kline["l"]),
            "close": float(kline["c"]),
            "volume": float(kline["v"]),
        }

    def _appendEMAs(self, df: pd.DataFrame):
        df["ema_9"] = df["close"].ewm(span=50, adjust=False).mean()
        df["ema_21"] = df["close"].ewm(span=200, adjust=False).mean()
        return df

    def appendCandleToDataFrame(self, raw, dataFrame: pd.DataFrame):
        candle = self._parseCandle(raw)
        newRow = pd.DataFrame([candle])
        newRow.set_index("timestamp", inplace=True)

        if dataFrame.empty:
            dataFrame = newRow
        else:
            dataFrame = pd.concat([dataFrame, newRow])

        if len(dataFrame) >= settings.minDataFrameLen:
            dataFrame = self._appendEMAs(dataFrame)

        return dataFrame

    def isCandleClosed(self, kline):
        return kline['k']['x']

    def _calculateEmaSignal(self, df: pd.DataFrame):
        if len(df) < 3 or "ema_9" not in df.columns or "ema_21" not in df.columns:
            logger.warning("Not enough data or missing EMAs.")
            return 0

        ema_9 = df["ema_9"].tolist()
        ema_21 = df["ema_21"].tolist()

        if ema_9[-2] < ema_21[-2] and ema_9[-1] > ema_21[-1]:
            return 1  # Bullish crossover
        elif ema_9[-2] > ema_21[-2] and ema_9[-1] < ema_21[-1]:
            return -1  # Bearish crossover
        return 0

    def calculateExitSignal(self, df: pd.DataFrame):
        if len(df) < 3 or "ema_9" not in df.columns or "ema_21" not in df.columns:
            return 0
        if self.tradedDirection == 1 and df["ema_9"].iloc[-1] < df["ema_21"].iloc[-1]:
            return 1
        if self.tradedDirection == -1 and df["ema_9"].iloc[-1] > df["ema_21"].iloc[-1]:
            return 1
        return 0

    async def createOrder(self, signal: int, df: pd.DataFrame):
        price = df.iloc[-1]["close"]
        timestamp = df.iloc[-1].name
        if signal == 1:
            self.tradedDirection = 1
            await self.positionService.order(
                timestamp=timestamp,
                symbol="btcusdt",
                side="BUY",
                stopPrice=price * 0.98,
                price=price,
            )
        elif signal == -1:
            self.tradedDirection = -1
            await self.positionService.order(
                timestamp=timestamp,
                symbol="btcusdt",
                side="SELL",
                stopPrice=price * 1.02,
                price=price,
            )

    async def processKLineData(self, message):
        data = json.loads(message)
        if not self.isCandleClosed(data):
            return

        self.positionService.getTotalPNL()
        self.dataFrame = self.appendCandleToDataFrame(
            data["k"], self.dataFrame)

        await self.positionService.trigger(
            data["k"]["h"], data["k"]["l"], data["k"]["c"])

        if "ema_9" in self.dataFrame.columns:
            print(self.dataFrame.iloc[-1]["ema_9"])
            await self.positionService.trailSL(self.dataFrame.iloc[-1]["ema_21"])

        # if (exited > 1):
        #     self.wait = 10
        #     return
        #
        # if (self.wait > 0):
        #     logger.info('COOLDOWN.....')
        #     self.wait = self.wait - 1
        #     return

        calculatedSignal = self._calculateEmaSignal(self.dataFrame.tail(3))
        if self.calculateExitSignal(self.dataFrame):
            # closed =
            await self.positionService.closePosition(
                symbol="btcusdt", price=self.dataFrame.iloc[-1]["close"]
            )
            # if (closed == 1):
            #     self.wait = 10

        if calculatedSignal != 0:
            await self.createOrder(calculatedSignal, self.dataFrame)
