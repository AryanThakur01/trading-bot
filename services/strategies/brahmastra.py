import json
from services.indicators import Indicators
from utils.logger import logger
from settings import settings
import pandas as pd
import pandas_ta as ta
from services.strategies.strategy import Strategy
from services.position import Position


class Brahmastra(Strategy, Indicators):
    dataFrame: pd.DataFrame
    hasSupertrendStarted: bool = False
    positionService: Position
    lastSignal: int = 0
    tradedDirection: int = None

    def __init__(self):
        self.dataFrame = pd.DataFrame(
            columns=["timestamp", "open", "high", "low", "close", "volume"])
        self.dataFrame.set_index("timestamp", inplace=True)
        self.dataFrame.sort_index(inplace=True)
        self.positionService = Position()

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

    def hasAllRequiredColumnsAndRows(self, df: pd.DataFrame):
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
        return 1

    def calculateBrahmastraSignal(self, df: pd.DataFrame, originalDf: pd.DataFrame = None):
        if (len(originalDf) < settings.minDataFrameLen or not self.hasAllRequiredColumnsAndRows(df)):
            logger.warning("Not enough data to calculate Brahmastra signal.")
            return 0

        supertrendSignal = self._calculateSupertrendSignal(df)
        macdSignal = self._calculateMACDSignal(df)
        print(
            f"Supertrend Signal: {supertrendSignal}, MACD Signal: {macdSignal}")

        lastSignal = self.lastSignal
        if (macdSignal == supertrendSignal):
            self.lastSignal = supertrendSignal
            if (supertrendSignal != lastSignal):
                return supertrendSignal
        return 0

    def calculateExitSignal(self, df: pd.DataFrame):
        if not self.hasAllRequiredColumnsAndRows(df):
            logger.warning(
                "Not enough data to calculate Brahmastra exit signal.")
            return 0
        if (self.tradedDirection is not None and df.iloc[-1]['supertrend_dir'] != self.tradedDirection):
            print(
                f"Exit signal triggered at {df.iloc[-1]['supertrend_dir']} and {self.tradedDirection}")
            return 1
        return 0

    async def crateOrder(self, signal: int, price: float = None):
        if signal == 1:
            self.tradedDirection = 1
            await self.positionService.order(
                symbol='btcusdt',
                side='BUY',
                stopPrice=self.dataFrame.iloc[-1]['supertrend'] - 200,
                price=price,
            )
        elif signal == -1:
            self.tradedDirection = -1
            await self.positionService.order(
                symbol='btcusdt',
                side='SELL',
                stopPrice=self.dataFrame.iloc[-1]['supertrend'] + 200,
                price=price,
            )

    async def processKLineData(self, message):
        data = json.loads(message)
        if not self.isCandleClosed(data):
            # Check if the KLine is closed ignore if not
            return

        self.positionService.getTotalPNL()
        self.dataFrame = self.appendCandleToDataFrame(
            data['k'], self.dataFrame)

        calculatedSignal = self.calculateBrahmastraSignal(
            self.dataFrame.tail(4), self.dataFrame)

        if (self.calculateExitSignal(self.dataFrame) == 1):
            await self.positionService.closePosition(
                symbol='btcusdt', price=self.dataFrame.iloc[-1]['close'])
        if (calculatedSignal != 0):
            await self.crateOrder(calculatedSignal, self.dataFrame.iloc[-1]['close'])

        self.positionService.exportTradesToCSV()
