from scrapy import Spider, FormRequest
from forexfactory.items import CalendarItem
from forexfactory.utils import headers, get_unixtime, clean_lst, get_num, now
from forexfactory.payloads import calendar_payload, CALENDAR_CONTENT_TYPE


class CalendarSpider(Spider):
    name = 'calendar'
    allowed_domains = ['forexfactory.com']

    def start_requests(self):
        today = now().strftime('%b %d, %Y')
        payload = calendar_payload(today)
        yield FormRequest(
            'https://www.forexfactory.com/flex.php',
            method='POST',
            headers={**headers, 'Content-Type': CALENDAR_CONTENT_TYPE},
            body=payload,
            callback=self.parse,
            errback=self.handle_error,
            meta={'impersonate': 'chrome'},
        )

    def parse(self, response):
        if response.status != 200:
            self.logger.warning(f'Calendar request failed: {response.status}')
            return

        rows = response.xpath('//table[@class="calendar__table  "]/tr[contains(@class, "calendar__row calendar_row")]')
        if not rows:
            self.logger.debug('Empty calendar page')
            return

        for row in rows:
            event_id = row.xpath('./@data-eventid').get()
            if not event_id:
                continue

            timestamp = row.xpath('./@data-timestamp').get()
            if not timestamp:
                self.logger.debug(f'Missing timestamp for event_id {event_id}')
                continue

            datetime_str = get_unixtime(timestamp, divide=1000, have_hour=True, timezone='UTC')

            currency = clean_lst(row.xpath('./td[contains(@class, "__currency")]//text()').getall())
            if not currency:
                self.logger.debug(f'Missing currency for event_id {event_id}')
                continue

            impact_raw = row.xpath('./td[contains(@class, "__impact")]/span/@title').get()
            impact = impact_raw.replace(' Impact Expected', '') if impact_raw else ''

            title = clean_lst(row.xpath('./td[contains(@class, "__event")]//text()').getall())
            if not title:
                self.logger.debug(f'Missing title for event_id {event_id}')
                continue

            actual = get_num(clean_lst(row.xpath('./td[contains(@class, "__actual")]//text()').getall()))
            forecast = get_num(clean_lst(row.xpath('./td[contains(@class, "__forecast")]//text()').getall()))
            previous = get_num(clean_lst(row.xpath('./td[contains(@class, "__previous")]//text()').getall()))

            item = CalendarItem()
            item['event_id'] = event_id
            item['datetime'] = datetime_str
            item['currency'] = currency
            item['impact'] = impact if impact else None
            item['event_type'] = None
            item['title'] = title
            item['actual'] = actual if actual else None
            item['forecast'] = forecast if forecast else None
            item['previous'] = previous if previous else None
            item['source_url'] = response.url

            yield item

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
