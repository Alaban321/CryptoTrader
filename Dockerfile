FROM python:3.8-slim-bullseye

WORKDIR /crypto_trader

RUN mkdir /crypto_trader/external
RUN mkdir /crypto_trader/external/config
RUN mkdir /crypto_trader/external/logs
RUN mkdir /crypto_trader/feed_handlers

COPY ./requirements.txt /crypto_trader/requirements.txt
COPY ./start.sh /crypto_trader/start.sh
COPY ./feed_handlers/market_data_feed.py /crypto_trader/feed_handlers/market_data_feed.py
COPY ./trader.py /crypto_trader/trader.py
COPY ./main.py /crypto_trader/main.py
COPY ./logger.py /crypto_trader/logger.py


RUN apt update
RUN apt install gcc git -y

RUN pip install --no-cache-dir --upgrade -r /crypto_trader/requirements.txt

RUN chmod +x /crypto_trader/start.sh

CMD ["/crypto_trader/start.sh"]
