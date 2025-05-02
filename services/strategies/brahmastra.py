import json
from services.indicators import Indicators
from utils.logger import logger
from settings import settings
import pandas as pd
import pandas_ta as ta
from services.strategies.strategy import Strategy


class Brahmastra(Strategy, Indicators):
    dataFrame: pd.DataFrame
    hasSupertrendStarted: bool = False

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

    def _appendSupertrend(self, df):
        supertrend = super().calculateSupertrend(df)
        if supertrend is not None:
            self.dataFrame["supertrend"] = supertrend["supertrend"]
            self.dataFrame["supertrend_dir"] = supertrend["supertrend_dir"]
            if not self.hasSupertrendStarted:
                if self.dataFrame["supertrend_dir"].iloc[-1] == -1:
                    logger.info("Supertrend has kicked in.")
                    self.hasSupertrendStarted = True
        return df

    def _appendMACD(self, df):
        macd_df = super()._getMACD(df)
        if macd_df is None:
            return None
        df['macd'] = macd_df['MACD_12_26_9']
        df['macd_signal'] = macd_df['MACDs_12_26_9']
        return df

    def _getLast4Signals(self, df):
        if len(df) < 4:
            return

    def appendCandleToDataFrame(self, raw):
        candle = self._parseCandle(raw)
        newRow = pd.DataFrame([candle])
        newRow.set_index("timestamp", inplace=True)
        if self.dataFrame.empty:
            self.dataFrame = newRow
        else:
            self.dataFrame = pd.concat([self.dataFrame, newRow])

        if (len(self.dataFrame) >= settings.minDataFrameLen):
            # Calculate and add vwap to dataframe
            last_X_rows = self.dataFrame.tail(
                settings.minDataFrameLen
            ) if settings.minDataFrameLen > 0 else self.dataFrame
            vwap = super().calculateVWAP(last_X_rows)
            self.dataFrame.loc[last_X_rows.index, "vwap"] = vwap

            # Calculate and add supertrend to dataframe
            self.dataFrame = self._appendSupertrend(self.dataFrame)

            # Calculate and add macd to dataframe
            newDf = self._appendMACD(self.dataFrame)
            if newDf is not None:
                self.dataFrame = newDf

    def isCandleClosed(self, kline):
        kline_data = kline['k']
        return kline_data['x']

    def processKLineData(self, message):
        data = json.loads(message)
        if not self.isCandleClosed(data):
            # Check if the KLine is closed ignore if not
            return

        self.appendCandleToDataFrame(data['k'])
