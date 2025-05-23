from utils.logger import logger
from datetime import datetime
import csv
import os
import requests
from settings import settings


class Position:
    activePosition = None
    orderList = []

    def __init__(self):
        logger.info('Position initialized')

    def getTotalPNL(self):
        if (len(self.orderList) == 0):
            return 0

        # Calculate and log total PNL
        totalPnl = sum(
            order['pnl'] for order in self.orderList if 'pnl' in order)

        if totalPnl > 0:
            logger.info(
                f"Total PNL: {totalPnl} - {len(self.orderList)} orders")
        elif totalPnl < 0:
            logger.critical(
                f"Total PNL: {totalPnl} - {len(self.orderList)} orders")
        else:
            print("No PNL")
        return totalPnl

    async def order(self, timestamp: str, symbol: str, side: str, stopPrice: float, price: float):
        orderType = 'STOP_MARKET'

        if settings.isForwardTesting:
            logger.info(
                f'Forward testing mode, not sending order to Binance: {timestamp} {symbol}, {side}, {orderType}, {stopPrice}')
            # url = f"{settings.binanceTestingEndpoint}/fapi/v1/order"
            # data = {
            #     'symbol': symbol,
            #     'side': side,
            #     'type': orderType,
            #     'stopPrice': stopPrice,
            #     'closePosition': True,
            # }
            # await requests.post(url, data=data)
            pass

        elif settings.isBackTesting:
            logger.debug(
                f'Back testing mode, not sending order to Binance: {timestamp} {symbol}, {side}, {orderType}, {stopPrice}')

            target = price
            if (side == "BUY"):
                target = price + (price - stopPrice)*2
            else:
                target = price - (stopPrice - price)*2

            # Create a new order
            self.activePosition = {
                'timestamp': timestamp,
                'symbol': symbol,
                'side': side,
                'orderType': orderType,
                'stopPrice': stopPrice,
                'orderPrice': price,
                'targetPrice': target
            }
            logger.info(
                f"Created order: Symbol: {symbol}, Side: {side}, OrderType: {orderType}, StopPrice: {stopPrice}, Price: {price}")

        else:
            logger.debug(
                f'TODO: Implement New order creation in production: {symbol}, {side}, {orderType}, {stopPrice}')

    async def trailSL(self, emaSmaller):
        if self.activePosition is None:
            return 0
        else:
            self.activePosition["stopPrice"] = emaSmaller
        return 1

    async def trigger(self, high, low, close):
        if self.activePosition is None:
            return 0

        position = self.activePosition
        side = position['side']
        stop = position['stopPrice']
        target = position['targetPrice']

        if side == 'BUY':
            if low <= stop:
                logger.warning("BUY stop loss hit")
                await self.closePosition(position['symbol'], stop)
                return 1
            # elif high >= target:
            #     logger.info("BUY target hit")
            #     await self.closePosition(position['symbol'], target)
            #     return 1

        elif side == 'SELL':
            if high >= stop:
                logger.warning("SELL stop loss hit")
                await self.closePosition(position['symbol'], stop)
                return 1
            # elif low <= target:
            #     logger.info("SELL target hit")
            #     await self.closePosition(position['symbol'], target)
            #     return 1
        return 0

    async def closePosition(self, symbol: str, price: float):
        if self.activePosition is not None:
            activePosition = self.activePosition
            if activePosition['side'] == 'BUY':
                exitPrice = max(activePosition['stopPrice'], price)
                activePosition['exitPrice'] = exitPrice

                activePosition['pnl'] = exitPrice - \
                    activePosition['orderPrice']

            elif activePosition['side'] == 'SELL':
                exitPrice = min(activePosition['stopPrice'], price)
                activePosition['exitPrice'] = exitPrice
                activePosition['pnl'] = activePosition['orderPrice'] - exitPrice

            self.orderList.append(activePosition)
            logger.error(
                f"Closed position: {activePosition} - {len(self.orderList)} orders")
            self.activePosition = None
            self.exportTradesToCSV()
            return 1
        else:
            print("No active position to close")
            return 0

    def exportTradesToCSV(self, filename: str = "trades.csv"):
        if not self.orderList:
            logger.warning("No trades to export.")
            return

        fieldnames = [
            'timestamp', 'symbol', 'side', 'orderType',
            'orderPrice', 'stopPrice', 'exitPrice', 'pnl', 'cumulativePnl'
        ]

        try:
            cumulativePnl = 0
            with open(filename, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

                for order in self.orderList:
                    pnl = order.get('pnl', 0)
                    cumulativePnl += pnl
                    writer.writerow({
                        'timestamp': order.get('timestamp', ''),
                        'symbol': order.get('symbol', ''),
                        'side': order.get('side', ''),
                        'orderType': order.get('orderType', ''),
                        'orderPrice': order.get('orderPrice', ''),
                        'stopPrice': order.get('stopPrice', ''),
                        'exitPrice': order.get('exitPrice', ''),
                        'pnl': pnl,
                        'cumulativePnl': cumulativePnl
                    })

            logger.info(f"Exported {len(self.orderList)} trades to {filename}")
        except Exception as e:
            logger.exception(f"Failed to export trades to CSV: {e}")
