import json
import re

from scrapy import Spider, Request

from forexfactory.items import CalendarItem
from forexfactory.utils import headers, get_unixtime, get_num, now


class CalendarSpider(Spider):
    name = 'calendar'
    allowed_domains = ['forexfactory.com']

    def start_requests(self):
        dt = now()
        day_url = f"{dt.strftime('%b').lower()}{dt.day}.{dt.year}"
        yield Request(
            f'https://www.forexfactory.com/calendar?day={day_url}',
            headers={**headers, 'Accept': 'text/html,application/xhtml+xml,*/*'},
            callback=self.parse,
            errback=self.handle_error,
            meta={'impersonate': 'chrome'},
        )

    def parse(self, response):
        if response.status != 200:
            self.logger.warning(f'Calendar request failed: {response.status}')
            return

        days = self._extract_days(response.text)
        if days is None:
            self.logger.warning('calendarComponentStates not found in page')
            return

        dt = now()
        today_label = f"{dt.strftime('%b')} {dt.day}"

        for day in days:
            date_text = re.sub(r'<[^>]+>', '', day.get('date', ''))
            if today_label not in date_text:
                continue
            for event in day.get('events', []):
                item = self._make_item(event, response.url)
                if item:
                    yield item

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
        currency = event.get('currency', '')
        title = event.get('name', '')
        if not event_id or not dateline or not currency or not title:
            return None
        item = CalendarItem()
        item['event_id'] = event_id
        item['datetime'] = get_unixtime(str(dateline), divide=1, have_hour=True, timezone='UTC')
        item['currency'] = currency
        item['impact'] = event.get('impactName') or None
        item['event_type'] = None
        item['title'] = title
        item['actual'] = get_num(event.get('actual', '')) or None
        item['forecast'] = get_num(event.get('forecast', '')) or None
        item['previous'] = get_num(event.get('previous', '')) or None
        item['source_url'] = source_url
        return item

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
