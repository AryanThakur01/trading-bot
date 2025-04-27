import requests
import time
from utils.logger import logger
from settings import settings


def getCurrentPrice(symbol='BTCUSDT'):
    url = f"{settings.binanceEndpoint}/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return float(data['price'])
    else:
        raise Exception(
            f"Error fetching price: {response.status_code} - {response.text}")


def convertToKlineData(data):
    return {
        'k': {
            't': data[0],  # open_time in ms (timestamp)
            'o': float(data[1]),  # open
            'h': float(data[2]),  # high
            'l': float(data[3]),  # low
            'c': float(data[4]),  # close
            'v': float(data[5]),  # volume
            'T': data[6],  # close_time in ms (timestamp)
            'q': float(data[7]),  # quote_asset_volume
            'n': int(data[8]),  # number_of_trades
            'V': float(data[9]),  # taker_buy_base_asset_volume
            'Q': float(data[10]),  # taker_buy_quote_asset_volume
            'B': data[11],  # ignore
            'x': True  # 'x' can be True for closed candles
        },
    }


def getHistoricalPrice(symbol, interval, limit, startTime=None):
    params = {}
    if startTime:
        params['startTime'] = startTime
    params['symbol'] = symbol
    params['interval'] = interval
    params['limit'] = limit

    paramsString = '&'.join(
        [f"{key}={value}" for key, value in params.items()])
    url = f"{settings.binanceEndpoint}/api/v3/klines?{paramsString}"
    logger.info(f"Fetching historical price data from {url}")
    response = requests.get(url)
    if response.status_code == 200:
        return response
    else:
        raise Exception(
            f"Error fetching historical price: {response.status_code} - {response.text}")


def getHistoricalData(symbol, interval, limit):
    if not settings.startDate:
        response = getHistoricalPrice(symbol, interval, limit)
        data = response.json()
        if len(data) == 0:
            return []
        appending = [convertToKlineData(item) for item in data]
        return appending

    startTime = int(time.mktime(time.strptime(
        settings.startDate, "%Y-%m-%d %H:%M:%S"))*1000)
    returnData = []
    while True:
        response = getHistoricalPrice(symbol, interval, limit)
        if response.status_code == 200:
            data = response.json()
            if len(data) == 0:
                break
            appending = [convertToKlineData(item) for item in data]
            for item in appending:
                returnData.append(item)
            startTime += limit * 5 * 60 * 1000  # Increment startTime by limit * interval
        else:
            raise Exception(
                f"Error fetching historical data: {response.status_code} - {response.text}")
    return returnData
