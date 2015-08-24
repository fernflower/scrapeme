from scrapy import exceptions

from scraper import utils


class DuplicatesPipeline(object):
    def __init__(self):
        self.last_ts = None

    def process_item(self, item, spider):
        # if crawler launched for the first time - return any item found
        if not spider.last_ts:
            if not self.last_ts:
                self.last_ts = item['date']
            return item
        # if last_ts exists -> any item older than last_ts is ignored
        if not self.last_ts:
            self.last_ts = spider.last_ts
        if utils.convert_to_datetime(item["date"]) <= self.last_ts:
            raise exceptions.DropItem(
                "Item %s date is older than last crawled" % item)
        return item

    def close_spider(self, spider):
        spider.last_ts = self.last_ts
