import pickle
import sys
import time

sys.path.append('/crypto_trader')

import asyncio
import zmq
from zmq.asyncio import Context
from logger import get_logger
import numpy as np

LOG = get_logger()

class Trader:

    name = 'Trader'

    def __init__(self):
        self.id = 'dev'
        context = Context.instance()
        self.zmq_book_port = 5678
        self.book_socket = context.socket(zmq.SUB)
        self.loop = asyncio.get_event_loop()
        self.tick_count = 0
        self.max_count = 100
        self.zmq_latencies = []

    async def on_tick(self):
        while True:
            msg = await self.book_socket.recv_string()
            now = time.time()
            # LOG.info('{} {}: received {}'.format(self.name, self.id, msg))
            self.tick_count += 1
            received_time = float(msg.split(' ')[-1])
            self.zmq_latencies.append(now - received_time)

            if self.tick_count > self.max_count:
                latencies = np.array(self.zmq_latencies)
                mean = np.mean(latencies) * 1000 * 1000
                std = np.std(latencies) * 1000 * 1000
                worst = np.max(latencies) * 1000 * 1000
                LOG.info('{} {} - latencies stats mean {}µs, std {}µs, worse {}µs'.format(self.name, self.id, mean, std, worst))
                LOG.info('{} {} - resetting zmq latencies'.format(self.name, self.id))
                self.zmq_latencies = []
                self.tick_count = 0

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

    def run(self):
        LOG.info('{} {} - entering run()'.format(self.name, self.id))
        LOG.info('{} {} - connecting to book socket on port {}'.format(self.name, self.id, self.zmq_book_port))
        self.book_socket.connect('tcp://127.0.0.1:{}'.format(self.zmq_book_port))
        self.book_socket.subscribe('BTC-USD-PERP')
        # self.book_socket.subscribe('ETH-USD-PERP')
        self.heartbeat_task = self.loop.create_task(self.heartbeat())
        self.book_listener_task = self.loop.create_task(self.on_tick())
        LOG.info('{} {} - starting asyncio loop'.format(self.name, self.id))
        self.loop.run_forever()

    def stop(self):
        LOG.info('{} {} - entering stop()'.format(self.name, self.id))
        self.loop.run_until_complete(self._cancel_running_task(self.book_listener_task))
        self.loop.run_until_complete(self._cancel_running_task(self.heartbeat_task))
        self.book_socket.close()


if __name__ == '__main__':
    trader = Trader()
    trader.run()
