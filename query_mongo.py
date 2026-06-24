import argparse
import json

import pymongo

DEFAULT_URI = "mongodb://localhost:27018"
DB_NAME = "forexfactory"

COLLECTIONS = [
    "calendar",
    "news",
    "instruments",
    "bars",
    "positions",
    "upcoming",
    "indicator_news",
]


def get_db(uri=DEFAULT_URI):
    return pymongo.MongoClient(uri)[DB_NAME]


def cmd_stats(args):
    db = get_db(args.uri)
    print(f"{'Collection':<20} {'Count':>8}")
    print("-" * 30)
    for col in COLLECTIONS:
        count = db[col].count_documents({})
        print(f"{col:<20} {count:>8}")


def cmd_query(args):
    db = get_db(args.uri)
    col = args.collection
    if col not in COLLECTIONS:
        print(f"Unknown collection. Choose from: {', '.join(COLLECTIONS)}")
        return

    filt = {}
    if args.instrument:
        filt["instrument"] = args.instrument.upper()
    if args.currency:
        filt["currency"] = args.currency.upper()
    if args.interval:
        filt["interval"] = args.interval
    if args.since:
        filt["datetime"] = {"$gte": args.since}
    if args.impact:
        filt["impact"] = args.impact.lower()

    sort_field = args.sort or "datetime"
    limit = args.limit or 20

    cursor = db[col].find(filt, {"_id": 0}).sort(sort_field, -1).limit(limit)
    docs = list(cursor)
    if not docs:
        print("No documents found.")
        return

    if args.json:
        print(json.dumps(docs, indent=2, default=str))
    else:
        for doc in docs:
            parts = []
            for k, v in doc.items():
                if isinstance(v, dict):
                    v = json.dumps(v)
                parts.append(f"{k}={v}")
            print("  ".join(parts))
    print(f"\n({len(docs)} rows)")


def cmd_calendar(args):
    args.collection = "calendar"
    args.instrument = None
    cmd_query(args)


def cmd_news(args):
    args.collection = "news"
    args.instrument = None
    args.interval = None
    cmd_query(args)


def cmd_bars(args):
    args.collection = "bars"
    args.currency = None
    args.impact = None
    cmd_query(args)


def cmd_positions(args):
    args.collection = "positions"
    args.currency = None
    args.impact = None
    cmd_query(args)


def cmd_upcoming(args):
    args.collection = "upcoming"
    args.interval = None
    cmd_query(args)


def cmd_indicator_news(args):
    args.collection = "indicator_news"
    args.currency = None
    cmd_query(args)


def cmd_instruments(args):
    args.collection = "instruments"
    args.currency = None
    args.interval = None
    args.impact = None
    args.since = None
    args.sort = "fetched_at"
    cmd_query(args)


def main():
    p = argparse.ArgumentParser(description="Query ForexFactory MongoDB data")
    p.add_argument("--uri", default=DEFAULT_URI, help="MongoDB URI")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("--limit", type=int, default=20)
        sp.add_argument("--since", help="Filter datetime >= value (string)")
        sp.add_argument("--json", action="store_true", help="Output raw JSON")
        sp.add_argument("--sort", help="Sort field (default: datetime desc)")

    stats_p = sub.add_parser("stats", help="Row counts for all collections")
    stats_p.set_defaults(func=cmd_stats)

    cal_p = sub.add_parser("calendar", help="Economic calendar events")
    add_common(cal_p)
    cal_p.add_argument("--currency", help="Filter by currency, e.g. USD")
    cal_p.add_argument("--impact", help="Filter by impact: High/Medium/Low")
    cal_p.set_defaults(func=cmd_calendar, instrument=None, interval=None)

    news_p = sub.add_parser("news", help="Market news articles")
    add_common(news_p)
    news_p.set_defaults(func=cmd_news, instrument=None, currency=None, interval=None, impact=None)

    inst_p = sub.add_parser("instruments", help="Market instrument snapshots")
    add_common(inst_p)
    inst_p.add_argument("--instrument", help="Filter by symbol, e.g. EURUSD")
    inst_p.set_defaults(func=cmd_instruments, currency=None, impact=None, since=None, sort="fetched_at")

    bars_p = sub.add_parser("bars", help="OHLCV price bars")
    add_common(bars_p)
    bars_p.add_argument("--instrument", help="e.g. EURUSD")
    bars_p.add_argument("--interval", help="e.g. H1")
    bars_p.set_defaults(func=cmd_bars, currency=None, impact=None)

    pos_p = sub.add_parser("positions", help="Trader position ratios")
    add_common(pos_p)
    pos_p.add_argument("--instrument", help="e.g. EURUSD")
    pos_p.add_argument("--interval", help="e.g. H1")
    pos_p.set_defaults(func=cmd_positions, currency=None, impact=None)

    up_p = sub.add_parser("upcoming", help="Upcoming calendar events by instrument")
    add_common(up_p)
    up_p.add_argument("--instrument", help="e.g. EURUSD")
    up_p.add_argument("--impact", help="Filter by impact: High/Medium/Low")
    up_p.set_defaults(func=cmd_upcoming, currency=None, interval=None)

    ind_p = sub.add_parser("indicator_news", help="Indicator-linked news by instrument")
    add_common(ind_p)
    ind_p.add_argument("--instrument", help="e.g. EURUSD")
    ind_p.add_argument("--interval", help="e.g. H1")
    ind_p.add_argument("--impact", help="Filter by impact")
    ind_p.set_defaults(func=cmd_indicator_news, currency=None)

    query_p = sub.add_parser("query", help="Generic query on any collection")
    add_common(query_p)
    query_p.add_argument("collection", choices=COLLECTIONS)
    query_p.add_argument("--instrument")
    query_p.add_argument("--currency")
    query_p.add_argument("--interval")
    query_p.add_argument("--impact")
    query_p.set_defaults(func=cmd_query)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
