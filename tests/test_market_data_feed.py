import pickle
from order_book import OrderBook
from decimal import Decimal
from feed_handlers.market_data_feed import prices_to_int, sizes_to_int


def sample_ftx_orderbook():
    with open('serialized_ftx.p', 'rb') as handle:
        res = pickle.load(handle)
    ob = OrderBook()
    ob.bids = {Decimal(price): size for price, size, in res['bid'].items()}
    ob.asks = {Decimal(price): size for price, size, in res['ask'].items()}
    return ob


def test_prices_to_int():
    ob = sample_ftx_orderbook()
    prices = prices_to_int(ob.bids)
    for price in prices:
        assert isinstance(price, int)


def test_sizes_to_int():
    ob = sample_ftx_orderbook()
    sizes = sizes_to_int(ob.bids)
    for size in sizes:
        assert isinstance(size, int)
