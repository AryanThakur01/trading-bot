import requests
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
    url = f"{settings.binanceEndpoint}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    print(url)
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        # # BETTER DATA DISPLAY
        #
        # # Convert to a DataFrame
        # columns = [
        #     "open_time", "open", "high", "low", "close", "volume",
        #     "close_time", "quote_asset_volume", "number_of_trades",
        #     "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        # ]
        # df = pd.DataFrame(data, columns=columns)
        # # Convert timestamps to readable dates
        # # First convert to datetime from milliseconds
        # df["open_time"] = pd.to_datetime(
        #     df["open_time"], unit="ms") + pd.Timedelta(hours=5, minutes=30)
        # df["close_time"] = pd.to_datetime(
        #     df["close_time"], unit="ms") + pd.Timedelta(hours=5, minutes=30)
        #
        # # Then, remove timezone info (it will be 'naive' datetime)
        # df["open_time"] = df["open_time"].dt.tz_localize(None)
        # df["close_time"] = df["close_time"].dt.tz_localize(None)
        #
        # # Display it
        # print(df[["open_time", "close_time", "open", "close"]])
        # # ===========
        # # Return data in the format similar to WebSocket return

        return [
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

    else:
        raise Exception(
            f"Error fetching historical data: {response.status_code} - {response.text}")
