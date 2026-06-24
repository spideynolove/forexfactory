import scrapy


class CalendarItem(scrapy.Item):
    collection = 'calendar'
    unique_key = ('event_id', 'datetime')
    event_id = scrapy.Field()
    datetime = scrapy.Field()
    currency = scrapy.Field()
    impact = scrapy.Field()
    event_type = scrapy.Field()
    title = scrapy.Field()
    actual = scrapy.Field()
    forecast = scrapy.Field()
    previous = scrapy.Field()
    source_url = scrapy.Field()


class NewsItem(scrapy.Item):
    collection = 'news'
    unique_key = ('news_type', 'datetime', 'title')
    news_type = scrapy.Field()
    datetime = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    mainterm = scrapy.Field()
    instrument = scrapy.Field()
    source_url = scrapy.Field()


class InstrumentItem(scrapy.Item):
    collection = 'instruments'
    unique_key = ('instrument', 'fetched_at')
    instrument = scrapy.Field()
    metrics = scrapy.Field()
    fetched_at = scrapy.Field()


class BarItem(scrapy.Item):
    collection = 'bars'
    unique_key = ('instrument', 'interval', 'datetime')
    instrument = scrapy.Field()
    interval = scrapy.Field()
    datetime = scrapy.Field()
    open_ = scrapy.Field()
    high_ = scrapy.Field()
    low_ = scrapy.Field()
    close_ = scrapy.Field()
    volume_ = scrapy.Field()


class PositionItem(scrapy.Item):
    collection = 'positions'
    unique_key = ('instrument', 'interval', 'datetime')
    instrument = scrapy.Field()
    interval = scrapy.Field()
    datetime = scrapy.Field()
    long_pct = scrapy.Field()
    short_pct = scrapy.Field()
    net = scrapy.Field()
    trader_count = scrapy.Field()
    stats = scrapy.Field()


class UpcomingItem(scrapy.Item):
    collection = 'upcoming'
    unique_key = ('instrument', 'event_id')
    instrument = scrapy.Field()
    event_id = scrapy.Field()
    datetime = scrapy.Field()
    impact = scrapy.Field()
    currency = scrapy.Field()
    title = scrapy.Field()
    source_url = scrapy.Field()


class IndicatorNewsItem(scrapy.Item):
    collection = 'indicator_news'
    unique_key = ('instrument', 'datetime', 'title')
    instrument = scrapy.Field()
    interval = scrapy.Field()
    datetime = scrapy.Field()
    impact = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    source_url = scrapy.Field()
