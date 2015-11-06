import cookielib
from datetime import datetime
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
    people_url = selector.Selector(text=html).xpath(xpath)[0].extract()
    m = re.search('\[group\]=(\d+)', people_url)
    return -1 * int(m.group(1))
