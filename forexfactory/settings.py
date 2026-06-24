BOT_NAME = 'forexfactory'

SPIDER_MODULES = ['forexfactory.spiders']
NEWSPIDER_MODULE = 'forexfactory.spiders'

ROBOTSTXT_OBEY = False

DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
URLLENGTH_LIMIT = 50000
TELNETCONSOLE_ENABLED = False

DOWNLOAD_HANDLERS = {
    'http': 'scrapy_impersonate.ImpersonateDownloadHandler',
    'https': 'scrapy_impersonate.ImpersonateDownloadHandler',
}

ITEM_PIPELINES = {
    'forexfactory.pipelines.MongoPipeline': 300,
}

MONGODB_URI = 'mongodb://localhost:27017'
MONGODB_DATABASE = 'forexfactory'

LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(levelname)s: %(message)s'

TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
FEED_EXPORT_ENCODING = 'utf-8'
