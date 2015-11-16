from scrapy import crawler as scrapy_crawler
from twisted import internet

from postscraper import settings


START_CHAIN = 2


class CrawlerRunner(scrapy_crawler.CrawlerRunner):
    last_map = {}

    def crawl(self, crawler_or_spidercls, *args, **kwargs):
        """
        Differs from scrapy.CrawlerRunner in a way how crawl jobs
        of the same type are added.
        If more than START_CHAIN spiders of the kind appear in _active set,
        then other spiders of this very type will be added as a deferred chain.
        """
        crawler = crawler_or_spidercls
        if not isinstance(crawler_or_spidercls, scrapy_crawler.Crawler):
            crawler = self._create_crawler(crawler_or_spidercls)

        self.crawlers.add(crawler)

        spider_type = crawler_or_spidercls.type
        types = len(self.last_map.get(spider_type, []))
        if types > 0:
            d = internet.task.deferLater(internet.reactor,
                                         settings.DOWNLOAD_DELAY * types,
                                         crawler.crawl, *args, **kwargs)
            self.last_map[spider_type].append(d)
        else:
            d = crawler.crawl(*args, **kwargs)
            self.last_map[spider_type] = [d]
        self._active.add(d)

        def _done(result):
            self.crawlers.discard(crawler)
            self._active.discard(d)
            return result

        return d.addBoth(_done)
