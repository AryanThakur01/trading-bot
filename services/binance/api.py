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
