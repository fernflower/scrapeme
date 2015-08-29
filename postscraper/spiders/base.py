from datetime import datetime
import json
import os
import urlparse

import scrapy

from postscraper import exc
import postscraper.items
from postscraper import settings
from postscraper import utils


def _fetch_body(self, response):
    item = postscraper.items.PostItem()
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
            f.seek(0)
            try:
                return utils.convert_to_datetime(f.read().strip())
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


def _create_spider_dir(name):
    # create directory to store spider date
    dirname = os.path.join(settings.SCRAPED_DIR, name)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

# below will be typical VK Spider methods

def _get_vk_url(cls, method, **kwargs):
    """Builds a url to retrieve data from VK

    Arguments from **kwargs will be passed in form
    key1=value1&key2=value2 ...
    """
    return cls.SCRAPE_WALL_URL % "&".join(["%s=%s" % (k, v)
                                            for (k, v) in kwargs.items()])

def _parse_vk(self, response):
    """Deals with json data received from VK API"""
    data = json.loads(response.body)
    posts_data = data["response"][1:]
    for post in posts_data:
        item = postscraper.items.PostItem()
        item['date'] = utils.convert_date_to_str(
            datetime.fromtimestamp(post['date']))
        item['text'] = post['text']
        item['title'] = ("Post from %s" % item['date'])
        item['link'] = ("http://vk.com/public%(group)s?w=wall-%(id)s" %
                        {'group': abs(self.owner_id),
                         'id': "%s_%s" % (abs(self.owner_id), post['id'])})
        yield item


def _start_requests_vk(self):
    scrape_url = self.get_url(
        'wall.get', count=self.count, owner_id=self.owner_id,
        offset=self.offset, version=self.API_VERSION, format=self.FORMAT)
    yield self.make_requests_from_url(scrape_url)


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
            cls_attrs[req_arg] = kwargs.pop(req_arg)
    except KeyError:
        raise exc.SpiderException(
            "%s attribute is required for spider creation" % req_arg)
    _create_spider_dir(cls_attrs['name'])
    return type(cls_attrs['name'] + "Class", (scrapy.Spider, ), cls_attrs)


def gen_vk_spider_class(**kwargs):
    """Generates a VK spider class with given name

    Spider will scrape wall, owner_id argument is obligatory.
    """
    cls_attrs = {'last_ts': property(fget=_get_last_ts, fset=_set_last_ts),
                 'last_seen_filename': os.path.join(
                     settings.SCRAPED_DIR, kwargs['name'],
                     settings.LAST_SEEN_FILENAME),
                 'SCRAPE_WALL_URL': 'https://api.vk.com/method/wall.get?%s',
                 'API_VERSION': '5.37',
                 'FORMAT': 'json',
                 'count': kwargs.get('count', 50),
                 'offset': kwargs.get('offset', 0),
                 'parse': _parse_vk,
                 'get_url': _get_vk_url,
                 'start_requests': _start_requests_vk}
    try:
        for req_arg in ["owner_id", "name"]:
            cls_attrs[req_arg] = kwargs.pop(req_arg)
    except KeyError:
        raise exc.SpiderException(
            "%s attribute is required for spider creation" % req_arg)
    _create_spider_dir(cls_attrs['name'])
    return type(cls_attrs['name'] + "Class", (scrapy.Spider, ), cls_attrs)
