import json
from utils.logger import logger
from settings import settings
import pandas as pd
import pandas_ta as ta


class Brahmastra:
    trades = 0
    passes = 0
    dataFrame: pd.DataFrame
    mustHaveColumnsForTrade: list = ["supertrend", "supertrend_dir", "vwap"]

    # This is used to check if supertrend is starting or already started
    hasSupertrendStarted: bool = False

    # Trades
    shortPositions: list = []
    longPositions: list = []
    totalPNL: float = 0.0

    last4Signals = []

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
        last_X_rows = self.dataFrame.tail(settings.minDataFrameLen)
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
        if (len(df) < settings.supertrendPeriod):
            return
        supertrend = ta.supertrend(
            df['high'],
            df['low'],
            df['close'],
            length=settings.supertrendPeriod,
            multiplier=settings.supertrendMultiplier
        )
        if supertrend is None:
            return
        df["supertrend"] = supertrend[f"SUPERT_{settings.supertrendPeriod}_{settings.supertrendMultiplier}.0"]
        df["supertrend_dir"] = supertrend[f"SUPERTd_{settings.supertrendPeriod}_{settings.supertrendMultiplier}.0"]
        if not self.hasSupertrendStarted:
            if df["supertrend_dir"].iloc[-1] == -1:
                logger.info("Supertrend has kicked in.")
                self.hasSupertrendStarted = True

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
        if "vwap" not in self.dataFrame.columns or len(self.dataFrame) < 2:
            return 0
        recentDf = self.dataFrame.tail(2)

        prev_close = recentDf["close"].iloc[0]
        prev_vwap = recentDf["vwap"].iloc[0]
        curr_close = recentDf["close"].iloc[1]
        curr_vwap = recentDf["vwap"].iloc[1]

        if pd.isna(prev_vwap) or pd.isna(curr_vwap):
            return 0

        # Mean reversion: price crosses **above** VWAP → SELL
        if prev_close < prev_vwap and curr_close > curr_vwap:
            return -1

        # Mean reversion: price crosses **below** VWAP → BUY
        elif prev_close > prev_vwap and curr_close < curr_vwap:
            return 1

        return 0

    def _getSupertrendSignal(self):
        previousDf = self.dataFrame.tail(2).head(1)
        recentDf = self.dataFrame.tail(1)
        if (recentDf["supertrend_dir"].values[0] == 1 and previousDf["supertrend_dir"].values[0] == -1):
            return 1
        elif (recentDf["supertrend_dir"].values[0] == -1 and previousDf["supertrend_dir"].values[0] == 1):
            return -1
        else:
            return 0

    def _getMACDSignal(self):
        df = self.dataFrame
        if len(df) < settings.minDataFrameLen:
            return 0
        macd_df = ta.macd(df['close'])
        recent = macd_df.tail(2)
        if macd_df is None or recent.isnull().values.any():
            return 0
        df['macd'] = macd_df['MACD_12_26_9']
        df['macd_signal'] = macd_df['MACDs_12_26_9']
        # Use last two rows to detect crossover
        recent = df[['macd', 'macd_signal']].tail(2)
        if len(recent) < 2:
            return 0
        prev_macd, prev_signal = recent.iloc[0]
        curr_macd, curr_signal = recent.iloc[1]
        if prev_macd < prev_signal and curr_macd > curr_signal:
            return 1  # Bullish crossover
        elif prev_macd > prev_signal and curr_macd < curr_signal:
            return -1  # Bearish crossover
        return 0  # No crossover

    def _waitForMoreData(self):
        if (self.hasSupertrendStarted) and len(self.dataFrame) > settings.minDataFrameLen:
            return 0
        else:
            return 1

    def _getSignalName(self, signal):
        if signal == 1:
            return 'BUY    '
        elif signal == -1:
            return 'SELL   '
        else:
            return 'NEUTRAL'

    def _setLast4Signals(self):
        if len(self.last4Signals) == 4:
            self.last4Signals.pop(0)

        self.last4Signals.append({
            "vwap": self._getVwapSignal(),
            "supertrend": self._getSupertrendSignal(),
            "macd": self._getMACDSignal()
        })

    def _getLast4Signals(self):
        if len(self.last4Signals) < 4:
            return None
        return self.last4Signals

    def _position(self, timestamp, price, signal, isNewPos=False):
        if signal == -1:
            if (len(self.longPositions) > 0):
                self.totalPNL += price - self.longPositions[-1]["price"]
                self.longPositions[-1]["pnl"] = (price -
                                                 self.longPositions[-1]["price"])
                if (self.longPositions[-1]["pnl"] > 0):
                    self.passes += 1
                logger.info(
                    f"Long position closed. Total PNL: {self.totalPNL}")
                self.longPositions.pop()
            elif isNewPos:
                self.trades += 1
                logger.info(f"Created Short position at: {price}")
                self.shortPositions.append({
                    "timestamp": timestamp,
                    "price": price,
                    "pnl": 0.0,
                })
        elif signal == 1:
            if (len(self.shortPositions) > 0):
                self.totalPNL += -(price - self.shortPositions[-1]["price"])
                self.shortPositions[-1]["pnl"] = - \
                    (price - self.shortPositions[-1]["price"])
                if (self.shortPositions[-1]["pnl"] > 0):
                    self.passes += 1
                logger.info(
                    f"Short position closed. Total PNL: {self.totalPNL}")
                self.shortPositions.pop()
            elif isNewPos:
                self.trades += 1
                logger.info(f"Created Long position at: {price}")
                self.longPositions.append({
                    "timestamp": timestamp,
                    "price": price,
                    "pnl": 0.0,
                })

    def _currentPositions(self, price):
        if len(self.longPositions) > 0:
            posPNL = price - self.longPositions[-1]["price"]
            logger.info(
                f"Current Long Position: {self.longPositions[-1]['price']} | position PNL: {posPNL}")
        if len(self.shortPositions) > 0:
            posPNL = -(price - self.shortPositions[-1]["price"])
            logger.info(
                f"Current Short Position: {self.shortPositions[-1]['price']} | position PNL: {posPNL}")

        if self.totalPNL > 0:
            logger.info(f"Total PNL: {self.totalPNL}")
        elif self.totalPNL < 0:
            logger.error(f"Total PNL: {self.totalPNL}")
        else:
            logger.debug(f"Total PNL: {self.totalPNL}")

    def processKLineData(self, message):
        data = json.loads(message)
        if not data["k"]["x"]:
            return
        candle = self._parseCandle(data["k"])
        self._appendToDataFrame(candle)
        if not self._waitForMoreData():
            self._setLast4Signals()
            last4Signals = self._getLast4Signals()

            if last4Signals:
                # # log all 4 signals
                # for signal in last4Signals:
                #     logger.debug(
                #         f"VWAP Signal: {self._getSignalName(signal['vwap'])} | Supertrend Signal: {self._getSignalName(signal['supertrend'])} | MACD Signal: {self._getSignalName(signal['macd'])}"
                #     )
                # logger.info("================================================")

                recentSupertrendSignal = last4Signals[-1]["supertrend"]
                recentMACDSignal = last4Signals[-1]["macd"]
                netSignal = 0
                currentDf = self.dataFrame

                logger.warn(
                    f"=============================== Supertrend says: {recentSupertrendSignal}")
                self._currentPositions(currentDf["close"].iloc[-1])
                if (len(self.shortPositions) > 0 and (recentSupertrendSignal == 1 or recentMACDSignal == 1)):
                    self._position(
                        currentDf.index[-1],
                        currentDf["close"].iloc[-1],
                        recentSupertrendSignal
                    )
                elif (len(self.longPositions) > 0 and (recentSupertrendSignal == -1 or recentMACDSignal == -1)):
                    self._position(
                        currentDf.index[-1],
                        currentDf["close"].iloc[-1],
                        recentSupertrendSignal
                    )
                else:
                    if recentSupertrendSignal != 0:
                        for signal in last4Signals:
                            if signal["macd"] != 0:
                                if signal["macd"] == recentSupertrendSignal:
                                    netSignal = recentSupertrendSignal
                    elif recentMACDSignal != 0:
                        for signal in last4Signals:
                            if signal["supertrend"] != 0:
                                if signal["supertrend"] == recentMACDSignal:
                                    netSignal = recentMACDSignal

                    if netSignal == 1:
                        self._position(
                            self.dataFrame.index[-1],
                            self.dataFrame["close"].iloc[-1],
                            netSignal,
                            isNewPos=True
                        )
                        logger.info(
                            f"BUY Signal: {netSignal}")
                    elif netSignal == -1:
                        self._position(
                            self.dataFrame.index[-1],
                            self.dataFrame["close"].iloc[-1],
                            netSignal,
                            isNewPos=True
                        )
                        logger.error(
                            f"SELL Signal: {netSignal}")
                    else:
                        logger.debug(
                            f"NEUTRAL Signal: {netSignal}")

            print("Successfull Trades: ", self.passes)
            print("Total Trades: ", self.trades)
            if self.trades > 0:
                print("Accuracy: ", (self.passes/self.trades)*100, "%")

            # if (len(self.dataFrame) == settings.minDataFrameLen):
            #     logger.info(
            #         "VWAP Signal || Supertrend Signal || MACD Signal")
            # logger.info(
            #     f"{self._getSignalName(vwapSignal)} \t\t {self._getSignalName(supertrendSignal)} \t\t {self._getSignalName(macdSignal)}"
            # )

            # currentDf = self.dataFrame
            # if (supertrendSignal == -1):
            #     if (len(self.longPositions) > 0):
            #         self.longPositions[-1]["pnl"] = (currentDf["close"].iloc[-1] - self.longPositions[-1]["price"])
            #         self.totalPNL += self.longPositions[-1]["pnl"]
            #         logger.info(
            #             f"Long position closed. Total PNL: {self.totalPNL}")
            #         self.longPositions.pop()
            #
            #     print("Short Position at", currentDf["close"].iloc[-1])
            #     self.shortPositions.append({
            #         "timestamp": currentDf.index[-1],
            #         "price": currentDf["close"].iloc[-1],
            #         "pnl": 0.0,
            #     })
            # elif (supertrendSignal == 1):
            #     if (len(self.shortPositions) > 0):
            #         self.shortPositions[-1]["pnl"] = -(currentDf["close"].iloc[-1] - self.shortPositions[-1]["price"])
            #         self.totalPNL += self.shortPositions[-1]["pnl"]
            #         logger.info(
            #             f"Short position closed. Total PNL: {self.totalPNL}")
            #         self.shortPositions.pop()
            #
            #     logger.info(f"Created Long position at: {currentDf['close'].iloc[-1]}")
            #     self.longPositions.append({
            #         "timestamp": currentDf.index[-1],
            #         "price": currentDf["close"].iloc[-1],
            #         "pnl": 0.0,
            #     })
        else:
            logger.debug(
                f"Current dataframe length: {len(self.dataFrame)} || Waiting for more data.... "
            )
