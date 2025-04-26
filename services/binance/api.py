import requests
import time
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


def getHistoricalData(symbol, interval, limit):
    startTime = int(time.mktime(time.strptime(
        settings.startDate, "%Y-%m-%d %H:%M:%S"))*1000)
    returnData = []

    while True:
        url = f"{settings.binanceEndpoint}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}&startTime={startTime}"
        print(url)
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(len(data))
            if len(data) == 0:
                break

            appending = [
                {
                    'k': {
                        't': item[0],  # open_time in ms (timestamp)
                        'o': float(item[1]),  # open
                        'h': float(item[2]),  # high
                        'l': float(item[3]),  # low
                        'c': float(item[4]),  # close
                        'v': float(item[5]),  # volume
                        'T': item[6],  # close_time in ms (timestamp)
                        'q': float(item[7]),  # quote_asset_volume
                        'n': int(item[8]),  # number_of_trades
                        'V': float(item[9]),  # taker_buy_base_asset_volume
                        'Q': float(item[10]),  # taker_buy_quote_asset_volume
                        'B': item[11],  # ignore
                        'x': True  # 'x' can be True for closed candles
                    },
                }
                for item in data
            ]
            for item in appending:
                returnData.append(item)
            startTime += limit * 5 * 60 * 1000  # Increment startTime by limit * interval

        else:
            raise Exception(
                f"Error fetching historical data: {response.status_code} - {response.text}")
    return returnData
