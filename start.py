import datetime

from flask import Flask, render_template, request
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


@app.route("/control")
def control_panel():
    """Every time user accesses control panel token is updated"""
    login_data = utils.authorize()
    return render_template('control_panel.html', **login_data)


if __name__ == "__main__":
    app.run()
