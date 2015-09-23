import argparse
import json
import logging
import sys

from scrapy import signals
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


def _find_spiders():
    """Find all classes that subclass scrapy.Spider"""
    res = []
    for module in misc.walk_modules(settings.NEWSPIDER_MODULE):
        # crawl responsibly
        spiders = [s for s in spider.iter_spider_classes(module)]
        # if no spider found -> continue
        if spiders == []:
            continue
        # FIXME not the best way to find a spider, is based on current practice
        # of only one spider in a file and the final may subclass a generated
        # one
        spider_cls = spiders[-1]
        res.append(spider_cls)
    return res


def crawl_all():
    # set up the crawler and start to crawl
    # one spider at a time
    # FIXME find a way to use postscraper.settings
    runner = CrawlerRunner(settings=Settings(
        {'DOWNLOAD_DELAY': settings.DOWNLOAD_DELAY,
         'ITEM_PIPELINES': settings.ITEM_PIPELINES}))

    dispatcher.connect(on_close, signal=signals.spider_closed)
    spider_modules = misc.walk_modules(settings.NEWSPIDER_MODULE)
    for spider_cls in _find_spiders():
        RUNNING_CRAWLERS.append(spider_cls)
        runner.crawl(spider_cls)
    d = runner.join()
    d.addBoth(lambda _: send_mail())

    internet.reactor.run()


def export(stream=sys.stdout):
    json_list = [s.to_dict() for s in _find_spiders()]
    json.dump(json_list, stream, separators=(',', ': '), indent=2)


def main():
    commands_map = {'crawl_all': crawl_all, 'export': export}
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    crawlall_parser = subparsers.add_parser(
        'crawl_all', help='Run all registered spiders')
    import_parser = subparsers.add_parser(
        'import', help='Import spiders from a json file')
    import_parser.add_argument('file',
                               help='A file with spider data in json format')
    export_parser = subparsers.add_parser(
        'export', help="Export all registered spiders' data as json")
    args = parser.parse_args(sys.argv[1:])
    if args.command:
        commands_map[args.command]()


if __name__ == "__main__":
    main()
