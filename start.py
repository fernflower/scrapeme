from flask import Flask, render_template, request
import pysolr

from scraper import settings

app = Flask(__name__)


@app.route("/results")
def query_results():
    # if nothing selected - output all results
    query = request.args.get('q', '')
    # FIXME some query preprocessing may be needed
    solr = pysolr.Solr(settings.SOLR_URL, timeout=settings.SOLR_TIMEOUT)
    items = solr.search(query)
    return render_template('show_items.html', items=items.docs)


if __name__ == "__main__":
    app.run()
