import html as htmllib
import re
from datetime import datetime

import pytz
from scrapy import Spider, Request
from parsel import Selector

from forexfactory.items import NewsItem
from forexfactory.utils import headers, get_unixtime, now


NEWS_TYPE_MAP = {
    'News / Latest Stories': 'latest',
    'Fundamental Analysis / Latest Stories': 'latest_fa',
    'Technical Analysis / Latest Stories': 'latest_ta',
}


class NewsSpider(Spider):
    name = 'news'
    allowed_domains = ['forexfactory.com']

    def start_requests(self):
        yield Request(
            'https://www.forexfactory.com/news',
            headers={**headers, 'Accept': 'text/html,application/xhtml+xml,*/*'},
            callback=self.parse,
            errback=self.handle_error,
            meta={'impersonate': 'chrome'},
        )

    def parse(self, response):
        if response.status != 200:
            self.logger.warning(f'News request failed: {response.status}')
            return

        for section_m in re.finditer(
            r'<news-block-component([^>]+)>(.*?)</news-block-component>',
            response.text, re.DOTALL
        ):
            attrs_str = section_m.group(1)
            section_html = section_m.group(2)

            title_m = re.search(r'data-title="([^"]+)"', attrs_str)
            if not title_m:
                continue
            section_title = htmllib.unescape(title_m.group(1))
            news_type = NEWS_TYPE_MAP.get(section_title)
            if news_type is None:
                continue

            ts_m = re.search(r'data-timestamp="(\d+)"', attrs_str)
            ref_ts = int(ts_m.group(1)) if ts_m else int(now().timestamp())

            sel = Selector(text=section_html)
            for item_sel in sel.css('div.news-block__item'):
                title_a = item_sel.css('div.news-block__title a')
                href = title_a.attrib.get('href', '')
                id_m = re.search(r'/news/(\d+)', href)
                if not id_m:
                    continue
                news_id = id_m.group(1)

                title = title_a.css('::text').get('').strip()
                title = re.sub(r'\s+', ' ', title)
                if not title:
                    continue

                time_text = item_sel.css('div.news-block__details span.nowrap::text').get('').strip()
                abs_ts = self._parse_relative_time(time_text, ref_ts)
                datetime_str = get_unixtime(str(abs_ts), divide=1, have_hour=True, timezone='UTC')

                detail_url = f'https://www.forexfactory.com{href}'
                yield Request(
                    detail_url,
                    headers={**headers, 'Accept': 'text/html,application/xhtml+xml,*/*'},
                    callback=self.parse_detail,
                    errback=self.handle_error,
                    dont_filter=True,
                    meta={
                        'impersonate': 'chrome',
                        'news_id': news_id,
                        'news_type': news_type,
                        'datetime': datetime_str,
                        'title': title,
                        'ff_url': detail_url,
                    },
                )

    def parse_detail(self, response):
        m = response.meta
        news_item = NewsItem()
        news_item['news_id'] = m['news_id']
        news_item['news_type'] = m['news_type']
        news_item['datetime'] = m['datetime']
        news_item['title'] = m['title']

        if response.status != 200:
            news_item['content'] = None
            news_item['mainterm'] = None
            news_item['instrument'] = None
            news_item['source_url'] = m['ff_url']
            yield news_item
            return

        sel = response.selector
        main = sel.css('li.news__article:not(.news_article--alloy)')

        copy_parts = main.css('p.news__copy ::text').getall()
        content = re.sub(r'\s+', ' ', ' '.join(t.strip() for t in copy_parts if t.strip())).strip()
        content = re.sub(r'\s*\(\s*full story\s*\)\s*$', '', content, flags=re.I).strip()

        market_href = sel.css('a[href*="/market/"]::attr(href)').get('')
        instrument = market_href.rstrip('/').rsplit('/', 1)[-1].upper() if market_href else None
        mainterm = sel.css('a[href*="/market/"]::text').get('').strip() or None

        ext_url = main.css('p.news__caption a[target="_blank"]::attr(href)').get('')

        news_item['content'] = content or None
        news_item['mainterm'] = mainterm
        news_item['instrument'] = instrument
        news_item['source_url'] = ext_url or m['ff_url']
        yield news_item

    def _parse_relative_time(self, text, ref_ts):
        total_seconds = 0
        hrs = re.search(r'(\d+)\s*hr', text)
        mins = re.search(r'(\d+)\s*min', text)
        if hrs:
            total_seconds += int(hrs.group(1)) * 3600
        if mins:
            total_seconds += int(mins.group(1)) * 60
        if total_seconds:
            return ref_ts - total_seconds
        try:
            d = datetime.strptime(f"{text.strip()} {now().year}", '%b %d %Y')
            return int(d.replace(tzinfo=pytz.UTC).timestamp())
        except ValueError:
            return ref_ts

    def handle_error(self, failure):
        self.logger.warning(f'Request failed: {failure.request.url}')
        return None
