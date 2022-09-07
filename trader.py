import zmq
from multiprocessing import shared_memory

def receiver(port):
    addr = 'tcp://127.0.0.1:{}'.format(port)
    ctx = zmq.Context.instance()
    s = ctx.socket(zmq.SUB)
    s.setsockopt(zmq.SUBSCRIBE, b'')
    exchange = 'FTX'
    symbol= 'BTC-USD-PERP'
    s.bind(addr)
    while True:
        shm_bid = shared_memory.SharedMemory(name='bids_{}_{}_shm'.format(exchange, symbol))
        shm_ask = shared_memory.SharedMemory(name='asks_{}_{}_shm'.format(exchange, symbol))
        data = s.recv_string()
        print(data)
        print('bid = {}'.format(shm_bid.buf))
        print('ask = {}'.format(shm_ask.buf))


if __name__ == '__main__':
    receiver(5678)
