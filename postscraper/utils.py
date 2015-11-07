import cookielib
from datetime import datetime
import json
import os
import re
import requests
import urllib
import urllib2
import urlparse

from scrapy import selector

from postscraper import exc
from postscraper import settings


VK_AUTH_URL = (("https://oauth.vk.com/authorize?client_id=%(app_id)s"
                "&display=wap&redirect_uri=%(redirect_url)s"
                "&scope=friends,offline&response_type=token&v=5.37") %
               {"app_id": settings.VK_APP_ID,
                "redirect_url": settings.VK_REDIRECT_URL})

API_URL_WALL = 'https://api.vk.com/method/wall.get?%s'
API_URL_BOARD = 'https://api.vk.com/method/board.getComments?%s'
API_VERSION = '5.37'


def convert_to_datetime(date_str):
    return datetime.strptime(date_str, settings.DATE_FORMAT)


def convert_date_to_str(date):
    return date.strftime(settings.DATE_FORMAT)


def convert_date_to_solr_date(date):
    return date.strftime(settings.SOLR_DATE_FORMAT)


def authorize(login, password):
    """A method for vk user auth and access_token retrieval.

    After a token is aquired any read action with user group can be performed.
    Returns a dictionary with vk_access data (token, user_id, expires_in)
    """
    opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
        urllib2.HTTPRedirectHandler())
    resp1 = opener.open(VK_AUTH_URL)
    sel = selector.Selector(text=resp1.read())
    login_url = sel.xpath(
        "descendant-or-self::form[@method='post']/@action")[0].extract()
    params = {"email": login, "pass": password}
    for s in sel.xpath("descendant-or-self::input[@type='hidden']"):
        name = s.xpath("./@name")[0].extract()
        value = s.xpath("./@value")[0].extract()
        params[name] = value
    logins = 0

    def _try_to_login():
        resp2 = opener.open(login_url, urllib.urlencode(params))
        if 'access_token=' not in resp2.url:
            # no access_token data -> failure
            raise exc.VkLoginFailure("Check credentials")
        url_params = dict(p.split('=') for p in urlparse.urlparse(
            resp2.url).fragment.split('&'))
        vk_url_params = {'vk_' + k: url_params[k] for k in url_params}
        for p in vk_url_params:
            os.environ[p] = str(vk_url_params[p])
        return vk_url_params

    while logins < settings.VK_LOGIN_ATTEMPT:
        try:
            return _try_to_login()
        except:
            # import time
            # time.sleep(settings.DOWNLOAD_DELAY)
            logins += 1
    raise exc.VkLoginFailure("%d login attempts, all failed" % logins)


def login_vk_user():
    """Logins vk user using login/password from settings.

    Acquires access_token and stores it in environment variable
    if no such variable has been set.
    """
    login_data = ['vk_access_token', 'vk_expires_in', 'vk_user_id']
    # FIXME check for token validity, not just existance
    if not all(os.environ.get(p) for p in login_data):
        authorize(settings.VK_USER_LOGIN, settings.VK_USER_PASSWORD)
    return {p: os.environ.get(p) for p in login_data}


def get_access_token():
    if not os.environ.get('vk_access_token'):
        login_vk_user()
    return os.environ.get('vk_access_token')


def get_vk_owner_id(url, access_token):
    group_url = url + '?access_token=%s' % access_token
    html = requests.get(group_url).text
    xpath = ("descendant-or-self::a[@href and "
             "starts-with(@href, '/search?c[section]=people&c[group]')]/@href")
    # if no such url is found then most likely you have no access to this group
    people_group_urls = selector.Selector(text=html).xpath(xpath)
    if len(people_group_urls) == 0:
        raise exc.VkAccessError(group=url)
    people_url = people_group_urls[0].extract()
    m = re.search('\[group\]=(\d+)', people_url)
    return -1 * int(m.group(1))


def build_url(url_base, **kwargs):
    """Builds a url to retrieve data from VK

    Arguments from **kwargs will be passed in form
    key1=value1&key2=value2 ...
    """
    return url_base % "&".join(["%s=%s" % (k, v) for (k, v) in kwargs.items()])


def check_vk_access(url, access_token, raise_exc=True):
    """Checks that this token is valid for data retrieval.

    Performs a wall.get request (1 post).
    Raises VkAccessError if fails and raise_exc.
    If wall data has been successfully retrieved, returns group's owner_id..
    """
    group_id = get_vk_owner_id(url=url, access_token=access_token)
    scrape_wall_url = build_url(API_URL_WALL,
                                count=1,
                                owner_id=group_id,
                                version=API_VERSION,
                                format='json',
                                access_token=access_token)
    data = json.loads(requests.get(scrape_wall_url).text)
    # FIXME code duplication, see postscraper.spiders.base
    if "error" in data:
        if raise_exc:
            raise exc.VkAccessError(group=group_id)
        return None
    return group_id
