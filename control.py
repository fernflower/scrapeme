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

from postscraper import exc
from postscraper import mymailsender
from postscraper import utils
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
        # if two spiders with the same name are found, then take the one that
        # subclasses the autogenerated
        spider_map = {}
        for s in spiders:
            if s.name in spider_map:
                # leave only the one that subclasses parent
                old = spider_map[s.name]
                if old in s.mro():
                    spider_map[s.name] = s
            else:
                spider_map[s.name] = s
        for s in spider_map.values():
            res.append(s)
    return res


def crawl_all(token=None):
    if not token:
        LOG.warn("No token passed, "
                "acquiring one using login data from settings")
        token = utils.get_access_token()
    LOG.info("Access token: %s" % token)
    runner = CrawlerRunner(settings=Settings(
        {'DOWNLOAD_DELAY': settings.DOWNLOAD_DELAY,
         'ITEM_PIPELINES': settings.ITEM_PIPELINES}))

    dispatcher.connect(on_close, signal=signals.spider_closed)
    for spider_cls in _find_spiders():
        # FIXME incapsulation vialation
        # inject access_token to a VK spider
        spider_cls.access_token = token
        RUNNING_CRAWLERS.append(spider_cls)
        runner.crawl(spider_cls)
    d = runner.join()
    d.addBoth(lambda _: send_mail())

    internet.reactor.run()


def export(stream=sys.stdout):
    json_list = [s.to_dict() for s in _find_spiders() if s.type == "vk"]
    json.dump(json_list, stream, separators=(',', ': '), indent=2)


def import_spiders(filename):
    with open(filename) as f:
        data = json.load(f)
    with open(settings.AUTOGENERATED_SPIDER_MODULE.replace('.', '/') + '.py',
              'w') as f:
        f.write('from postscraper.spiders import base\n\n')
        for i, spider_data in enumerate(data):
            # FIXME introduce factory method here
            if spider_data.pop('type') != 'vk':
                raise exc.SpiderException("Only VK spider can be autogenerated")

            def _dict_to_kwargs_str(spider_data):
                # FIXME bloody hell, there must be some other way to generate a
                # module!!!
                spider_data['module'] = settings.AUTOGENERATED_SPIDER_MODULE
                return (", ".join(
                    ["%s=%s" % (key,
                                value if not isinstance(value, basestring)
                                else '"' + value + '"')
                     for key, value in spider_data.items()]))

            f.write(('spider_%d = base.create_vk_spider(' +
                     _dict_to_kwargs_str(spider_data) + ')\n\n') % i)


def main():
    commands_map = {'crawl_all': (crawl_all, 'token'), 'export': (export, ),
                    'import': (import_spiders, 'file')}
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    crawlall_parser = subparsers.add_parser(
        'crawl_all', help='Run all registered spiders')

    crawlall_parser.add_argument('--token',
                                 help='Access token for private VK info')
    import_parser = subparsers.add_parser(
        'import', help='Import spiders from a json file')
    import_parser.add_argument('file',
                               help='A file with spider data in json format')
    export_parser = subparsers.add_parser(
        'export', help="Export all registered spiders' data as json")
    args = parser.parse_args()
    if args.command:
        func_data = commands_map[args.command]
        if len(func_data) == 1:
            func_data[0]()
        else:
            func_data[0](*[getattr(args, v) for v in func_data[1:]])


if __name__ == "__main__":
    main()
