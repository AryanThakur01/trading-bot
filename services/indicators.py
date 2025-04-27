import pandas as pd
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
