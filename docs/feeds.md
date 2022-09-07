# Feed Handlers

##  Architecture

Market Feed class in charge of:

- start / stop feed
- handling ws connection / reconnection
- exposing orderbook through shared memory
- passing event messages using zmq


## Cryptofeed

### Compute time

- full 100 levels book reconstruction: ~200µs
- on average reconstructing a 100 levels book is 50-100µs 