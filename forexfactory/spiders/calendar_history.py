import json
from datetime import datetime, timedelta

import pytz
from scrapy import Spider, Request, FormRequest

from forexfactory.items import CalendarItem
from forexfactory.utils import headers
from forexfactory.payloads import calendar_payload, CALENDAR_CONTENT_TYPE


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
            date_str = self.current_date.strftime('%b %d, %Y')
            payload = calendar_payload(date_str)
            self.current_date += timedelta(days=1)
            yield FormRequest(
                'https://www.forexfactory.com/flex.php',
                method='POST',
                headers={**headers, 'Content-Type': CALENDAR_CONTENT_TYPE},
                body=payload,
                callback=self.parse_calendar,
                errback=self.handle_error,
                meta={'impersonate': 'chrome'},
            )

    def parse_calendar(self, response):
        if response.status != 200:
            self.logger.warning(f'Calendar request failed: {response.status}')
            return

        rows = response.xpath('//table[@class="calendar__table  "]/tr[contains(@class, "calendar__row calendar_row")]')
        if not rows:
            self.logger.debug(f'Empty calendar page for {response.url}')
            return

        for row in rows:
            event_id = row.xpath('./@data-eventid').get()
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
            item['datetime'] = event.get('date', '')
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

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
