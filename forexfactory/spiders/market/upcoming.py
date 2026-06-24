import json
import re
from datetime import timedelta

from scrapy import Spider, Request

from forexfactory.items import UpcomingItem
from forexfactory.utils import headers, get_unixtime, now


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

        sym = self.symbol.lower()
        self._currencies = {sym[:3], sym[3:]} if len(sym) == 6 else {sym}
        self._ts_now = int(now().timestamp())
        self._count = 0

    def start_requests(self):
        yield self._day_request(0)

    def _day_request(self, offset):
        dt = now() + timedelta(days=offset)
        day_url = f"{dt.strftime('%b').lower()}{dt.day}.{dt.year}"
        return Request(
            f'https://www.forexfactory.com/calendar?day={day_url}',
            headers={**headers, 'Accept': 'text/html,application/xhtml+xml,*/*'},
            callback=self.parse_day,
            errback=self.handle_error,
            meta={'impersonate': 'chrome', 'offset': offset},
        )

    def parse_day(self, response):
        if response.status != 200:
            self.logger.warning(f'Calendar request failed: {response.status}')
            return

        days = self._extract_days(response.text)
        if days is not None:
            for day in days:
                for event in day.get('events', []):
                    if self._count >= self.limit:
                        return
                    item = self._make_item(event, response.url)
                    if item:
                        self._count += 1
                        yield item

        offset = response.meta.get('offset', 0)
        if self._count < self.limit and offset < 29:
            yield self._day_request(offset + 1)

    def _extract_days(self, html):
        for s in re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL):
            if 'calendarComponentStates' not in s:
                continue
            idx = s.find('days: [')
            if idx == -1:
                continue
            start = idx + len('days: ')
            depth, end = 0, start
            for i, ch in enumerate(s[start:]):
                if ch == '[':
                    depth += 1
                elif ch == ']':
                    depth -= 1
                    if depth == 0:
                        end = start + i + 1
                        break
            try:
                return json.loads(s[start:end].replace('\\/', '/'))
            except (json.JSONDecodeError, ValueError):
                return None
        return None

    def _make_item(self, event, source_url):
        event_id = str(event.get('id', ''))
        dateline = event.get('dateline')
        currency = (event.get('currency') or '').lower()
        title = event.get('name', '')

        if not event_id or not dateline or not currency or not title:
            return None
        if dateline < self._ts_now:
            return None
        if currency not in self._currencies:
            return None

        impact = event.get('impactName') or None
        if impact and impact.lower() == 'low':
            return None

        item = UpcomingItem()
        item['instrument'] = self.symbol
        item['event_id'] = event_id
        item['datetime'] = get_unixtime(str(dateline), divide=1, have_hour=True, timezone='UTC')
        item['impact'] = impact
        item['currency'] = currency.upper()
        item['title'] = title
        item['source_url'] = source_url
        return item

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
