import time
from binance.api import getCurrentPrice


def main():
    while True:
        price = getCurrentPrice()
        print(f"[BTC/USDT] Current price: {price}")
        time.sleep(5)


if __name__ == "__main__":
    main()
