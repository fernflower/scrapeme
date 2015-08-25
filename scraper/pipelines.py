from scrapy import exceptions

from scraper import utils


class DuplicatesPipeline(object):
    def __init__(self):
        # datetime object
        self.last_ts = None

    def process_item(self, item, spider):
        # if crawler launched for the first time - return any item found
        if not spider.last_ts:
            self.last_ts = utils.convert_to_datetime(item['date'])
            return item
        if not self.last_ts:
            self.last_ts = spider.last_ts
        # if last_ts exists -> any item older than last_ts is ignored
        if utils.convert_to_datetime(item["date"]) <= spider.last_ts:
            raise exceptions.DropItem(
                "Item %s date is older than last crawled" % item)
        # in case posts can be updated -> check that last ts is maximum
        item_date = utils.convert_to_datetime(item['date'])
        if (self.last_ts < item_date):
            self.last_ts = item_date
        return item

    def close_spider(self, spider):
        spider.last_ts = self.last_ts
