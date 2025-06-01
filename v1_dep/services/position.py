import csv
from typing import Optional, Literal
from datetime import datetime
from utils.logger import logger
from settings import settings


Side = Literal["BUY", "SELL"]

class Exit:
    qty:       float
    price:     float


class Trade:
    timestamp:  datetime
    qty:        float
    entry:      float
    exit:       [Exit] = []
    side:       Side
    orderType:  Literal["STOP_MARKET", "LIMIT"]
    pnl:        float
    totalRisk:  float = 0.0

    sl:         float
    tp:         Optional[float]

    bookedHalfTpProfit: bool = False
    bookedFullTpProfit: bool = False


class Position:
    activePosition: Optional[Trade] = None
    orderList: list[Trade] = []

    async def get_total_pnl(self) -> float:
        if not self.orderList:
            return 0.0
        pnl = sum(order['pnl'] for order in self.orderList if 'pnl' in order)
        if (pnl > 0):
            logger.info(f"Total Pnl for all orders: {pnl}")
        elif (pnl < 0):
            logger.error(f"Total Pnl for all orders: {pnl}")
        else:
            print(f"NO PNL, {self.orderList}")

        print(f"Total Balance: {await self.getBalanceUSD() + pnl}")
        return sum(order['pnl'] for order in self.orderList if 'pnl' in order)

    async def getBalanceUSD(self) -> float:
        # API Call to get the balance in USD
        return 1000

    async def getMinQty(self, symbol: str) -> float:
        minSizes = {
            "BTCUSDT": 0.001,
            "ETHUSDT": 0.01,
            "BNBUSDT": 0.01,
            "XRPUSDT": 1.0,
            "LTCUSDT": 0.01,
            "ADAUSDT": 1.0,
            "SOLUSDT": 0.01,
        }
        size = minSizes.get(symbol)
        if size is None:
            logger.error(f"Symbol {symbol} not found in min sizes.")
            raise ValueError(f"Symbol {symbol} not found in min sizes.")
        return size

    def printActivePosition(self):
        if not self.activePosition:
            return
        for key, value in self.activePosition.items():
            print(f"\t{key}: {value}")

    async def open_position(self, symbol: str, side: Side, price: float, atr: float, entry_time: datetime):
        if self.activePosition:
            logger.warning("Position already open, cannot open a new one.")
            return

        balance = await self.getBalanceUSD()
        minSize = await self.getMinQty(symbol)
        qty = settings.unitTradeSize * 3

        if qty < minSize:
            raise ValueError(f"Invalid Quantity: {qty} is less than minimum size {minSize} for symbol {symbol}.")
        elif balance <= 0:
            raise ValueError("Insufficient balance to open a position.")
        elif qty * price > balance:
            logger.warn(f"Position size {qty} of value {qty*price} exceeds available balance {balance}. No Position opened.")
            return

        sl = price - (atr * settings.trailSLMultiplier) if side == "BUY" else price + (atr * settings.trailSLMultiplier)
        self.activePosition = {
            'timestamp': entry_time,
            'qty': qty,
            'entry': price,
            'side': side,
            'orderType': 'STOP_MARKET',
            'pnl': 0.0,
            'totalRisk': (sl - price if side == "BUY" else price - sl) * qty,

            'sl': sl,
            'tp': price + ((atr * settings.trailSLMultiplier) if side == "BUY" else -(atr * settings.trailSLMultiplier))*2,
            'bookedHalfTpProfit': False,
            'bookedFullTpProfit': False,
            'exit': []
        }
        logger.info("Position opened: ")
        self.printActivePosition()

    async def sl_ticker(self, open: float, high: float, low: float, close: float):
        if not self.activePosition:
            return

        if self.activePosition['side'] == "BUY":
            if low <= self.activePosition['sl']:
                await self.close_position(exit_price=self.activePosition['sl'])
        elif self.activePosition['side'] == "SELL":
            if high >= self.activePosition['sl']:
                await self.close_position(exit_price=self.activePosition['sl'])

    async def tp_ticker(self, open: float, high: float, low: float, close: float):
        if not self.activePosition:
            return

        half_profit = (self.activePosition['tp'] - self.activePosition['entry']) / 2 + self.activePosition['entry']

        if self.activePosition['side'] == "BUY":
            if not self.activePosition['bookedHalfTpProfit'] and high >= half_profit:
                self.activePosition['sl'] = self.activePosition['entry']
                await self.close_position(exit_price=half_profit, exit_size=self.activePosition['qty'] / 3)
                self.activePosition['bookedHalfTpProfit'] = True
            elif not self.activePosition['bookedFullTpProfit'] and high >= self.activePosition['tp']:
                self.activePosition['sl'] = half_profit
                await self.close_position(exit_price=self.activePosition['tp'], exit_size=self.activePosition['qty'] * 1 / 2)
                self.activePosition['bookedFullTpProfit'] = True
        elif self.activePosition['side'] == "SELL":
            if not self.activePosition['bookedHalfTpProfit'] and low <= half_profit:
                self.activePosition['sl'] = self.activePosition['entry']
                await self.close_position(exit_price=half_profit, exit_size=self.activePosition['qty'] / 3)
                self.activePosition['bookedHalfTpProfit'] = True
            elif not self.activePosition['bookedFullTpProfit'] and low <= self.activePosition['tp']:
                self.activePosition['sl'] = half_profit
                await self.close_position(exit_price=self.activePosition['tp'], exit_size=self.activePosition['qty'] * 1 / 2)
                self.activePosition['bookedFullTpProfit'] = True

    async def position_ticker(self, open:float, high: float, low: float, close: float):
        if not self.activePosition:
            return

        await self.sl_ticker(open, high, low, close)
        await self.tp_ticker(open, high, low, close)

    async def close_position(self, exit_price: float, exit_size: Optional[float] = None):
        if not self.activePosition:
            logger.warning("No active position to close.")
            return

        if exit_size is None:
            exit_size = self.activePosition['qty']
        elif exit_size > self.activePosition['qty']:
            exit_size = self.activePosition['qty']
        else:
            exit_size = exit_size

        if exit_size <= 0:
            raise ValueError("Exit size must be greater than zero.")

        entry_price = self.activePosition['entry']
        side = self.activePosition['side']
        pnl = ((exit_price - entry_price) if side == "BUY" else (entry_price - exit_price)) * exit_size

        self.activePosition['exit'].append({
            'qty': exit_size,
            'price': exit_price
        })
        self.activePosition['pnl'] += pnl
        self.activePosition['qty'] -= exit_size

        if (self.activePosition['qty'] <= 0):
            logger.info("Closed position: ")
            self.printActivePosition()
            self.orderList.append(self.activePosition)
            self.activePosition = None
        else:
            logger.info("Partial close: ")
            self.printActivePosition()

    def format_exits(self, exits: list[Exit]) -> str:
        if not exits:
            return "??"
        return " -- ".join(f"{e['price']} | {e['qty']}" for e in exits)

    def export_to_csv(self, filename: str = "trades.csv"):
        if not self.orderList or len(self.orderList[0]) == 0:
            return

        keys = list(self.orderList[0].keys())
        keys.append('cumulativePnl')

        try:
            with open(filename, mode='w', newline='') as file:
                cumulativePnl = 0
                writer = csv.DictWriter(file, fieldnames=keys)
                writer.writeheader()

                for order in self.orderList:
                    pnl = order.get('pnl', 0)
                    cumulativePnl += pnl
                    writer.writerow({
                        'timestamp': order.get('timestamp', ''),
                        'totalRisk': order.get('totalRisk', ''),
                        'qty': order.get('qty', ''),
                        'entry': order.get('entry', ''),
                        'exit': self.format_exits(order.get('exit', [])),
                        'side': order.get('side', ''),
                        'orderType': order.get('orderType', ''),
                        'pnl': pnl,
                        'cumulativePnl': cumulativePnl,
                        'sl': order.get('sl', ''),
                        'tp': order.get('tp', '')
                    })
            print(f"Exported {len(self.orderList)} trades to {filename}")

        except Exception as e:
            logger.exception(f"Failed to export trades to CSV: {e}")
