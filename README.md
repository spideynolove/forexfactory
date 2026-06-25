# forexfactory

Scrapy project that crawls [ForexFactory](https://www.forexfactory.com) and stores data in MongoDB.

## Spiders

| Spider | Params | Data |
|---|---|---|
| `calendar` | — | Today's economic events (impact, currency, actual/forecast/previous) |
| `calendar_history` | `START,END` | Historical events over a date range (max 365 days) |
| `news` | — | All 5 news feeds: latest, hottest, most viewed, latest FA, latest TA |
| `market_instruments` | `sym1,sym2,...` | Live instrument metrics |
| `market_bars` | `SYMBOL,COUNT,INTERVAL` | OHLCV bars |
| `market_positions` | `SYMBOL,LIMIT,INTERVAL` | Long/short trader ratio time-series |
| `market_upcoming` | `SYMBOL[,LIMIT]` | Upcoming economic events for an instrument |
| `market_indicators_news` | `SYMBOL[,INTERVAL]` | Indicator news for an instrument |

Valid intervals: `M1 M5 M15 M30 H1 H4 D1 W1`

## Setup

### Local

Activate whatever Python environment you use, then install dependencies:

```bash
pip install -r requirements.txt
```

MongoDB defaults to `mongodb://localhost:27018`, database `forexfactory`. Override via env vars:

```bash
export MONGODB_URI=mongodb://host:27018
export MONGODB_DATABASE=mydb
```

### Docker (recommended)

Docker runs MongoDB and the scraper in isolated containers. **You do not need to install Python, activate any conda/virtualenv, or run `pip install` yourself** — the Dockerfile handles all of that inside the container. Any Python environment on your host machine is irrelevant.

Data is stored in a named Docker volume (`mongo_data`) that persists on your host across container restarts.

```bash
# Start MongoDB only
docker compose up -d mongo

# Full crawl — no proxies
docker compose run --rm scraper /bin/sh crawl_all.sh

# Full crawl — with proxies (mount your proxy list into the container)
docker compose run --rm \
  -e PROXY_LIST_PATH=/proxies/proxies.txt \
  -v ~/proxies.txt:/proxies/proxies.txt:ro \
  scraper /bin/sh crawl_all.sh
```

## Proxy rotation

Proxies are **optional**. Set `PROXY_LIST_PATH` to a plain-text `host:port` file (one per line) to enable `scrapy-rotating-proxies`. If unset, the proxy middleware is not loaded and requests go direct.

```bash
# Local — no proxies
scrapy crawl calendar

# Local — with proxies
PROXY_LIST_PATH=~/proxies.txt scrapy crawl calendar
```

## Usage

All scrapy commands run from the project root:

```bash
scrapy crawl calendar
scrapy crawl calendar_history -a params=2024-01-01,2024-12-31
scrapy crawl news
scrapy crawl market_instruments -a params=eurusd,gbpusd,usdjpy
scrapy crawl market_bars -a params=eurusd,100,H1
scrapy crawl market_positions -a params=usdjpy,100,H1
scrapy crawl market_upcoming -a params=eurusd,20
scrapy crawl market_indicators_news -a params=eurusd,H1
```

Run without writing to MongoDB:

```bash
scrapy crawl calendar -s ITEM_PIPELINES={}
```

## Querying results

`query_mongo.py` is a CLI for all 7 collections:

```bash
python query_mongo.py stats                                      # row counts
python query_mongo.py bars --instrument EURUSD --interval H1    # OHLCV bars
python query_mongo.py positions --instrument USDJPY --limit 50  # trader ratios
python query_mongo.py calendar --currency USD --impact high     # calendar events
python query_mongo.py news --limit 10 --json                    # raw JSON output
python query_mongo.py upcoming --instrument EURUSD
python query_mongo.py indicator_news --instrument GBPUSD --interval H1
python query_mongo.py instruments
python query_mongo.py query bars --instrument AUDUSD --since "2026-01-01"
```

Pass `--uri mongodb://host:port` to connect to a non-default MongoDB instance.

## MongoDB collections

| Collection | Upsert key |
|---|---|
| `calendar` | `event_id` + `datetime` |
| `news` | `news_type` + `news_id` |
| `instruments` | `instrument` + `fetched_at` |
| `bars` | `instrument` + `interval` + `datetime` |
| `positions` | `instrument` + `interval` + `datetime` |
| `upcoming` | `instrument` + `event_id` |
| `indicator_news` | `instrument` + `datetime` + `title` |

## Tests

```bash
pytest tests/ -v
pytest tests/test_parsers.py::test_calendar_parse
```
