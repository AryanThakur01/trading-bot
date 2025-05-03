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
    lastSignal: int = 0

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
            df["supertrend"] = supertrend["supertrend"]
            df["supertrend_dir"] = supertrend["supertrend_dir"]
            if not self.hasSupertrendStarted:
                if df["supertrend_dir"].iloc[-1] == -1:
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

    def appendCandleToDataFrame(self, raw, dataFrame: pd.DataFrame):
        candle = self._parseCandle(raw)
        newRow = pd.DataFrame([candle])
        newRow.set_index("timestamp", inplace=True)
        if dataFrame.empty:
            dataFrame = newRow
        else:
            dataFrame = pd.concat([dataFrame, newRow])

        if (len(dataFrame) >= settings.minDataFrameLen):
            # Calculate and add vwap to dataframe
            last_X_rows = dataFrame.tail(
                settings.minDataFrameLen
            ) if settings.minDataFrameLen > 0 else dataFrame
            vwap = super().calculateVWAP(last_X_rows)
            dataFrame.loc[last_X_rows.index, "vwap"] = vwap

            # Calculate and add supertrend to dataframe
            dataFrame = self._appendSupertrend(dataFrame)

            # Calculate and add macd to dataframe
            newDf = self._appendMACD(dataFrame)
            if newDf is not None:
                dataFrame = newDf
        return dataFrame

    def isCandleClosed(self, kline):
        kline_data = kline['k']
        return kline_data['x']

    def _calculateMACDSignal(self, df: pd.DataFrame):
        if df is None or len(df) < 4:
            return False
        macdList = df["macd"].tolist()
        macdSignalList = df["macd_signal"].tolist()

        for i in range(1, len(df)):
            if macdList[-i] > macdSignalList[-i] and macdList[-(i-1)] < macdSignalList[-(i-1)]:
                return 1
            elif macdList[-i] < macdSignalList[-i] and macdList[-(i-1)] > macdSignalList[-(i-1)]:
                return -1

        return 0

    def _calculateSupertrendSignal(self, df: pd.DataFrame):
        # Supertrend Signal calculation
        supertrendDirs = df["supertrend_dir"].tolist()
        supertrendSignal = supertrendDirs[-1]

        for i in range(len(supertrendDirs)):
            if supertrendDirs[i] != supertrendSignal:
                return supertrendSignal
        return 0

    def calculateBrahmastraSignal(self, df: pd.DataFrame, originalDf: pd.DataFrame = None):
        if (len(originalDf) < settings.minDataFrameLen):
            logger.warning("Not enough data to calculate Brahmastra signal.")
            return 0
        required_columns = ["vwap", "supertrend_dir", "macd", "macd_signal"]

        # Check if we have at least 4 rows
        if len(df) < 4:
            logger.warning("Not enough data to calculate Brahmastra signal.")
            return 0

        # Check if all required columns exist
        for col in required_columns:
            if col not in df.columns:
                logger.warning(f"Missing required column: {col}")
                return 0

        supertrendSignal = self._calculateSupertrendSignal(df)
        macdSignal = self._calculateMACDSignal(df)

        if (supertrendSignal == macdSignal):
            signal = supertrendSignal
            if (self.lastSignal == signal):
                print("Do nothing")
                return 0
            self.lastSignal = signal

            if signal == 1:
                logger.info(
                    f"Buy Signal at {df.iloc[-1]['close']}, Stoploss: {df.iloc[-1]['supertrend'] - 100}")
                return 1
            elif signal == -1:
                logger.critical(
                    f"Sell Signal at {df.iloc[-1]['close']}, Stoploss: {df.iloc[-1]['supertrend'] + 100}")
                return -1
            else:
                print("Do nothing")
                return 0

        return 0

    def processKLineData(self, message):
        data = json.loads(message)
        if not self.isCandleClosed(data):
            # Check if the KLine is closed ignore if not
            return

        self.dataFrame = self.appendCandleToDataFrame(
            data['k'], self.dataFrame)

        calculatedSignal = self.calculateBrahmastraSignal(
            self.dataFrame.tail(4), self.dataFrame)
