import codecs
from datetime import datetime
import json
import logging
import os
import urlparse

import scrapy

from postscraper import exc
import postscraper.items
from postscraper import settings
from postscraper import utils

LOG = logging.getLogger(__name__)


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
    if not date_str:
        return
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
        yield scrapy.Request(link,
                             callback=self.fetch_body,
                             meta={'title': title, 'link': link, 'date': date})


def _process_date(self, sel):
    """Returns date as string in the correct format"""
    return self.select(sel, 'date')[0].extract().strip()


def _create_spider_dir(name):
    # create directory to store spider date
    dirname = os.path.join(settings.SCRAPED_DIR, name)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

# below will be typical VK Spider methods


def _parse_vk_wall(self, response):
    """Deals with wall posts' json data received from VK API"""
    if response.status != 200:
        LOG.info("200 OK expected, got %s" % response.status)
        raise exc.SpiderException("Response code not supported: %s" %
                                  response.status)
    data = json.loads(response.body)
    # FIXME code duplication
    if "error" in data:
        raise exc.SpiderException("%(name)s spider failed: %(reason)s" %
                                  {"reason": data["error"]["error_msg"],
                                   "name": self.name})
    posts_data = data["response"][1:]
    for post in posts_data:
        item = postscraper.items.PostItem()
        if post['text'] == '':
            # a repost of some kind
            try:
                item['text'] = ("%(title)s\n%(description)s" % {
                    'description': post['attachment']['link']['description'],
                    'title': post['attachment']['link']['title']})
                item['link'] = post['attachment']['link']['url']
            except (KeyError, ValueError):
                continue
        else:
            # a native post
            item['text'] = post['text']
            item['link'] = ("http://vk.com/public%(group)s?w=wall-%(id)s" %
                            {'group': abs(self.owner_id),
                             'id': "%s_%s" % (abs(self.owner_id), post['id'])})
        item['date'] = utils.convert_date_to_str(
            datetime.fromtimestamp(post['date']))
        item['title'] = ("Wall post from %s" % item['date'])
        item['author'] = ("http://vk.com/" +
                          ('id%s' % post['from_id']
                           if post['from_id'] > 0
                           else 'club%s' % abs(post['from_id'])))
        yield item


def _parse_vk_board(self, response):
    """Deals with board comments' json data received from VK API"""
    if response.status != 200:
        LOG.info("200 OK expected, got %s" % response.status)
        raise exc.SpiderException("Response code not supported: %s" %
                                  response.status)
    data = json.loads(response.body)
    # FIXME code duplication
    if "error" in data:
        raise exc.SpiderException("%(name)s spider failed: %(reason)s" %
                                  {"reason": data["error"]["error_msg"],
                                   "name": self.name})
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
            item['author'] = ("http://vk.com/" +
                              ('id%s' % post['from_id']
                               if post['from_id'] > 0
                               else 'club%s' % abs(post['from_id'])))
            yield item

    # FIXME last 100 comments per request is VK API limitation
    fetch_last_100 = utils.build_url(utils.API_URL_BOARD,
                                     count=100,
                                     offset=max(count-100, 0),
                                     topic_id=topic_id,
                                     group_id=abs(self.owner_id),
                                     api_version=utils.API_VERSION,
                                     format='json',
                                     access_token=self.access_token)
    yield scrapy.Request(fetch_last_100, callback=_process_comments)


def _start_requests_vk(self):
    scrape_wall_url = utils.build_url(utils.API_URL_WALL,
                                      count=self.count,
                                      owner_id=self.owner_id,
                                      offset=self.offset,
                                      version=utils.API_VERSION,
                                      format='json',
                                      access_token=self.access_token)
    scrape_board_urls = [utils.build_url(utils.API_URL_BOARD,
                                         count=1,
                                         offset=0,
                                         topic_id=topic_id,
                                         group_id=abs(self.owner_id),
                                         version=utils.API_VERSION,
                                         format='json',
                                         access_token=self.access_token)
                         for topic_id in self.boards]
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
                meta={'topic_id': self.boards[i-1]})
        yield request


