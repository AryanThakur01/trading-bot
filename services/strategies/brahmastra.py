import json
from settings import settings
import pandas as pd
import pandas_ta as ta


class Brahmastra:
    dataFrame: pd.DataFrame

    # This is used to check if supertrend is starting or already started
    isSupertrendStarting: bool = True

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
        last_X_rows = self.dataFrame.tail(settings.brahmastraVWAPLen)
        vwap_series = ta.vwap(
            last_X_rows["high"],
            last_X_rows["low"],
            last_X_rows["close"],
            last_X_rows["volume"]
        )
        self.dataFrame.loc[last_X_rows.index, "vwap"] = vwap_series

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
                print("Supertrend has kicked in.")
                self.isSupertrendStarting = False

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

    def _VWAPSignal(self):
        recentDf = self.dataFrame.tail(1)
        if (recentDf["close"].values[0] > recentDf["vwap"].values[0]):
            return 1
        elif (recentDf["close"].values[0] < recentDf["vwap"].values[0]):
            return -1

    def _displayDataFrameFilteredColumns(self, columns):
        # Displaying supertrend and supertrend directions only and if none then displaying waiting for more data and current dataframe length
        if "supertrend" in self.dataFrame.columns and "supertrend_dir" in self.dataFrame.columns:
            print(self.dataFrame[columns])
        else:
            print("Waiting for more data. Current dataframe length: ",
                  len(self.dataFrame))

    def processKLineData(self, message):
        data = json.loads(message)
        if not data["k"]["x"]:
            return
        candle = self._parseCandle(data["k"])
        self._appendToDataFrame(candle)
        self._displayDataFrameFilteredColumns(["supertrend", "supertrend_dir"])
