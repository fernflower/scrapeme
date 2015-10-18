import datetime

from jinja2 import Environment, FileSystemLoader
import pysolr
from scrapy import exceptions

from postscraper import settings
from postscraper import utils


class SolrInjectPipeline(object):
    def __init__(self):
        self.solr = pysolr.Solr(settings.SOLR_URL,
                                timeout=settings.SOLR_TIMEOUT)
        self.items = []

    def process_item(self, item, spider):
        self.items.append(item)
        return item

    def close_spider(self, spider):
        # inject new items into Solr
        for item in self.items:
            str_date = item['date']
            item['date'] = datetime.datetime.strptime(str_date,
                                                      settings.DATE_FORMAT)
        self.solr.add(self.items)


class RemoveDuplicatesPipeline(object):
    def __init__(self):
        # datetime object to update last crawl in
        self.last_ts = None

    def process_item(self, item, spider):
        # inject source name
        item['source'] = spider.name
        item_date = utils.convert_to_datetime(item['date'])
        # if crawler launched for the first time - get first item's date as
        # last_ts; else take last launch time as starting point
        if not self.last_ts:
            self.last_ts = (item_date if not spider.last_ts else spider.last_ts)
        # first launch -> save all items found
        if not spider.last_ts:
            return item
        # if last_ts exists -> any item older than last crawl time is ignored
        if item_date <= spider.last_ts:
            raise exceptions.DropItem(
                "Item %s date is older than last crawled" % item)
        # in case posts can be updated -> check that last ts is maximum
        if (self.last_ts < item_date):
            self.last_ts = item_date
        return item

    def close_spider(self, spider):
        # update last crawl time
        spider.last_ts = self.last_ts


class SendMailPipeline(object):
    def __init__(self):
        self.solr = pysolr.Solr(settings.SOLR_URL,
                                timeout=settings.SOLR_TIMEOUT)

    def _filter_by_query(self, spider):
        """Return those items from recently fetched that match the QUERY.

        Make sure that items have been uploaded to Solr but last crawl time
        not updated before calling this func
        """
        # FIXME does Solr have a native way to do this?
        def escape(link):
            res = link
            for c in ['/', ':', '?', '&']:
                res = res.replace(c, '\\'+c)
            return res
        # increment date by 1 second to hide last seen result
        # FIXME how can we do it with a solr query?
        last_to_show = (datetime.datetime.now() -
                        datetime.timedelta(days=settings.POSTS_TTL))
        if not spider.last_ts:
            spider.last_ts = last_to_show
        inc_date = max(spider.last_ts + datetime.timedelta(0, 1), last_to_show)
        query = ((u"%(query)s AND date:([%(date)s TO NOW]) "
                    "AND source: %(source)s") %
                    {'query': settings.QUERY,
                    'date': utils.convert_date_to_solr_date(inc_date),
                    'source': spider.name})
        items = self.solr.search(query, sort="date desc",
                                 rows=settings.QUERY_ROWS)
        # convert dates to human-readable non-solr format
        for item in items:
            # FIXME move to utils
            dt = datetime.datetime.strptime(item['date'],
                                            settings.SOLR_DATE_FORMAT)
            item['date'] = dt.strftime(settings.DATE_FORMAT)
        return items

    def close_spider(self, spider):
        """Sends an email with new items if any"""
        items = self._filter_by_query(spider)
        # don't generate an email with 0 results
        if len(items) == 0:
            spider.email = None
            return
        env = Environment(loader=FileSystemLoader(settings.TEMPLATES_DIR))
        template = env.get_template('mail_items.html')
        body = template.render(items=items, query=settings.QUERY)
        # save email body in a file
        date = ("the very beginning" if not spider.last_ts
                else utils.convert_date_to_str(spider.last_ts))
        text = ("<h1>"
                "%(count)s new items from %(link)s since %(date)s</h1>\n"
                "%(body)s"
                % {'count': len(items), 'link': spider.name,
                    'date': date, 'body': body})
        spider.email = text
