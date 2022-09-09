import sys
sys.path.append('/crypto_trader')

import asyncio
import zmq
from zmq.asyncio import Context
from logger import get_logger

LOG = get_logger()

class Trader:

    name = 'Trader'

    def __init__(self):
        self.id = 'dev'
        context = Context.instance()
        self.zmq_book_port = 5678
        self.book_socket = context.socket(zmq.SUB)
        self.loop = asyncio.get_event_loop()

    async def book_listener(self):
        while True:
            msg = await self.book_socket.recv_string()
            LOG.info('{} {}: received book event {}'.format(self.name, self.id, msg))

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
        self.heartbeat_task = self.loop.create_task(self.heartbeat())
        self.book_listener_task = self.loop.create_task(self.book_listener())
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
