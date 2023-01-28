import enum


class OrderType(enum.Enum):
    Market = 0
    Limit = 1
    Stop = 2
    StopLimit = 3


class OrderStatus(enum.Enum):
    Pending = 0
    Executed = 1


class Side(enum.Enum):
    Buy = 1
    Sell = -1


class TimeInForce(enum.Enum):
    Day = 0
    GTC = -1


class Order:
    def __init__(self, exectype=OrderType.Market, size=1, tif=0, side=Side.Buy, price=None, status=OrderStatus.Pending,
                 oso=None, nextbar=False):
        """
        :param nextbar: True = skip current bar
        """
        self.exectype = exectype
        self.size = size
        self.tif = tif
        self.status = status
        self.side = side
        self.oso = oso
        self.nextbar = nextbar
        self.execprice = None
        self.price = price
