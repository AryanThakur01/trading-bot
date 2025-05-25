from abc import ABC, abstractmethod


class Strategy(ABC):
    @abstractmethod
    def isCandleClosed(self, kline):
        """
        Check if the KLine is a closing candle.
        :param kline: The KLine data.
        :return: True if it is a closing candle, False otherwise.
        """
        pass

    @abstractmethod
    def processKLineData(self, message):
        """
        Process KLine data.
        :param message: The message containing KLine data.
        """
        pass
