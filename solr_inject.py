import argparse
import datetime
import json

import pysolr

from scraper import settings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_file',
                        help='file with json data to load into Solr')
    parser.add_argument('--solr_url', default=settings.SOLR_URL,
                        help='url where Solr runs', required=False)

    args = parser.parse_args()
    solr = pysolr.Solr(args.solr_url, timeout=settings.SOLR_TIMEOUT)
    with open(args.input_file) as f:
        items = json.load(f)
        # transfer date to datetime
        for item in items:
            str_date = item['date']
            item['date'] = datetime.datetime.strptime(str_date,
                                                      settings.DATE_FORMAT)
    solr.add(items)

if __name__ == "__main__":
    main()
