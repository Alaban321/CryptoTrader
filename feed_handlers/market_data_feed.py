import sys
sys.path.append('/crypto_trader')


from cryptofeed.feedhandler import FeedHandler
from cryptofeed.defines import L2_BOOK
from cryptofeed.exchanges import EXCHANGE_MAP
from decimal import Decimal
# import pickle
# from pprint import pprint
# import sys
# import time
# from multiprocessing import shared_memory
import zmq
import zmq.asyncio
import asyncio

from cryptofeed.backends.zmq import BookZMQ
from order_book import SortedDict
# from numba import jit
from logger import get_logger

LOG = get_logger()

DECIMAL_TO_INT_MULTIPLIER = Decimal(1e9)
INT_MULTIPLIER = 1e9

def prices_to_int(side: SortedDict):
    prices = [int(price * DECIMAL_TO_INT_MULTIPLIER) for price in side]
    return prices

def sizes_to_int(side: SortedDict):
    sizes = [int(side[price] * DECIMAL_TO_INT_MULTIPLIER) for price in side]
    return sizes

def prices_to_str(side: SortedDict):
    prices = [str(price) for price in side]
    return prices

# def _sizes_to_str(side: SortedDict):
#     sizes = [str(size) for _, size in side.items()]
#     return sizes

class MarketFeedHandler:
    """
    Class that wraps cryptofeed FeedHandler, passes event messages to other components
    and exposes reconstructed orderbook through shared memory
    """

    name = 'MarketFeedHandler'

    def __init__(self, config: str, measure_time : bool = False):
        self.fh = FeedHandler(config)
        self.running = False
        self.id = 'dev'
        self.loop = asyncio.get_event_loop()

        context = zmq.asyncio.Context()
        self.zmq_book_port = 5678
        self.socket = context.socket(zmq.PUB)


        # shared memory
        # self.shared_memory_book_size = 140# * 100
        # self.shm_bids = {}
        # self.shm_asks = {}

        # time measurement
        self.measure_time = measure_time
        if self.measure_time:
            self.book_process_time = []
            self.book_to_shared_memory_time = []
            self.count = 0
            self.count_max = 5000

    # async def zmq_pub(self, ts):
    #     # zmq
    #     host = '127.0.0.1'
    #     port = 5678
    #     url = "tcp://{}:{}".format(host, port)
    #     context = zmq.asyncio.Context.instance()
    #     con = context.socket(zmq.PUB)
    #     con.connect(url)
    #     while self.running:
    #         await con.send_string('Book event received on {}'.format(ts))

    def add_feed(self, exchange: str, symbols: list):
        # for symbol in symbols:
            # self.shm_bids[(exchange, symbol)] = shared_memory.SharedMemory(name='bids_{}_{}_shm'.format(exchange, symbol), create=True, size=self.shared_memory_book_size)
            # self.shm_asks[(exchange, symbol)] = shared_memory.SharedMemory(name='asks_{}_{}_shm'.format(exchange, symbol), create=True, size=self.shared_memory_book_size)

        assert exchange in EXCHANGE_MAP
        channels = [L2_BOOK]
        callbacks = {L2_BOOK: self.on_book}
        # callbacks = {L2_BOOK: BookZMQ(snapshots_only=False, snapshot_interval=2, port=5678)}
        feed = EXCHANGE_MAP[exchange](symbols=symbols, channels=channels, callbacks=callbacks)
        self.fh.add_feed(feed)

    def feeds(self):
        return self.fh.feeds

    def run(self):
        LOG.info('{} {} - entering run()'.format(self.name, self.id))
        self.running = True
        LOG.info('{} - {} - bind zmq socket port {}'.format(self.name, self.id, self.zmq_book_port))
        self.socket.bind('tcp://127.0.0.1:{}'.format(self.zmq_book_port))
        self.heartbeat_task = self.loop.create_task(self.heartbeat())
        # loop.create_task()
        self.fh.run(start_loop=False)
        LOG.info('{} {} - starting asyncio loop'.format(self.name, self.id))
        self.loop.run_forever()


    def stop(self):
        LOG.info('{} {} - entering stop()'.format(self.name, self.id))
        self.running = False
        self.loop.run_until_complete(self._cancel_running_task(self.heartbeat_task))
        self.socket.close()
        LOG.info('{} {} - sopping feedhandler'.format(self.name, self.id))
        self.fh.stop()

    async def on_book(self, data, receipt_timestamp):
        msg = 'received book event on {}'.format(receipt_timestamp)
        await self.socket.send_string(msg)
        # LOG.info('{} {} - {}'.format(self.name, self.id, msg))

    async def heartbeat(self):
        while True:
            await asyncio.sleep(5)
            LOG.info('{} {}: heartbeat'.format(self.name, self.id))

    async def _cancel_running_task(self, task):
        LOG.info('{} {}: cancelling task {}'.format(self.name, self.id, task))
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            LOG.info('{} {}: task {} is cancelled now'.format(self.name, self.id, task))


    # async def on_book(self, data, receipt_timestamp):
    #     if self.measure_time:
    #         self.count += 1
    #         if self.count >= self.count_max:
    #
    #             with open('feed_stats.p', 'wb') as handle:
    #                 to_dump = {
    #                     'book_process_time': self.book_process_time,
    #                     # 'book_to_shared_memory_time': self.book_to_shared_memory_time
    #                 }
    #                 pickle.dump(to_dump, handle)
    #             print('Wrote file.')
    #             # for sh in self.shm_bids:
    #             #     self.shm_bids[sh].close()
    #             self.fh.stop()
    #
    #         if self.count < self.count_max:
    #             time_1 = time.time()
    #             self.book_process_time.append(time_1 - receipt_timestamp)
    #             # ob = data.book
    #             # buffer = self.shm_bids[('FTX', 'BTC-USD-PERP')].buf
    #             # buffer = ob.bids.index(0)[0]
    #             # buffer = self.shm_asks[('FTX', 'BTC-USD-PERP')].buf
    #             # buffer = ob.asks.index(0)[0]
    #             time_2 = time.time()
    #             self.book_to_shared_memory_time.append(time_2 - time_1)
    #             await self.zmq_pub(receipt_timestamp)
    #             print('events left: {}'.format(self.count_max - self.count))


if __name__ == '__main__':

    config = {'uvloop': True, 'log': {'disabled': True}}
    market_data_handler = MarketFeedHandler(config, measure_time=True)
    symbols = ['BTC-USD-PERP']
    market_data_handler.add_feed(exchange='FTX', symbols=symbols)
    market_data_handler.run()
