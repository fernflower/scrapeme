import datetime
import logging
import subprocess
import time

import flask
from flask import Flask, Response, render_template, request, redirect, url_for
import pysolr
from scrapy.utils.log import configure_logging

from postscraper import autogenerate
from postscraper import exc
from postscraper import settings
from postscraper import utils
from postscraper import spider_utils

app = Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY

configure_logging()
LOG = logging.getLogger(__name__)


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


@app.route("/cleanup")
def cleanup():
    """Remove data from solr older than post ttl"""
    solr = pysolr.Solr(settings.SOLR_URL, timeout=settings.SOLR_TIMEOUT)
    date = utils.convert_date_to_solr_date(
        datetime.datetime.now() - datetime.timedelta(days=settings.POSTS_TTL))
    xml = solr.delete(q="date:[* TO %s]" % date)
    return Response(xml, mimetype="text/xml")


@app.route("/control")
def control_panel():
    TOKEN_KEYS = ['access_token', 'user_id', 'expires_in']
    if not all(request.values.get(x) is not None for x in TOKEN_KEYS):
        return redirect(url_for("oauth_vk"))
    login_data = {k: request.values.get(k) for k in TOKEN_KEYS}
    return render_template('control_panel.html', **login_data)


@app.route("/oauth")
def oauth_vk():
    return redirect(utils.VK_AUTH_URL)


@app.route("/authorized")
def login_success():
    return render_template('authorized.html')


@app.route("/crawlall")
def launch_crawl():
    token = request.args.get('access_token', '')

    def func():
        # FIXME native call?
        cmd = 'python control.py crawl_all --token %s' % token
        # cmd = 'dmesg'
        proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        lines = proc.stderr.readlines(64)
        while lines != []:
            time.sleep(0.1)
            out = u"<br/>\n".join(lines)
            lines = proc.stderr.readlines(64)
            yield out

    return Response(func(), mimetype='text/html; charset=utf-8')


@app.route("/addform")
def add_spider_form():
    token = request.args.get('access_token', '')
    return render_template('add_spider.html', token=token)


@app.route("/getownerid", methods=['POST'])
def get_owner_id():
    token = request.form.get('access_token', '')
    url = request.form.get('url')
    if not url or not token:
        return {}
    try:
        owner_id = utils.check_vk_access(url=url, access_token=token)
    except exc.VkAccessError as e:
        return flask.jsonify(**{'status': 'fail', 'message': e.message})

    return flask.jsonify(**{'owner_id': owner_id, 'access_token': token,
                            'url': url, 'status': 'success'})


@app.route("/add", methods=['POST'])
def process_add_spider():
    try:
        url = request.form.get('vk_group_url')
        spider_name = request.form.get('spider_name')
        owner_id = utils.get_vk_owner_id(url)
        board_urls = request.form.getlist('board_url[]')
        # FIXME XXX not the best way to acquire board number
        group_boards = [int(x.split('_')[-1]) for x in board_urls
                        if 'vk.com/topic%d' % owner_id in x]
        # if spider with this name or url already exists -> raise an error
        error = None
        if spider_utils.find_spider(name=spider_name, type='vk'):
            error = {'status': 'fail',
                     'error': ('A spider with the name %s already exists' %
                               spider_name)}
        if spider_utils.find_spider(owner_id=owner_id, type='vk'):
            # FIXME make it editable for the user
            error = {'status': 'fail',
                     'error': 'A spider for group %s already exists' % owner_id}
        if error:
            return flask.jsonify(**error)

        # leave those urls that refer to the group
        if len(group_boards) != len(board_urls):
            LOG.warn("Not all board_urls refer to the VK group,"
                     " invalid will be left out.")
        spider_json = autogenerate.add_user_spider_json(
            {'type': 'vk', 'owner_id': owner_id, 'boards': group_boards,
             'name': spider_name})
    except exc.VkSpiderException as e:
        error = {'status': 'fail', 'error': e.message}
        return flask.jsonify(**error)

    return flask.jsonify(**spider_json)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
