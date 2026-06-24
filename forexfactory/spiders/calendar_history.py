import json
import re
from datetime import datetime, timedelta

import pytz
from scrapy import Spider, Request

from forexfactory.items import CalendarItem
from forexfactory.utils import headers


class CalendarHistorySpider(Spider):
    name = 'calendar_history'
    allowed_domains = ['forexfactory.com']

    def __init__(self, params=None, *args, **kwargs):
        super(CalendarHistorySpider, *args, **kwargs)
        if not params:
            raise ValueError('params required: START,END as YYYY-MM-DD,YYYY-MM-DD')

        try:
            start_str, end_str = params.split(',')
            self.start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d').replace(tzinfo=pytz.UTC)
            self.end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d').replace(tzinfo=pytz.UTC)
        except ValueError as e:
            raise ValueError(f'Invalid params format: {e}. Expected: START,END as YYYY-MM-DD,YYYY-MM-DD')

        if self.start_date > self.end_date:
            raise ValueError('START date must be before or equal to END date')

        if (self.end_date - self.start_date).days > 365:
            raise ValueError('Date range cannot exceed 365 days')

        self.current_date = self.start_date

    def start_requests(self):
        while self.current_date <= self.end_date:
            dt = self.current_date
            day_url = f"{dt.strftime('%b').lower()}{dt.day}.{dt.year}"
            self.current_date += timedelta(days=1)
            yield Request(
                f'https://www.forexfactory.com/calendar?day={day_url}',
                headers={**headers, 'Accept': 'text/html,application/xhtml+xml,*/*'},
                callback=self.parse_calendar,
                errback=self.handle_error,
                meta={'impersonate': 'chrome', 'day_url': day_url},
            )

    def parse_calendar(self, response):
        if response.status != 200:
            self.logger.warning(f'Calendar request failed: {response.status}')
            return

        days = self._extract_days(response.text)
        if days is None:
            self.logger.debug(f'calendarComponentStates not found for {response.meta.get("day_url")}')
            return

        day_label = self._day_url_to_label(response.meta.get('day_url', ''))

        for day in days:
            date_text = re.sub(r'<[^>]+>', '', day.get('date', ''))
            if day_label and day_label not in date_text:
                continue
            for event in day.get('events', []):
                event_id = str(event.get('id', ''))
                if not event_id:
                    continue
                yield Request(
                    f'https://www.forexfactory.com/calendar/events?event_id={event_id}&limit=200',
                    headers=headers,
                    callback=self.parse_events,
                    errback=self.handle_error,
                    meta={'impersonate': 'chrome', 'event_id': event_id, 'calendar_url': response.url},
                )

    def parse_events(self, response):
        if response.status != 200:
            self.logger.warning(f'Events request failed: {response.status}')
            return

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.warning(f'Failed to parse events JSON for {response.url}')
            return

        events = data.get('data', {}).get('events', [])
        if not events:
            self.logger.debug(f'No events data for event_id {response.meta.get("event_id")}')
            return

        for event in events:
            item = CalendarItem()
            item['event_id'] = response.meta.get('event_id')
            raw_date = event.get('date', '')
            item['datetime'] = raw_date + ' 00:00' if raw_date and len(raw_date) == 10 else raw_date
            item['currency'] = event.get('currency', '')
            item['impact'] = event.get('impact_name')
            item['event_type'] = event.get('category')
            item['title'] = event.get('name', '')
            item['actual'] = event.get('actual')
            item['forecast'] = event.get('forecast')
            item['previous'] = event.get('previous')
            item['source_url'] = response.meta.get('calendar_url', response.url)

            if not item['event_id'] or not item['datetime'] or not item['currency'] or not item['title']:
                self.logger.debug(f'Missing required fields in event: {event}')
                continue

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

    def _day_url_to_label(self, day_url):
        m = re.match(r'([a-z]+)(\d+)\.', day_url)
        if not m:
            return ''
        return f"{m.group(1).capitalize()} {int(m.group(2))}"

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
