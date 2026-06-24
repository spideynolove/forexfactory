import os

BOT_NAME = 'forexfactory'

SPIDER_MODULES = ['forexfactory.spiders']
NEWSPIDER_MODULE = 'forexfactory.spiders'

ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 1
DOWNLOAD_TIMEOUT = 30
RETRY_TIMES = 5
CONCURRENT_REQUESTS_PER_DOMAIN = 1
URLLENGTH_LIMIT = 50000
TELNETCONSOLE_ENABLED = False

DOWNLOAD_HANDLERS = {
    'http': 'scrapy_impersonate.ImpersonateDownloadHandler',
    'https': 'scrapy_impersonate.ImpersonateDownloadHandler',
}

DOWNLOADER_MIDDLEWARES = {
    'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
    'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
}

ITEM_PIPELINES = {
    'forexfactory.pipelines.MongoPipeline': 300,
}

MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27018')
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'forexfactory')

ROTATING_PROXY_LIST_PATH = os.environ.get('PROXY_LIST_PATH', '')
ROTATING_PROXY_PAGE_RETRY_TIMES = 10
CONCURRENT_REQUESTS_PER_IP = 1

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(levelname)s: %(message)s'

TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
FEED_EXPORT_ENCODING = 'utf-8'
