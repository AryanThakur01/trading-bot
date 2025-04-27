import json
from services.indicators import Indicators
from utils.logger import logger
from settings import settings
import pandas as pd
import pandas_ta as ta
from services.strategies.strategy import Strategy


class Brahmastra(Strategy, Indicators):
    dataFrame: pd.DataFrame

    def __init__(self):
        self.dataFrame = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume"])
        self.dataFrame.set_index("timestamp", inplace=True)
        self.dataFrame.sort_index(inplace=True)

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

    def appendCandleToDataFrame(self, raw):
        candle = self._parseCandle(raw)
        newRow = pd.DataFrame([candle])
        newRow.set_index("timestamp", inplace=True)
        if self.dataFrame.empty:
            self.dataFrame = newRow
        else:
            self.dataFrame = pd.concat([self.dataFrame, newRow])

        if (len(self.dataFrame) >= settings.minDataFrameLen):
            last_X_rows = self.dataFrame.tail(
                settings.minDataFrameLen) if settings.minDataFrameLen > 0 else self.dataFrame
            vwap = super().calculateVWAP(last_X_rows)
            print(last_X_rows.index, vwap)
            self.dataFrame.loc[last_X_rows.index, "vwap"] = vwap
            print(self.dataFrame)
            logger.info("==========================")

    def isCandleClosed(self, kline):
        kline_data = kline['k']
        return kline_data['x']

    def processKLineData(self, message):
        data = json.loads(message)
        if not self.isCandleClosed(data):
            # Check if the KLine is closed ignore if not
            return

        self.appendCandleToDataFrame(data['k'])

        # kline = self.parseCandle(data['k'])
