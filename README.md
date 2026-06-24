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
| `market_positions` | `SYMBOL,LIMIT,INTERVAL` | Long/short ratio time-series + stats |
| `market_upcoming` | `SYMBOL[,LIMIT]` | Upcoming economic events for an instrument |
| `market_indicators_news` | `SYMBOL[,INTERVAL]` | Indicator news for an instrument |

Valid intervals: `M1 M5 M15 M30 H1 H4 D1 W1`

## Setup

```bash
source ~/env/.venv/bin/activate
uv pip install -r requirements.txt
```

MongoDB defaults to `mongodb://localhost:27017`, database `forexfactory`. Override via env vars:

```bash
export MONGODB_URI=mongodb://host:27017
export MONGODB_DATABASE=mydb
```

## Usage

All scrapy commands run from the `forexfactory/` subdirectory (where `scrapy.cfg` lives):

```bash
cd forexfactory

# Today's calendar
scrapy crawl calendar

# Historical calendar (inclusive date range, max 365 days)
scrapy crawl calendar_history -a params=2024-01-01,2024-12-31

# All news feeds
scrapy crawl news

# Instrument metrics
scrapy crawl market_instruments -a params=eurusd,gbpusd,usdjpy

# OHLCV bars (COUNT 1–500)
scrapy crawl market_bars -a params=eurusd,100,H1

# Long/short positions (LIMIT 1–500)
scrapy crawl market_positions -a params=usdjpy,100,H1

# Upcoming events (LIMIT 1–100, default 20)
scrapy crawl market_upcoming -a params=eurusd,20

# Indicator news (INTERVAL default H1)
scrapy crawl market_indicators_news -a params=eurusd,H1
```

Run without writing to MongoDB (useful for testing):

```bash
scrapy crawl calendar -s ITEM_PIPELINES={}
```

## MongoDB collections

| Collection | Upsert key |
|---|---|
| `calendar` | `event_id` + `datetime` |
| `news` | `news_type` + `datetime` + `title` |
| `instruments` | `instrument` + `fetched_at` |
| `bars` | `instrument` + `interval` + `datetime` |
| `positions` | `instrument` + `interval` + `datetime` |
| `upcoming` | `instrument` + `event_id` |
| `indicator_news` | `instrument` + `datetime` + `title` |

## Tests

```bash
# From project root
pytest tests/ -v

# Single test
pytest tests/test_parsers.py::test_calendar_parse
```
