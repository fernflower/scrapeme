import datetime
from jinja2 import Environment, FileSystemLoader
import pysolr
from scrapy import exceptions
from scraper import mymailsender
from scrapy.settings import Settings

from scraper import settings
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


class SolrInjectPipeline(object):
    def __init__(self):
        self.new_items = []

    def process_item(self, item, spider):
        self.new_items.append(item)
        return item

    def close_spider(self, spider):
        if len(self.new_items) == 0:
            return
        solr = pysolr.Solr(settings.SOLR_URL, timeout=settings.SOLR_TIMEOUT)
        for item in self.new_items:
            str_date = item['date']
            item['date'] = datetime.datetime.strptime(str_date,
                                                      settings.DATE_FORMAT)
        solr.add(self.new_items)


class SendMailPipeline(object):

    def __init__(self):
        self.new_items = []

    def process_item(self, item, spider):
        self.new_items.append(item)
        return item

    def close_spider(self, spider):
        """Sends an email with new items if any"""
        if len(self.new_items) == 0:
            return
        # show only new items that match the QUERY
        solr = pysolr.Solr(settings.SOLR_URL, timeout=settings.SOLR_TIMEOUT)

        # FIXME does Solr have a native way to do this?
        def escape(link):
            res = link
            for c in ['/', ':', '?', '&']:
                res = res.replace(c, '\\'+c)
            return res

        if spider.last_ts is None:
            query = settings.QUERY
        else:
            # query filtered by new_items links (link is a uid now)
            query = (u"%(query)s AND date:([%(date)s TO NOW])" %
                     {'query': settings.QUERY,
                      'date': utils.convert_date_to_solr_date(spider.last_ts)})
        items = solr.search(query, sort="date desc")
        # convert dates to human-readable non-solr format
        for item in items:
            # FIXME move to utils
            dt = datetime.datetime.strptime(item['date'],
                                            settings.SOLR_DATE_FORMAT)
            item['date'] = dt.strftime(settings.DATE_FORMAT)
        mailer = mymailsender.MailSender.from_settings(Settings(
            settings.MAILER_SETTINGS))
        env = Environment(loader=FileSystemLoader(settings.TEMPLATES_DIR))
        template = env.get_template('mail_items.html')
        body = template.render(items=items, query=settings.QUERY)
        date = ("the very beginning" if not spider.last_ts
                else utils.convert_date_to_str(spider.last_ts))
        mailer.send(to=settings.MAIL_RECIPIENT_LIST,
                    subject=(
                        "%(count)s new items from %(link)s since %(date)s" %
                        {'count': len(items),
                         'link': spider.name,
                         'date': date}),
                    body=body, mimetype="text/html; charset=utf-8")
