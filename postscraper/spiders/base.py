import codecs
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


def _get_email(self):
    """Returns the contents of email file if any found"""
    if os.path.exists(self.email_filename):
        with open(self.email_filename) as f:
            f.seek(0)
            return f.read().strip()
    return None


def _set_email(self, data):
    if data:
        with codecs.open(self.email_filename, 'w', 'utf-8') as f:
            f.write(data)
    elif os.path.exists(self.email_filename):
        os.remove(self.email_filename)


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
    return cls.API_URL % (method, "&".join(["%s=%s" % (k, v)
                                           for (k, v) in kwargs.items()]))


def _parse_vk_wall(self, response):
    """Deals with wall posts' json data received from VK API"""
    data = json.loads(response.body)
    posts_data = data["response"][1:]
    for post in posts_data:
        item = postscraper.items.PostItem()
        item['date'] = utils.convert_date_to_str(
            datetime.fromtimestamp(post['date']))
        item['text'] = post['text']
        item['title'] = ("Wall post from %s" % item['date'])
        item['link'] = ("http://vk.com/public%(group)s?w=wall-%(id)s" %
                        {'group': abs(self.owner_id),
                         'id': "%s_%s" % (abs(self.owner_id), post['id'])})
        yield item


def _parse_vk_board(self, response):
    """Deals with board comments' json data received from VK API"""
    data = json.loads(response.body)
    count = data["response"]["comments"][0]
    topic_id = response.meta['topic_id']

    def _process_comments(response):
        data = json.loads(response.body)
        posts_data = data["response"]["comments"][1:]
        for post in posts_data:
            item = postscraper.items.PostItem()
            item['date'] = utils.convert_date_to_str(
                datetime.fromtimestamp(post['date']))
            item['text'] = post['text']
            item['title'] = ("Board post from %s" % item['date'])
            item['link'] = ("http://vk.com/public%(group)s?w=wall-%(id)s" %
                            {'group': abs(self.owner_id),
                             'id': "%s_%s" % (abs(self.owner_id), post['id'])})
            yield item

    # FIXME last 100 comments per request is VK API limitation
    fetch_last_100 = self.get_url('board.getComments',
                                  count=100,
                                  offset=max(count-100, 0),
                                  topic_id=topic_id,
                                  group_id=abs(self.owner_id),
                                  api_version=self.API_VERSION,
                                  format=self.FORMAT)
    yield scrapy.Request(fetch_last_100, callback=_process_comments)


def _start_requests_vk(self):
    scrape_wall_url = self.get_url(
        'wall.get', count=self.count, owner_id=self.owner_id,
        offset=self.offset, version=self.API_VERSION, format=self.FORMAT)
    scrape_board_urls = [self.get_url('board.getComments',
                                      count=1,
                                      offset=0,
                                      topic_id=topic_id,
                                      group_id=abs(self.owner_id),
                                      version=self.API_VERSION,
                                      format=self.FORMAT)
                         for topic_id in self.boards_to_crawl]
    urls = [('wall', scrape_wall_url)]
    urls.extend([('board', url) for url in scrape_board_urls])
    for (i, (type, url)) in enumerate(urls):
        if type == 'wall':
            request = scrapy.Request(url, dont_filter=True,
                                     callback=self.parse_wall)
        else:
            request = scrapy.Request(
                url, dont_filter=True,
                callback=self.parse_board,
                meta={'topic_id': self.boards_to_crawl[i-1]})
        yield request


def _common_attrs_dict(spider_name):
    return {'last_ts': property(fget=_get_last_ts, fset=_set_last_ts),
            'last_seen_filename': os.path.join(settings.SCRAPED_DIR,
                                               spider_name,
                                               settings.LAST_SEEN_FILENAME),
            'email': property(fget=_get_email, fset=_set_email),
            'email_filename': os.path.join(settings.SCRAPED_DIR, spider_name,
                                           settings.EMAIL_BODY_FILENAME)}


def gen_spider_class(**kwargs):
    """Generates a spider class with given name/allowed_domains/start_urls

    The class will have a default parse method.
    Besides a directory for spider data will be created.
    """
    cls_attrs = _common_attrs_dict(kwargs.get('name'))
    cls_attrs.update({'parse': _parse, 'fetch_body': _fetch_body,
                      'select': _select, 'process_date': _process_date})
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
    cls_attrs = _common_attrs_dict(kwargs.get('name'))
    cls_attrs.update({
        'API_URL': 'https://api.vk.com/method/%s?%s',
        'API_VERSION': '5.37',
        'FORMAT': 'json',
        'boards_to_crawl': kwargs.get('boards') or [],
        'count': kwargs.get('count', 50),
        'offset': kwargs.get('offset', 0),
        'parse_wall': _parse_vk_wall,
        'parse_board': _parse_vk_board,
        'get_url': _get_vk_url,
        'start_requests': _start_requests_vk})
    try:
        for req_arg in ["owner_id", "name"]:
            cls_attrs[req_arg] = kwargs.pop(req_arg)
    except KeyError:
        raise exc.SpiderException(
            "%s attribute is required for spider creation" % req_arg)
    _create_spider_dir(cls_attrs['name'])
    return type(cls_attrs['name'] + "Class", (scrapy.Spider, ), cls_attrs)


def create_vk_spider(name, owner_id, module, boards=None):
    generated = gen_vk_spider_class(name=name, owner_id=owner_id)
    # a nasty hack to make generated class discoverable by scrapy
    generated.__module__ = module
    return generated


def create_site_spider(name, url, module, selectors_dict=None):
    allowed_domains = [urlparse.urlsplit(url)[1]]
    generated = gen_spider_class(name=name, allowed_domains=allowed_domains,
                                 start_urls=[url])
    generated.__module__ = module
    return generated
