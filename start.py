import datetime

from flask import Flask, Response, render_template, request
import pysolr

from postscraper import settings, utils

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
    login_data = utils.login_vk_user()
    return render_template('control_panel.html', **login_data)


if __name__ == "__main__":
    app.run()
