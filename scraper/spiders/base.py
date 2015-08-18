import os
import urlparse

import scrapy

from scraper import exc
import scraper.items
from scraper import settings


def _fetch_body(self, response):
    item = scraper.items.PostItem()
    item['title'] = response.meta['title']
    item['link'] = response.meta['link']
    item['date'] = response.meta['date']
    item['text'] = " ".join(self.select(response, 'text').extract())
    yield item


def _select(self, obj, var_name):
    """Applies either css or xpath selector to 'obj'

    The final choice depends on the class variable.
    Var_name can be either 'post' or 'title'.
    """
    schemas = {'_css': obj.css, '_xpath': obj.xpath}
    for schema, func in schemas.items():
        var = var_name + schema
        if hasattr(self, var):
            return func(getattr(self, var))
    raise exc.SpiderException("No such variable: %s" % var)


def _parse(self, response):
    dirname = os.path.join(settings.SCRAPED_DIR, self.name)
    # if no SCRAPED_DIR/scrapername directory exists, create one
    if not os.path.exists(dirname):
        os.makedirs(dirname)
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
    """
    cls_attrs = {'parse': _parse, 'fetch_body': _fetch_body,
                 'select': _select, 'process_date': _process_date}
    try:
        for req_arg in ["name", "allowed_domains", "start_urls"]:
            val = kwargs.pop(req_arg)
            cls_attrs[req_arg] = val
    except KeyError:
        raise exc.SpiderException(
            "%s attribute is required for spider creation" % req_arg)
    return type(cls_attrs['name'] + "Class", (scrapy.Spider, ), cls_attrs)