def to_dict(cls, type):
    res = {'type': type}
    # all non-callables or system functions
    spider_vars = [a for a in dir(cls) if cls.is_repr_param(a)]
    for var in spider_vars:
        res[var] = getattr(cls, var)
    return res


def _common_attrs_dict(spider_name, spider_type):
    return {'last_ts': property(fget=_get_last_ts, fset=_set_last_ts),
            'last_seen_filename': os.path.join(settings.SCRAPED_DIR,
                                               spider_name,
                                               settings.LAST_SEEN_FILENAME),
            'email': property(fget=_get_email, fset=_set_email),
            'email_filename': os.path.join(settings.SCRAPED_DIR, spider_name,
                                           settings.EMAIL_BODY_FILENAME),
            'to_dict': classmethod(lambda x: to_dict(x, type=spider_type)),
            'type': spider_type}


def gen_spider_class(**kwargs):
    """Generates a spider class with given name/allowed_domains/start_urls

    The class will have a default parse method.
    Besides a directory for spider data will be created.
    """
    REQUIRED = ["name", "allowed_domains", "start_urls"]

    @classmethod
    def is_repr_param(cls, param):
        """Used in serialization.

        A method which tells if a parameter should appear in
        to_dict method's output"""
        return (param.endswith('_css') or param.endswith('_xpath') or
                param in REQUIRED)
    cls_attrs = _common_attrs_dict(kwargs.get('name'), 'site')
    cls_attrs.update({'parse': _parse, 'fetch_body': _fetch_body,
                      'select': _select, 'process_date': _process_date,
                      'is_repr_param': is_repr_param})
    try:
        for req_arg in REQUIRED:
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
    REQUIRED = ["name", "owner_id", "access_token"]

    # FIXME generalize?
    @classmethod
    def is_repr_param(cls, param):
        """Used in serialization.

        A method which tells if a parameter should appear in
        to_dict method's output"""
        return param in ["name", "owner_id", "boards"]
    cls_attrs = _common_attrs_dict(kwargs.get('name'), 'vk')
    cls_attrs.update({
        'boards': kwargs.get('boards') or [],
        'count': kwargs.get('count', 50),
        'offset': kwargs.get('offset', 0),
        'parse_wall': _parse_vk_wall,
        'parse_board': _parse_vk_board,
        'is_repr_param': is_repr_param,
        'start_requests': _start_requests_vk})
    try:
        for req_arg in REQUIRED:
            cls_attrs[req_arg] = kwargs.pop(req_arg)
    except KeyError:
        raise exc.SpiderException(
            "%s attribute is required for spider creation" % req_arg)
    _create_spider_dir(cls_attrs['name'])
    return type(cls_attrs['name'] + "Class", (scrapy.Spider, ), cls_attrs)


def create_vk_spider(name, module, boards=None, owner_id=None, url=None,
                     access_token=''):
    if not owner_id and not url:
        raise exc.SpiderException("Either owner_id or url must be specified!")
    if owner_id and url:
        raise exc.SpiderException("Both owner_id and url given, choose one")
    if url:
        raise exc.SpiderException("Url passing not supported yet")
    # XXX call to utils.get_access_token left only for convenient
    # scrapy crawl spider-name calls.
    # FIXME change to calls from control.py one day
    access_token = access_token or utils.get_access_token()
    generated = gen_vk_spider_class(
        name=name, owner_id=owner_id, boards=boards, access_token=access_token)
    # a nasty hack to make generated class discoverable by scrapy
    generated.__module__ = module
    return generated


def create_site_spider(name, url, module, selectors_dict=None):
    allowed_domains = [urlparse.urlsplit(url)[1]]
    generated = gen_spider_class(name=name, allowed_domains=allowed_domains,
                                 start_urls=[url])
    generated.__module__ = module
    # FIXME possible security hazard
    for var, value in selectors_dict.items():
        setattr(generated, var, value)
    return generated
