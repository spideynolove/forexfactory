import json

from scrapy import Spider, Request

from forexfactory.items import PositionItem
from forexfactory.utils import headers, get_unixtime, now


class PositionsSpider(Spider):
    name = 'market_positions'
    allowed_domains = ['forexfactory.com']

    def __init__(self, params=None, *args, **kwargs):
        super(PositionsSpider, *args, **kwargs)
        if not params:
            raise ValueError('params required: SYMBOL,LIMIT,INTERVAL (e.g., usdjpy,100,H1)')

        parts = [p.strip() for p in params.split(',')]
        if len(parts) != 3:
            raise ValueError('params format: SYMBOL,LIMIT,INTERVAL')

        self.symbol = parts[0].upper()
        self.limit = int(parts[1])
        self.interval = parts[2].upper()

        if self.limit < 1 or self.limit > 500:
            raise ValueError('LIMIT must be between 1 and 500')

    def start_requests(self):
        yield Request(
            f'https://www.forexfactory.com/explorerapi.php'
            f'?content=positions&do=positions_graph_data'
            f'&currency={self.symbol}&interval={self.interval}&limit={self.limit}',
            headers=headers,
            callback=self.parse_positions,
            errback=self.handle_error,
            meta={'impersonate': 'chrome', 'symbol': self.symbol, 'interval': self.interval},
        )

    def parse_positions(self, response):
        if response.status != 200:
            self.logger.warning(f'Positions request failed: {response.status}')
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning('Failed to parse positions JSON')
            return

        for item_data in data.get('positions', []):
            dateline = item_data.get('dateline')
            if not dateline:
                continue

            if dateline > int(now().timestamp()):
                continue

            datetime_str = get_unixtime(str(dateline), divide=1, have_hour=True, timezone='UTC')

            pos = item_data.get('pos', {})
            long_val = pos.get('long', 0)
            short_val = pos.get('short', 0)

            item = PositionItem()
            item['instrument'] = response.meta.get('symbol', '')
            item['interval'] = response.meta.get('interval', '')
            item['datetime'] = datetime_str
            item['long_pct'] = round(long_val, 4)
            item['short_pct'] = round(short_val, 4)
            item['net'] = None
            item['trader_count'] = None
            item['stats'] = None

            yield item

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
