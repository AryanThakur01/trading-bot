import pandas as pd
import numpy as np
from settings import settings
import pandas_ta as ta


class Indicators:
    def __init__(self, data):
        self.data = data

    def calculateVWAP(self, last_X_rows: pd.DataFrame):
        """
        Calculate the Volume Weighted Average Price (VWAP) for the given data.
        """
        vwap_series = ta.vwap(
            last_X_rows["high"],
            last_X_rows["low"],
            last_X_rows["close"],
            last_X_rows["volume"]
        )
        return vwap_series

    def calculateSupertrend(self, df: pd.DataFrame):
        if (len(df) < settings.supertrendPeriod):
            return

        supertrend = ta.supertrend(
            df['high'],
            df['low'],
            df['close'],
            length=settings.supertrendPeriod,
            multiplier=settings.supertrendMultiplier
        )
        supertrend["supertrend"] = supertrend[
            f"SUPERT_{settings.supertrendPeriod}_{settings.supertrendMultiplier}.0"]
        supertrend["supertrend_dir"] = supertrend[
            f"SUPERTd_{settings.supertrendPeriod}_{settings.supertrendMultiplier}.0"]
        return supertrend

    def _getMACD(self, df: pd.DataFrame):
        return ta.macd(df['close'])
