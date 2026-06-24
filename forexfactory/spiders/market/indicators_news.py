import json

from scrapy import Spider, Request

from forexfactory.items import IndicatorNewsItem
from forexfactory.utils import headers, get_unixtime, now, tran_s, SPECIALS


VALID_INTERVALS = {'M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1'}


class IndicatorsNewsSpider(Spider):
    name = 'market_indicators_news'
    allowed_domains = ['mds-api.forexfactory.com']

    def __init__(self, params=None, *args, **kwargs):
        super(IndicatorsNewsSpider, *args, **kwargs)
        if not params:
            raise ValueError('params required: SYMBOL,INTERVAL (e.g., eurusd,H1)')

        parts = [p.strip() for p in params.split(',')]
        if len(parts) == 1:
            self.symbol = parts[0].upper()
            self.interval = 'H1'
        elif len(parts) == 2:
            self.symbol, self.interval = parts
            self.symbol = self.symbol.upper()
            self.interval = self.interval.upper()
        else:
            raise ValueError('params format: SYMBOL,INTERVAL (e.g., eurusd,H1)')

        if self.interval not in VALID_INTERVALS:
            raise ValueError(f'INTERVAL must be one of {", ".join(sorted(VALID_INTERVALS))}')

    def start_requests(self):
        to_ts = int(now().timestamp())
        from_ts = to_ts - 86400
        instrument = SPECIALS.get(self.symbol.lower(), tran_s(self.symbol))
        url = (
            f'https://mds-api.forexfactory.com/indicators/news'
            f'?instrument={instrument}'
            f'&interval={self.interval}'
            f'&from={from_ts}&to={to_ts}'
        )
        yield Request(
            url,
            headers=headers,
            callback=self.parse,
            errback=self.handle_error,
            meta={'impersonate': 'chrome', 'symbol': self.symbol, 'interval': self.interval},
        )

    def parse(self, response):
        if response.status != 200:
            self.logger.warning(f'Indicators news request failed: {response.status}')
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning('Failed to parse indicators news JSON')
            return

        for item_data in data.get('data', []):
            timestamp = item_data.get('timestamp')
            if not timestamp:
                continue

            datetime_str = get_unixtime(str(timestamp), divide=1, have_hour=True, timezone='UTC')

            impact = item_data.get('impact')
            if impact and impact.lower() == 'low':
                continue

            title = item_data.get('title', '')
            if not title:
                continue

            item = IndicatorNewsItem()
            item['instrument'] = response.meta.get('symbol', '')
            item['interval'] = response.meta.get('interval', '')
            item['datetime'] = datetime_str
            item['impact'] = impact
            item['title'] = title
            item['content'] = item_data.get('content')
            item['source_url'] = response.url

            yield item

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
