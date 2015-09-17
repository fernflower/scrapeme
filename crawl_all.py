from importlib import import_module
import logging
import subprocess

from scrapy import crawler, signals
from scrapy.crawler import CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils import misc, spider
from scrapy.xlib.pydispatch import dispatcher
from scrapy.utils.log import configure_logging
from twisted import internet

from postscraper import mymailsender
from postscraper import settings


configure_logging()
LOG = logging.getLogger(__name__)
# crawlers that are running
RUNNING_CRAWLERS = []
FINISHED_CRAWLERS = []


def send_mail():
    body = "\n".join([s.email for s in FINISHED_CRAWLERS if s.email])
    if body:
        mailer = mymailsender.MailSender.from_settings(
            Settings(settings.MAILER_SETTINGS))
        mailer.send(to=settings.MAIL_RECIPIENT_LIST,
                    subject="New items from scraper",
                    body=body,
                    mimetype="text/html; charset=utf-8")
    internet.reactor.stop()


def on_close(spider):
    """
    Activates on spider closed signal
    """
    # for debug purposes
    RUNNING_CRAWLERS.remove(type(spider))
    FINISHED_CRAWLERS.append(spider)
    LOG.info("Spider closed: %s" % spider)


def main():
    # set up the crawler and start to crawl
    # one spider at a time
    # FIXME find a way to use postscraper.settings
    runner = CrawlerRunner(settings=Settings(
        {'DOWNLOAD_DELAY': settings.DOWNLOAD_DELAY,
         'ITEM_PIPELINES': settings.ITEM_PIPELINES}))

    dispatcher.connect(on_close, signal=signals.spider_closed)
    for module in misc.walk_modules(settings.NEWSPIDER_MODULE):
        # crawl responsibly
        spiders = [s for s in spider.iter_spider_classes(module)]
        # if no spider found -> continue
        if spiders == []:
            continue
        spider_cls = spiders[0]
        RUNNING_CRAWLERS.append(spider_cls)
        runner.crawl(spider_cls)
    d = runner.join()
    d.addBoth(lambda _: send_mail())

    internet.reactor.run()


if __name__ == "__main__":
    main()
