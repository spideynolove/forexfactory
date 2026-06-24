import json

from scrapy import Spider, Request

from forexfactory.items import BarItem
from forexfactory.utils import headers, get_unixtime, get_num, now, tran_s, SPECIALS


VALID_INTERVALS = {'M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1'}


class BarsSpider(Spider):
    name = 'market_bars'
    allowed_domains = ['mds-api.forexfactory.com']

    def __init__(self, params=None, *args, **kwargs):
        super(BarsSpider, *args, **kwargs)
        if not params:
            raise ValueError('params required: SYMBOL,COUNT,INTERVAL (e.g., eurusd,100,H1)')

        parts = [p.strip() for p in params.split(',')]
        if len(parts) != 3:
            raise ValueError('params format: SYMBOL,COUNT,INTERVAL (e.g., eurusd,100,H1)')

        symbol_raw, count_str, interval = parts
        self.symbol = symbol_raw.upper()
        self.count = int(count_str)
        self.interval = interval.upper()

        if self.count < 1 or self.count > 500:
            raise ValueError('COUNT must be between 1 and 500')

        if self.interval not in VALID_INTERVALS:
            raise ValueError(f'INTERVAL must be one of {", ".join(sorted(VALID_INTERVALS))}')

    def start_requests(self):
        to_ts = str(int(now().timestamp()))
        instrument = SPECIALS.get(self.symbol.lower(), tran_s(self.symbol))
        url = (
            f'https://mds-api.forexfactory.com/bars'
            f'?instrument={instrument}'
            f'&interval={self.interval}'
            f'&per_page={self.count}'
            f'&to={to_ts}'
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
            self.logger.warning(f'Bars request failed: {response.status}')
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning('Failed to parse bars JSON')
            return

        for bar_data in data.get('data', []):
            timestamp = bar_data.get('timestamp')
            if not timestamp:
                continue

            datetime_str = get_unixtime(str(timestamp), divide=1, have_hour=True, timezone='UTC')

            item = BarItem()
            item['instrument'] = response.meta.get('symbol', '').upper()
            item['interval'] = response.meta.get('interval', '')
            item['datetime'] = datetime_str
            item['open_'] = get_num(bar_data.get('open'))
            item['high_'] = get_num(bar_data.get('high'))
            item['low_'] = get_num(bar_data.get('low'))
            item['close_'] = get_num(bar_data.get('close'))
            item['volume_'] = get_num(bar_data.get('volume')) or None

            if not item['open_'] or not item['high_'] or not item['low_'] or not item['close_']:
                self.logger.debug(f'Missing required OHLC fields in bar: {bar_data}')
                continue

            yield item

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
