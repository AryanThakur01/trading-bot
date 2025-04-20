import json
from settings import settings
import pandas as pd
import pandas_ta as ta


class Brahmastra:
    dataFrame: pd.DataFrame
    lastVWAPSignal: int = 0

    def __init__(self):
        self.dataFrame = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume"])

    def _displayCandle(self, candle):
        if (len(self.dataFrame) == 1):
            print("Timestamp\t\t\tOpen\t\tHigh\t\tLow\t\tClose\t\tVolume")
        print(f"{candle['timestamp']}\t{candle['open']}\t{candle['high']}\t"
              f"{candle['low']}\t{candle['close']}\t{candle['volume']}")

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

    def _appendVWAPToDataFrame(self):
        last_10_rows = self.dataFrame.tail(10)
        vwap_series = ta.vwap(
            last_10_rows["high"],
            last_10_rows["low"],
            last_10_rows["close"],
            last_10_rows["volume"]
        )
        self.dataFrame.loc[last_10_rows.index, "vwap"] = vwap_series

    def _appendToDataFrame(self, candle):
        newRow = pd.DataFrame([candle])
        newRow.set_index("timestamp", inplace=True)
        if self.dataFrame.empty:
            self.dataFrame = newRow
        else:
            self.dataFrame = pd.concat([self.dataFrame, newRow])

        self._appendVWAPToDataFrame()

    def _getDataFrame(self):
        return self.dataFrame.copy()

    def _VWAPSignal(self):
        signal = None
        if (len(self.dataFrame) == 0):
            return 0

        recentDf = self.dataFrame.tail(1)
        if (recentDf["close"].values[0] > recentDf["vwap"].values[0]):
            signal = 1
        elif (recentDf["close"].values[0] < recentDf["vwap"].values[0]):
            signal = -1
        else:
            signal = 0

        if (self.lastVWAPSignal != signal):
            self.lastVWAPSignal = signal
            return signal
        else:
            return 0

    def processKLineData(self, message):
        data = json.loads(message)
        if not data["k"]["x"]:
            return
        candle = self._parseCandle(data["k"])
        self._appendToDataFrame(candle)
        print(self._VWAPSignal())
