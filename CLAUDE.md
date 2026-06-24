# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtualenv before any Python work
source ~/env/.venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Run all tests (from project root, where tests/ lives)
pytest tests/

# Run a single test
pytest tests/test_parsers.py::test_calendar_parse

# All scrapy commands run from project root (scrapy.cfg is at repo root)
scrapy crawl calendar
scrapy crawl calendar_history -a params=2024-01-01,2024-01-31
scrapy crawl news
scrapy crawl market_positions -a params=usdjpy,100,H1
scrapy crawl market_instruments -a params=eurusd,gbpusd
scrapy crawl market_bars -a params=eurusd,100,H1
scrapy crawl market_upcoming -a params=eurusd,20
scrapy crawl market_indicators_news -a params=eurusd,H1

# Install a new package
uv pip install <package>
```

## Architecture

This is a Scrapy project that scrapes forex economic data from forexfactory.com and stores it in MongoDB.

### Request pattern

All calendar and news spiders POST to `https://www.forexfactory.com/flex.php` using hardcoded multipart/form-data payloads defined in `payloads.py`. Market data spiders (instruments, bars) hit `https://mds-api.forexfactory.com`. Every request sets `meta={'impersonate': 'chrome'}` for the `scrapy-impersonate` download handler.

### Items and MongoDB storage

Each item class in `items.py` declares two class attributes:
- `collection` — the MongoDB collection name
- `unique_key` — a tuple of field names used as the composite upsert key

`MongoPipeline` reads these at runtime to route and upsert items. Missing `unique_key` fields raise `DropItem`.

### Spider params convention

Multi-argument spiders accept a single `-a params=...` string that is split by comma internally. Validation (range checks, format) happens in `__init__`. Intervals for market spiders: `M1 M5 M15 M30 H1 H4 D1 W1`.

### Utilities (utils.py)

- `headers` — shared request headers dict (User-Agent, Accept, Referer, Origin)
- `get_unixtime(timestamp, divide, have_hour, timezone)` — converts unix timestamps to `YYYY-MM-DD HH:MM` strings
- `clean_lst(text_list)` — joins and normalizes whitespace from XPath text node lists
- `get_num(string)` — strips non-numeric characters, used for actual/forecast/previous fields
- `tran_s(sstr)` — converts 6-char symbol like `eurusd` to `EUR/USD`
- `SPECIALS` — maps non-standard symbols (`nikkei`, `gold`) to their API names

### Environment

MongoDB connection defaults to `mongodb://localhost:27017`, database `forexfactory`. Override via `MONGODB_URI` and `MONGODB_DATABASE` env vars.
