import datetime
import os
import subprocess
import time

from flask import Flask, Response, render_template, request, redirect, url_for
import pysolr

from postscraper import exc, settings, utils

app = Flask(__name__)
app.secret_key = settings.FLASK_SECRET_KEY


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
    if not utils.is_authorized_vk():
        return redirect(url_for("oauth_vk"))
    login_data = utils.login_vk_user()
    return render_template('control_panel.html', **login_data)


@app.route("/login", methods=['POST'])
def enter_with_vk():
    login = request.form.get('vk_login')
    password = request.form.get('vk_pass')
    try:
        login_data = utils.authorize(login, password)
        return render_template('control_panel.html', **login_data)
    except exc.VkLoginFailure:
        return Response("Unable to authorize, try again")


@app.route("/set_token", methods=['POST'])
def set_token():
    # XXX may be a bug: request.form.get(key, request.form[KEY]) - 2 also
    # calculated
    vk_url_params = {'vk_' + k.lstrip('#'): v for k, v in request.form.items()}
    for p in vk_url_params:
        os.environ[p] = str(vk_url_params[p])
    # return render_template('control_panel.html', **vk_url_params)
    # FIXME find out how to call control and reload page
    return render_template('control_panel.html', **vk_url_params)


@app.route("/oauth")
def oauth_vk():
    return redirect(utils.VK_AUTH_URL)


@app.route("/authorized")
def login_success():
    return render_template('authorized.html')


@app.route("/crawlall")
def launch_crawl():
    def func():
        # FIXME native call?
        cmd = 'python control.py crawl_all'
        # cmd = 'dmesg'
        proc = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        lines = proc.stderr.readlines(64)
        while lines != []:
            time.sleep(0.1)
            out = u"<br/>\n".join(lines)
            lines = proc.stderr.readlines(64)
            yield out

    return Response(func(), mimetype='text/html; charset=utf-8')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
