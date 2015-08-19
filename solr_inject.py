import argparse
import datetime
import json

import pysolr

from scraper import settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='file with json data to load into Solr')
    parser.add_argument('--solr_url', default="http://localhost:8080/solr",
                        help='url where Solr runs', required=False)

    args = parser.parse_args()
    solr = pysolr.Solr(args.solr_url, timeout=10)
    with open(args.input_file) as f:
        items = json.load(f)
        # FIXME will be removed after prototype is finished
        import render
        raw_html = render.show_items(items)
        with open('out.html', 'wb') as html:
            html.write(raw_html.encode('utf-8'))
        # transfer date to datetime
        for item in items:
            str_date = item['date']
            item['date'] = datetime.datetime.strptime(str_date,
                                                      settings.DATE_FORMAT)
    solr.add(items)

if __name__ == "__main__":
    main()
