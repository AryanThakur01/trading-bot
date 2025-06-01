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

    def _appendIndicators(self, df: pd.DataFrame):
        df["ema_small"] = df["close"].ewm(span=50, adjust=False).mean()
        df["ema_large"] = df["close"].ewm(span=200, adjust=False).mean()
        df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=14)
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
            dataFrame = self._appendIndicators(dataFrame)

        return dataFrame

    def isCandleClosed(self, kline):
        return kline['k']['x']

    def _calculateEmaSignal(self, df: pd.DataFrame):
        if len(df) < 3 or "ema_small" not in df.columns or "ema_large" not in df.columns:
            logger.warning("Not enough data or missing EMAs.")
            return 0

        ema_small = df["ema_small"].tolist()
        ema_large = df["ema_large"].tolist()

        if ema_small[-2] < ema_large[-2] and ema_small[-1] > ema_large[-1]:
            return 1  # Bullish crossover
        elif ema_small[-2] > ema_large[-2] and ema_small[-1] < ema_large[-1]:
            return -1  # Bearish crossover
        return 0

    def calculateExitSignal(self, df: pd.DataFrame):
        if len(df) < 3 or "ema_small" not in df.columns or "ema_large" not in df.columns:
            return 0
        if self.tradedDirection == 1 and df["ema_small"].iloc[-1] < df["ema_large"].iloc[-1]:
            return 1
        if self.tradedDirection == -1 and df["ema_small"].iloc[-1] > df["ema_large"].iloc[-1]:
            return 1
        return 0

    async def createOrder(self, signal: int, df: pd.DataFrame):
        atr = df.iloc[-1]["atr"] if "atr" in df.columns else 0.0
        price = df.iloc[-1]["close"]
        timestamp = df.iloc[-1].name
        self.tradedDirection = signal
        await self.positionService.open_position(
            symbol=settings.symbol,
            side="BUY" if signal == 1 else "SELL",
            price=price,
            atr=atr,
            entry_time=timestamp,
        )

    async def processKLineData(self, message):
        data = json.loads(message)
        if not self.isCandleClosed(data):
            return

        self.dataFrame = self.appendCandleToDataFrame(
            data["k"], self.dataFrame)
        await self.positionService.position_ticker(
            open=self.dataFrame.iloc[-1]["open"],
            high=self.dataFrame.iloc[-1]["high"],
            low=self.dataFrame.iloc[-1]["low"],
            close=self.dataFrame.iloc[-1]["close"]
        )

        calculatedSignal = self._calculateEmaSignal(self.dataFrame.tail(3))
        if self.calculateExitSignal(self.dataFrame):
            await self.positionService.close_position(
                exit_price=self.dataFrame.iloc[-1]["close"]
            )
            pass

        if calculatedSignal != 0:
            await self.createOrder(calculatedSignal, self.dataFrame)

        self.positionService.export_to_csv(settings.symbol+'_trades.csv')

        await self.positionService.get_total_pnl()
