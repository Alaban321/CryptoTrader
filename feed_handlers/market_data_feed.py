from cryptofeed.feedhandler import FeedHandler
from cryptofeed.defines import L2_BOOK
from cryptofeed.exchanges import EXCHANGE_MAP
import pickle
from pprint import pprint
# import sys
import time
from multiprocessing import shared_memory
import zmq
import zmq.asyncio
import asyncio
# from cryptofeed.backends.zmq import BookZMQ

class MarketFeedHandler:
    """
    Class that wraps cryptofeed FeedHandler, passes event messages to other components
    and exposes reconstructed orderbook through shared memory
    """


    def __init__(self, config: str, measure_time : bool = False):
        self.fh = FeedHandler(config)
        self.running = False



        # self.socket = context.socket(zmq.PUB)
        # self.socket.bind('tcp://127.0.0.1:{}'.format(self.zmq_pub_port))

        # shared memory
        self.shared_memory_book_size = 140# * 100
        self.shm_bids = {}
        self.shm_asks = {}

        # time measurement
        self.measure_time = measure_time
        if self.measure_time:
            self.book_process_time = []
            self.book_to_shared_memory_time = []
            self.count = 0
            self.count_max = 5000

    async def zmq_pub(self, ts):
        # zmq
        host = '127.0.0.1'
        port = 5678
        url = "tcp://{}:{}".format(host, port)
        context = zmq.asyncio.Context.instance()
        con = context.socket(zmq.PUB)
        con.connect(url)
        while self.running:
            await con.send_string('Book event received on {}'.format(ts))

    def add_feed(self, exchange: str, symbols: list):
        for symbol in symbols:
            self.shm_bids[(exchange, symbol)] = shared_memory.SharedMemory(name='bids_{}_{}_shm'.format(exchange, symbol), create=True, size=self.shared_memory_book_size)
            self.shm_asks[(exchange, symbol)] = shared_memory.SharedMemory(name='asks_{}_{}_shm'.format(exchange, symbol), create=True, size=self.shared_memory_book_size)

        assert exchange in EXCHANGE_MAP
        channels = [L2_BOOK]
        # callbacks = {L2_BOOK: [self.on_book, BookZMQ(snapshots_only=False, snapshot_interval=2, port=5678)]}
        callbacks = {L2_BOOK: self.on_book}
        # callbacks = {L2_BOOK: self.on_book}
        feed = EXCHANGE_MAP[exchange](symbols=symbols, channels=channels, callbacks=callbacks)
        self.fh.add_feed(feed)

    def feeds(self):
        return self.fh.feeds

    def run(self):
        self.running = True
        # loop = asyncio.get_event_loop()
        # loop.create_task()
        self.fh.run(start_loop=True)

    def stop(self):
        self.running = False
        self.fh.stop()

    async def on_book(self, data, receipt_timestamp):
        if self.measure_time:
            self.count += 1
            if self.count >= self.count_max:

                with open('feed_stats.p', 'wb') as handle:
                    to_dump = {
                        'book_process_time': self.book_process_time,
                        'book_to_shared_memory_time': self.book_to_shared_memory_time
                    }
                    pickle.dump(to_dump, handle)
                print('Wrote file.')
                for sh in self.shm_bids:
                    self.shm_bids[sh].close()
                self.fh.stop()

            if self.count < self.count_max:
                time_1 = time.time()
                self.book_process_time.append(time_1 - receipt_timestamp)
                ob = data.book
                buffer = self.shm_bids[('FTX', 'BTC-USD-PERP')].buf
                buffer = ob.bids.index(0)[0]
                buffer = self.shm_asks[('FTX', 'BTC-USD-PERP')].buf
                buffer = ob.asks.index(0)[0]
                time_2 = time.time()
                self.book_to_shared_memory_time.append(time_2 - time_1)
                await self.zmq_pub(receipt_timestamp)
                print('events left: {}'.format(self.count_max - self.count))


if __name__ == '__main__':

    def debug_market_data_feedhandler():
        config = {'uvloop': True, 'log': {'disabled': True}}
        market_data_handler = MarketFeedHandler(config, measure_time=True)
        symbols = ['BTC-USD-PERP']
        market_data_handler.add_feed(exchange='FTX', symbols=symbols)
        market_data_handler.run()

    debug_market_data_feedhandler()
