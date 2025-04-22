import json
from utils.logger import logger
from settings import settings
import pandas as pd
import pandas_ta as ta


class Brahmastra:
    dataFrame: pd.DataFrame
    mustHaveColumnsForTrade: list = ["supertrend", "supertrend_dir", "vwap"]

    # This is used to check if supertrend is starting or already started
    isSupertrendStarting: bool = True

    # Trades
    shortPositions: list = []
    longPositions: list = []
    totalPNL: float = 0.0

    def __init__(self):
        self.dataFrame = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume"])

    def _parseCandle(self, kline):
        preferretTime = kline["T"]+(settings.timeZoneOffsetms)
        return {
            "timestamp": pd.to_datetime(preferretTime, unit="ms"),
            "open": float(kline["o"]),
            "high": float(kline["h"]),
            "low": float(kline["l"]),
            "close": float(kline["c"]),
            "volume": float(kline["v"]),
        }

    # This function is to append VWAP to the dataframe
    def _appendVWAPToDataFrame(self):
        last_X_rows = self.dataFrame.tail(settings.brahmastraVWAPLen)
        vwap_series = ta.vwap(
            last_X_rows["high"],
            last_X_rows["low"],
            last_X_rows["close"],
            last_X_rows["volume"]
        )
        self.dataFrame.loc[last_X_rows.index, "vwap"] = vwap_series

    # This function is to append supertrend to the dataframe
    def _appendSupertrendSignalToDataFrame(self):
        df = self.dataFrame
        if (len(df) < settings.brahmastraSupertrendPeriod):
            return
        supertrend = ta.supertrend(
            df['high'],
            df['low'],
            df['close'],
            length=settings.brahmastraSupertrendPeriod,
            multiplier=settings.brahmastraSupertrendMultiplier
        )
        if supertrend is None:
            return
        df["supertrend"] = supertrend[f"SUPERT_{settings.brahmastraSupertrendPeriod}_{settings.brahmastraSupertrendMultiplier}.0"]
        df["supertrend_dir"] = supertrend[f"SUPERTd_{settings.brahmastraSupertrendPeriod}_{settings.brahmastraSupertrendMultiplier}.0"]
        if self.isSupertrendStarting:
            if df["supertrend_dir"].iloc[-1] == -1:
                logger.info("Supertrend has kicked in.")
                self.isSupertrendStarting = False

    # This function is to append all data and columns to the dataframe
    def _appendToDataFrame(self, candle):
        newRow = pd.DataFrame([candle])
        newRow.set_index("timestamp", inplace=True)
        if self.dataFrame.empty:
            self.dataFrame = newRow
        else:
            self.dataFrame = pd.concat([self.dataFrame, newRow])

        self._appendVWAPToDataFrame()
        self._appendSupertrendSignalToDataFrame()

    def _getDataFrame(self):
        return self.dataFrame.copy()

    def _getVwapSignal(self):
        recentDf = self.dataFrame.tail(1)
        if (recentDf["close"].values[0] > recentDf["vwap"].values[0]):
            return 1
        elif (recentDf["close"].values[0] < recentDf["vwap"].values[0]):
            return -1

    def _getSupertrendSignal(self):
        previousDf = self.dataFrame.tail(2).head(1)
        recentDf = self.dataFrame.tail(1)
        if (recentDf["supertrend_dir"].values[0] == 1 and previousDf["supertrend_dir"].values[0] == -1):
            return 1
        elif (recentDf["supertrend_dir"].values[0] == -1 and previousDf["supertrend_dir"].values[0] == 1):
            return -1
        else:
            return 0

    def _waitForMoreData(self):
        if self.isSupertrendStarting:
            return 1
        else:
            return 0

    def processKLineData(self, message):
        data = json.loads(message)
        if not data["k"]["x"]:
            return
        candle = self._parseCandle(data["k"])
        self._appendToDataFrame(candle)
        if not self._waitForMoreData():
            # vwapSignal = self._getVwapSignal()
            supertrendSignal = self._getSupertrendSignal()
            currentDf = self.dataFrame

            if (supertrendSignal == -1):
                print("Short Position at", currentDf["close"].iloc[-1])
                self.shortPositions.append({
                    "timestamp": currentDf.index[-1],
                    "price": currentDf["close"].iloc[-1],
                    "pnl": 0.0,
                })
                pass
            elif (supertrendSignal == 1):
                if (len(self.shortPositions) > 0):
                    self.shortPositions[-1]["pnl"] = -(currentDf["close"].iloc[-1] - self.shortPositions[-1]["price"])
                    self.totalPNL += self.shortPositions[-1]["pnl"]
                    logger.info(
                        f"Short position closed. Total PNL: {self.totalPNL}")
                    self.shortPositions.pop()
                pass
        else:
            logger.debug(
                f"Please wait your system is starting.... Current dataframe length: {len(self.dataFrame)}")
