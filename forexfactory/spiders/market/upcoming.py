import json

from scrapy import Spider, Request

from forexfactory.items import UpcomingItem
from forexfactory.utils import headers, get_unixtime


class UpcomingSpider(Spider):
    name = 'market_upcoming'
    allowed_domains = ['forexfactory.com']

    def __init__(self, params=None, *args, **kwargs):
        super(UpcomingSpider, *args, **kwargs)
        if not params:
            raise ValueError('params required: SYMBOL,LIMIT (e.g., eurusd,20)')

        parts = [p.strip() for p in params.split(',')]
        if len(parts) == 1:
            self.symbol = parts[0].upper()
            self.limit = 20
        elif len(parts) == 2:
            self.symbol, limit_str = parts
            self.symbol = self.symbol.upper()
            self.limit = int(limit_str)
        else:
            raise ValueError('params format: SYMBOL,LIMIT (e.g., eurusd,20)')

        if self.limit < 1 or self.limit > 100:
            raise ValueError('LIMIT must be between 1 and 100')

    def start_requests(self):
        yield Request(
            f'https://www.forexfactory.com/upcoming/{self.symbol}?limit={self.limit}',
            headers=headers,
            callback=self.parse,
            errback=self.handle_error,
            meta={'impersonate': 'chrome', 'symbol': self.symbol},
        )

    def parse(self, response):
        if response.status != 200:
            self.logger.warning(f'Upcoming request failed: {response.status}')
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning('Failed to parse upcoming JSON')
            return

        for event in data.get('events', []):
            event_id = event.get('id') or event.get('event_id')
            if not event_id:
                continue

            dateline = event.get('dateline')
            if not dateline:
                continue

            datetime_str = get_unixtime(str(dateline), divide=1, have_hour=True, timezone='UTC')

            impact = event.get('impact_name')
            if impact and impact.lower() == 'low':
                continue

            currency = event.get('currency', '')
            title = event.get('name', '')

            if not currency or not title:
                self.logger.debug(f'Missing required fields in event: {event}')
                continue

            item = UpcomingItem()
            item['instrument'] = response.meta.get('symbol', '')
            item['event_id'] = str(event_id)
            item['datetime'] = datetime_str
            item['impact'] = impact
            item['currency'] = currency
            item['title'] = title
            item['source_url'] = response.url

            yield item

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
