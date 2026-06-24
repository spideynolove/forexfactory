#!/bin/sh

PAIRS="eurusd,gbpusd,usdjpy,gbpjpy,audusd,usdcad,usdchf"
INTERVAL="H1"
LIMIT="200"

echo "==> calendar"
scrapy crawl calendar

echo "==> news"
scrapy crawl news

echo "==> market_instruments"
scrapy crawl market_instruments -a params="$PAIRS"

for SYM in eurusd gbpusd usdjpy audusd; do
    echo "==> market_bars $SYM $INTERVAL"
    scrapy crawl market_bars -a params="$SYM,$LIMIT,$INTERVAL"

    echo "==> market_positions $SYM $INTERVAL"
    scrapy crawl market_positions -a params="$SYM,$LIMIT,$INTERVAL"

    echo "==> market_upcoming $SYM"
    scrapy crawl market_upcoming -a params="$SYM,20"

    echo "==> market_indicators_news $SYM $INTERVAL"
    scrapy crawl market_indicators_news -a params="$SYM,$INTERVAL"
done

echo "==> Done."
