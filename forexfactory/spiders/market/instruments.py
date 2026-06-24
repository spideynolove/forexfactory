import json

from scrapy import Spider, Request

from forexfactory.items import InstrumentItem
from forexfactory.utils import headers, now, tran_s, SPECIALS


class InstrumentsSpider(Spider):
    name = 'market_instruments'
    allowed_domains = ['mds-api.forexfactory.com']

    def __init__(self, params=None, *args, **kwargs):
        super(InstrumentsSpider, *args, **kwargs)
        if not params:
            raise ValueError('params required: comma-separated symbol pairs (e.g., eurusd,gbpusd)')
        self.symbols = [s.strip().upper() for s in params.split(',') if s.strip()]
        if not self.symbols:
            raise ValueError('At least one symbol required')

    def start_requests(self):
        instruments_param = ','.join(SPECIALS.get(s.lower(), tran_s(s)) for s in self.symbols)
        yield Request(
            f'https://mds-api.forexfactory.com/instruments?instruments={instruments_param}',
            headers=headers,
            callback=self.parse,
            errback=self.handle_error,
            meta={'impersonate': 'chrome'},
        )

    def parse(self, response):
        if response.status != 200:
            self.logger.warning(f'Instruments request failed: {response.status}')
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning('Failed to parse instruments JSON')
            return

        for item_data in data.get('data', []):
            instrument_name = item_data.get('instrument', {}).get('name', '').replace('/', '').lower()
            if not instrument_name:
                continue

            metrics = item_data.get('metrics')
            if not metrics:
                continue

            fetched_at = now().strftime('%Y-%m-%d %H:%M')

            item = InstrumentItem()
            item['instrument'] = instrument_name
            item['metrics'] = metrics
            item['fetched_at'] = fetched_at

            yield item

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
