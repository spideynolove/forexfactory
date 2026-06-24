import os
import pymongo
from scrapy.exceptions import DropItem


class MongoPipeline:
    def __init__(self, uri, database):
        self.uri = uri
        self.database = database
        self.client = None
        self.db = None
        self._indexed = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            uri=crawler.settings.get('MONGODB_URI') or os.getenv('MONGODB_URI', 'mongodb://localhost:27017'),
            database=crawler.settings.get('MONGODB_DATABASE') or os.getenv('MONGODB_DATABASE', 'forexfactory'),
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.uri)
        self.db = self.client[self.database]

    def close_spider(self, spider):
        if self.client is not None:
            self.client.close()

    def process_item(self, item, spider):
        document = dict(item)
        collection = getattr(item.__class__, 'collection', spider.name)
        unique_key = getattr(item.__class__, 'unique_key', None)

        if unique_key:
            missing = [k for k in unique_key if not document.get(k)]
            if missing:
                raise DropItem(f"Missing unique_key fields {missing} in {collection}")
            if collection not in self._indexed:
                self.db[collection].create_index([(k, 1) for k in unique_key], unique=True)
                self._indexed.add(collection)
            filter_doc = {k: document[k] for k in unique_key}
            self.db[collection].replace_one(filter_doc, document, upsert=True)
        else:
            self.db[collection].insert_one(document)
        return item
