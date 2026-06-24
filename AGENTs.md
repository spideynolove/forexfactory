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

# Full crawl via Docker (MongoDB + scraper in containers)
docker compose run --rm scraper /bin/sh crawl_all.sh

# Query MongoDB results
python query_mongo.py stats
python query_mongo.py bars --instrument EURUSD --interval H1 --limit 10
python query_mongo.py positions --instrument USDJPY
python query_mongo.py calendar --currency USD --impact high
python query_mongo.py news --json

# Install a new package
uv pip install <package>
```

## Architecture

This is a Scrapy project that scrapes forex economic data from forexfactory.com and stores it in MongoDB.

### Request pattern

- **calendar / calendar_history / market_upcoming**: GET `https://www.forexfactory.com/calendar?day=...`. Calendar data is embedded as `window.calendarComponentStates` JSON in a `<script>` tag — not in the HTML table.
- **news**: GET `https://www.forexfactory.com/news`. Data is in `<news-block-component>` custom elements.
- **market_instruments / market_bars**: hit `https://mds-api.forexfactory.com`.
- **market_positions**: GET `https://www.forexfactory.com/explorerapi.php`. The `pos` field is always int `0`; real ratios come from `traders_ratio`, `traders_long`, `traders_short`.
- **market_indicators_news**: GET `https://www.forexfactory.com/market/...`.

Every request sets `meta={'impersonate': 'chrome'}` for the `scrapy-impersonate` download handler.

### Proxy rotation

`scrapy-rotating-proxies` handles proxy rotation and ban detection. Configure via:
- `PROXY_LIST_PATH` env var — path to plain-text `host:port` proxy list
- `ROTATING_PROXY_PAGE_RETRY_TIMES = 10` — retries per page with different proxies
- `BanDetectionMiddleware` marks proxies dead on timeouts and connection errors

`docker-compose.yml` mounts `~/proxies.txt` into the container at `/proxies/proxies.txt`.

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
- `now()` — returns current UTC datetime (patchable in tests)

### Environment

MongoDB connection defaults to `mongodb://localhost:27018`, database `forexfactory`. Override via `MONGODB_URI` and `MONGODB_DATABASE` env vars. Docker compose passes `mongodb://mongo:27017` (internal network).
