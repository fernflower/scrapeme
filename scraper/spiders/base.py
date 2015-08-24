from datetime import datetime
import os
import urlparse

import scrapy

from scraper import exc
import scraper.items
from scraper import settings
from scraper import utils


def _fetch_body(self, response):
    item = scraper.items.PostItem()
    for meta_key in ['title', 'link', 'date']:
        item[meta_key] = response.meta[meta_key]
    item['text'] = "\n".join(self.select(response, 'text').extract())
    yield item


def _select(self, obj, var_name):
    """Applies either css or xpath selector to 'obj'

    The final choice depends on the class variable.
    Var_name can be 'post','title', 'date' or 'link'.
    """
    schemas = {'_css': obj.css, '_xpath': obj.xpath}
    for schema, func in schemas.items():
        var = var_name + schema
        if hasattr(self, var):
            return func(getattr(self, var))
    raise exc.SpiderException("No such variable: %s" % var)


def _get_last_ts(self):
    """Returns a datetime object"""
    if os.path.exists(self.last_seen_filename):
        with open(self.last_seen_filename) as f:
            try:
                return utils.convert_to_datetime(f.read())
            except ValueError:
                return None
    return None


def _set_last_ts(self, date):
    date_str = (utils.convert_date_to_str(date)
                if isinstance(date, datetime) else date)
    with open(self.last_seen_filename, 'wb') as f:
        f.write(date_str)


def _parse(self, response):
    for sel in self.select(response, 'post'):
        title = self.select(sel, 'title')[0].extract().strip()
        rel_link = self.select(sel, 'link')[0].extract().strip()
        link = urlparse.urljoin(response.url, rel_link)
        date = self.process_date(sel)
        yield scrapy.Request(link, callback=self.fetch_body,
                             meta={'title': title, 'link': link, 'date': date})


def _process_date(self, sel):
    return self.select(sel, 'date')[0].extract().strip()


def gen_spider_class(**kwargs):
    """Generates a spider class with given name/allowed_domains/start_urls

    The class will have a default parse method.
    Besides a directory for spider data will be created.
    """
    cls_attrs = {'parse': _parse, 'fetch_body': _fetch_body,
                 'select': _select, 'process_date': _process_date,
                 'last_ts': property(fget=_get_last_ts, fset=_set_last_ts),
                 'last_seen_filename': os.path.join(
                     settings.SCRAPED_DIR, kwargs['name'],
                     settings.LAST_SEEN_FILENAME)}
    try:
        for req_arg in ["name", "allowed_domains", "start_urls"]:
            val = kwargs.pop(req_arg)
            cls_attrs[req_arg] = val
    except KeyError:
        raise exc.SpiderException(
            "%s attribute is required for spider creation" % req_arg)
    # create directory to store spider date
    dirname = os.path.join(settings.SCRAPED_DIR, cls_attrs['name'])
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    return type(cls_attrs['name'] + "Class", (scrapy.Spider, ), cls_attrs)
