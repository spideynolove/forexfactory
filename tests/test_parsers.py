import pytest
import pytz
from datetime import datetime
from unittest.mock import patch
from scrapy.http import HtmlResponse, TextResponse, Request

from forexfactory.spiders.calendar import CalendarSpider
from forexfactory.spiders.calendar_history import CalendarHistorySpider
from forexfactory.spiders.news import NewsSpider
from forexfactory.spiders.market.instruments import InstrumentsSpider
from forexfactory.spiders.market.bars import BarsSpider
from forexfactory.spiders.market.positions import PositionsSpider
from forexfactory.spiders.market.upcoming import UpcomingSpider
from forexfactory.spiders.market.indicators_news import IndicatorsNewsSpider
from forexfactory.items import (
    CalendarItem, NewsItem, InstrumentItem, BarItem,
    PositionItem, UpcomingItem, IndicatorNewsItem,
)


FIXTURES = 'tests/fixtures'


def _read(name):
    with open(f'{FIXTURES}/{name}', 'rb') as f:
        return f.read()


def test_calendar_parse():
    spider = CalendarSpider()
    response = HtmlResponse(url='http://test', body=_read('calendar_row.html'))
    fixed_now = datetime(2024, 7, 1, tzinfo=pytz.UTC)
    with patch('forexfactory.spiders.calendar.now', return_value=fixed_now):
        items = list(spider.parse(response))
    assert len(items) == 1
    assert isinstance(items[0], CalendarItem)
    assert items[0]['event_id'] == '12345'
    assert items[0]['datetime'] == '2024-07-01 00:00'
    assert items[0]['currency'] == 'USD'
    assert items[0]['impact'] == 'High'
    assert items[0]['title'] == 'Non-Farm Employment Change'
    assert items[0]['actual'] == '272'
    assert items[0]['forecast'] == '200'
    assert items[0]['previous'] == '165'
    assert items[0]['source_url'] == 'http://test'


def test_calendar_parse_missing_event_id():
    spider = CalendarSpider()
    html = '''
    <table class="calendar__table  ">
      <tr class="calendar__row calendar_row" data-timestamp="1719792000000">
        <td class="calendar__cell __currency">USD</td>
        <td class="calendar__cell __event">Test Event</td>
      </tr>
    </table>
    '''
    response = HtmlResponse(url='http://test', body=html.encode())
    items = list(spider.parse(response))
    assert len(items) == 0


def test_calendar_parse_missing_timestamp():
    spider = CalendarSpider()
    html = '''
    <table class="calendar__table  ">
      <tr class="calendar__row calendar_row" data-eventid="12345">
        <td class="calendar__cell __currency">USD</td>
        <td class="calendar__cell __event">Test Event</td>
      </tr>
    </table>
    '''
    response = HtmlResponse(url='http://test', body=html.encode())
    items = list(spider.parse(response))
    assert len(items) == 0


def test_calendar_history_requires_params():
    with pytest.raises(ValueError):
        CalendarHistorySpider()


def test_calendar_history_bad_order():
    with pytest.raises(ValueError):
        CalendarHistorySpider(params='2024-01-02,2024-01-01')


def test_calendar_history_valid_params():
    spider = CalendarHistorySpider(params='2024-01-01,2024-01-02')
    assert spider.start_date <= spider.end_date


def test_news_parse():
    spider = NewsSpider()
    request = Request(url='http://test', meta={'news_type': 'latest'})
    response = HtmlResponse(url='http://test', body=_read('news.html'), request=request)
    items = list(spider.parse(response))
    assert len(items) == 2
    assert isinstance(items[0], NewsItem)
    assert items[0]['news_type'] == 'latest'
    assert items[0]['datetime'] == '2024-07-01 00:00'
    assert items[0]['title'] == 'Fed Chair Powell speaks at economic conference'
    assert items[0]['source_url'] == 'https://www.forexfactory.com/news/11111-fed-chair-powell'


def test_instruments_parse():
    spider = InstrumentsSpider(params='eurusd,gbpjpy')
    response = TextResponse(url='http://test', body=_read('instruments.json'))
    items = list(spider.parse(response))
    assert len(items) == 2
    assert isinstance(items[0], InstrumentItem)
    assert items[0]['instrument'] == 'eurusd'
    assert items[0]['metrics']['pip'] == 0.0001
    assert items[0]['fetched_at'].startswith('20')


def test_bars_parse():
    spider = BarsSpider(params='eurusd,100,H1')
    request = Request(url='http://test', meta={'symbol': 'EURUSD', 'interval': 'H1'})
    response = TextResponse(url='http://test', body=_read('bars.json'), request=request)
    items = list(spider.parse(response))
    assert len(items) == 2
    assert isinstance(items[0], BarItem)
    assert items[0]['instrument'] == 'EURUSD'
    assert items[0]['interval'] == 'H1'
    assert items[0]['datetime'] == '2024-07-01 00:00'
    assert items[0]['open_'] == '1.0845'
    assert items[0]['close_'] == '1.0855'
    assert items[0]['volume_'] == '15000'


def test_positions_parse():
    spider = PositionsSpider(params='usdjpy,100,H1')
    stats_request = Request(url='http://test', meta={'symbol': 'USDJPY', 'interval': 'H1', 'limit': 100})
    ratio_response = TextResponse(url='http://test', body=_read('positions_ratio.json'), request=stats_request)
    items = list(spider.parse_positions(ratio_response))
    assert len(items) == 2
    assert isinstance(items[0], PositionItem)
    assert items[0]['instrument'] == 'USDJPY'
    assert items[0]['interval'] == 'H1'
    assert items[0]['datetime'] == '2024-07-01 00:00'
    assert items[0]['long_pct'] == 55.2
    assert items[0]['short_pct'] == 44.8


def test_upcoming_parse():
    spider = UpcomingSpider(params='eurusd,20')
    request = Request(url='http://test', meta={'symbol': 'EURUSD'})
    response = TextResponse(url='http://test', body=_read('upcoming.json'), request=request)
    items = list(spider.parse(response))
    assert len(items) == 1
    assert isinstance(items[0], UpcomingItem)
    assert items[0]['instrument'] == 'EURUSD'
    assert items[0]['event_id'] == '123'
    assert items[0]['datetime'] == '2024-07-01 00:00'
    assert items[0]['impact'] == 'High'
    assert items[0]['currency'] == 'USD'
    assert items[0]['title'] == 'NFP'


def test_indicators_news_parse():
    spider = IndicatorsNewsSpider(params='eurusd,H1')
    request = Request(url='http://test', meta={'symbol': 'EURUSD', 'interval': 'H1'})
    response = TextResponse(url='http://test', body=_read('indicators_news.json'), request=request)
    items = list(spider.parse(response))
    assert len(items) == 1
    assert isinstance(items[0], IndicatorNewsItem)
    assert items[0]['instrument'] == 'EURUSD'
    assert items[0]['interval'] == 'H1'
    assert items[0]['datetime'] == '2024-07-01 00:00'
    assert items[0]['impact'] == 'High'
    assert items[0]['title'] == 'Strong support level'
