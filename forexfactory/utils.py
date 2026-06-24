import re
import pytz
from datetime import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.forexfactory.com/',
    'Origin': 'https://www.forexfactory.com',
}

SPECIALS = {'nikkei': 'Nikkei225/USD', 'gold': 'Gold/USD'}

now = lambda: datetime.now(tz=pytz.UTC)


def get_num(string: str = None, filter_: str = r"([^0-9.])") -> str:
    return re.sub(filter_, "", str(string).strip()) if string else ""


def get_number(nstr: str = None, rnum: int = 4) -> str:
    nstr = get_num(nstr)
    return str(round(float(nstr), rnum)) if nstr else ''


def get_unix(time_: datetime = None, multiply: int = 1000):
    return str(datetime.timestamp(time_) * multiply).split('.')[0]


def get_unixtime(timestamp: str = None, divide: int = 1000, have_hour: bool = False, timezone: str = 'UTC') -> str:
    if not timestamp:
        return ""
    hour = ' %H:%M' if have_hour else ''
    target_timezone = pytz.timezone(timezone)
    dt = datetime.fromtimestamp(int(timestamp) / divide, target_timezone)
    return dt.strftime(f'%Y-%m-%d{hour}')


def tran_s(sstr: str = None) -> str:
    return f"{sstr[:3]}/{sstr[3:]}".upper()


def flatten(l) -> list:
    return [item for sublist in l for item in sublist]


def gen_perform(symbols: tuple = None, periods: tuple = None):
    symbols = [symbol[:3] + '%2F' + symbol[3:] for symbol in symbols]
    RETS = [list(zip([symbol] * len(period), period))
            for symbol in symbols for period in periods.values()]
    return (','.join(item) for item in flatten(RETS))


def revert_perform(string: str = None) -> str:
    string = string.split(',')
    return string[0].replace('%2F', ''), ''.join(string[1:])


def clean_lst(text_list: list) -> str:
    if not text_list:
        return ''
    cleaned = ' '.join([t.strip() for t in text_list if t.strip()])
    return re.sub(r'\s+', ' ', cleaned)
