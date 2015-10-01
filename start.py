import cookielib
import datetime
import urllib
import urllib2
import urlparse

from flask import Flask, render_template, request, session
import pysolr
from scrapy import selector

from postscraper import settings

app = Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY
VK_AUTH_URL = (("https://oauth.vk.com/authorize?client_id=%(app_id)s"
                "&display=wap&redirect_uri=%(redirect_url)s"
                "&scope=friends&response_type=token&v=5.37") %
               {"app_id": settings.VK_APP_ID,
                "redirect_url": settings.VK_REDIRECT_URL})


@app.route("/results")
def query_results():
    # if nothing selected - output all results
    query = request.args.get('q', '')
    # FIXME some query preprocessing may be needed
    solr = pysolr.Solr(settings.SOLR_URL, timeout=settings.SOLR_TIMEOUT)
    items = solr.search(query, sort="date desc", rows=settings.QUERY_ROWS)
    items_out = list(items.docs)
    for item in items_out:
        # change date format from ugly Solr to nice user defined
        dt = datetime.datetime.strptime(item['date'],
                                        settings.SOLR_DATE_FORMAT)
        item['date'] = dt.strftime(settings.DATE_FORMAT)
    return render_template('show_items.html', items=items_out, query=query)


@app.route("/control")
def control_panel():
    return render_template('control_panel.html',
                           access_token=session.get('vk_access_token'),
                           user_id=session.get('vk_user_id'),
                           expires_in=session.get('vk_expires_in'))


@app.route("/auth")
def vk_auth():
    opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
        urllib2.HTTPRedirectHandler())
    resp = opener.open(VK_AUTH_URL).read()
    sel = selector.Selector(text=resp)
    login_url = sel.xpath(
        "descendant-or-self::form[@method='post']/@action")[0].extract()
    params = {"email": settings.VK_USER_LOGIN,
              "pass": settings.VK_USER_PASSWORD}
    for s in sel.xpath("descendant-or-self::input[@type='hidden']"):
        name = s.xpath("./@name")[0].extract()
        value = s.xpath("./@value")[0].extract()
        params[name] = value
    resp = opener.open(login_url, urllib.urlencode(params))
    url_params = dict(p.split('=')
                      for p in urlparse.urlparse(resp.url).fragment.split('&'))
    for key in url_params:
        session['vk_' + key] = url_params[key]
    return render_template('control_panel.html', **url_params)


if __name__ == "__main__":
    app.run()
