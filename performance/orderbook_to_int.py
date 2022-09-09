import timeit
import numpy as np
from feed_handlers.market_data_feed import prices_to_int, prices_to_str, sizes_to_int
from order_book import SortedDict, OrderBook
import requests
from decimal import Decimal
import pickle

from functools import wraps
import time

def profile(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        measures = []
        for i in range(1000):
            start = time.time()
            ret = f(*args, **kwargs)
            total_time = time.time() - start
            measures.append(total_time)
        measures = np.array(measures)
        mean = np.mean(measures)
        std = np.std(measures)
        print(f"Mean time: {mean * 1000 * 1000:.6f} µs")
        print(f"Std time: {std * 1000 * 1000:.6f} µs")
        return ret
    return wrapper

@profile
def profile_prices_to_int(side: SortedDict):
    return prices_to_int(side)

@profile
def profile_prices_to_str(side: SortedDict):
    return prices_to_str(side)

@profile
def profile_sizes_to_int(side: SortedDict):
    return sizes_to_int(side)

@profile
def profile_pickle_ob(ob: OrderBook):
    ob_dict = ob.to_dict()
    with open('ob_pickle_perf.p', 'wb') as handle:
        pickle.dump(ob_dict, handle)

@profile
def profile_unpickle_ob(ob_path: str):
    with open(ob_path, 'rb') as handle:
        ob = pickle.load(handle)


def sample_coinbase_orderbook():
    ob = OrderBook()

    # get some orderbook data
    data = requests.get("https://api.pro.coinbase.com/products/BTC-USD/book?level=2").json()

    ob.bids = {Decimal(price): size for price, size, _ in data['bids']}
    ob.asks = {Decimal(price): size for price, size, _ in data['asks']}
    return ob


def sample_ftx_orderbook():
    with open('serialized_ftx.p', 'rb') as handle:
        res  = pickle.load(handle)
    ob = OrderBook()
    ob.bids = {Decimal(price): size for price, size, in res['bid'].items()}
    ob.asks = {Decimal(price): size for price, size, in res['ask'].items()}
    return ob


if __name__ == '__main__':
    ob = sample_ftx_orderbook()
    # print('Prices to int performance')
    # prices = profile_prices_to_int(ob.bids)
    # print('Sizes to int performance')
    # profile_sizes_to_int(ob.bids)
    # print('Pickle ob performance')
    # profile_pickle_ob(ob)
    # print('Unpickle ob performance')
    # profile_unpickle_ob('ob_pickle_perf.p')

