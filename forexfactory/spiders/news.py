from scrapy import Spider, FormRequest

from forexfactory.items import NewsItem
from forexfactory.utils import headers, get_unixtime, clean_lst
from forexfactory.payloads import NEWS_PAYLOADS, NEWS_CONTENT_TYPE


class NewsSpider(Spider):
    name = 'news'
    allowed_domains = ['forexfactory.com']

    def start_requests(self):
        for news_type, payload in NEWS_PAYLOADS.items():
            yield FormRequest(
                'https://www.forexfactory.com/flex.php',
                method='POST',
                headers={**headers, 'Content-Type': NEWS_CONTENT_TYPE},
                body=payload,
                callback=self.parse,
                errback=self.handle_error,
                meta={'impersonate': 'chrome', 'news_type': news_type},
            )

    def parse(self, response):
        if response.status != 200:
            self.logger.warning(f'News request failed for {response.meta.get("news_type")}: {response.status}')
            return

        news_type = response.meta.get('news_type')
        items = response.xpath('//ul[@class="body flexposts"]/li')

        for item in items:
            timestamp = item.xpath('./@data-timestamp').get()
            if not timestamp:
                continue

            datetime_str = get_unixtime(timestamp, divide=1, have_hour=True, timezone='UTC')

            title = clean_lst(item.xpath('./descendant-or-self::*/text()').getall())
            if not title:
                continue

            news_item = NewsItem()
            news_item['news_type'] = news_type
            news_item['datetime'] = datetime_str
            news_item['title'] = title
            news_item['content'] = None
            news_item['mainterm'] = None
            news_item['instrument'] = None
            news_item['source_url'] = 'https://www.forexfactory.com/news'

            yield news_item

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
