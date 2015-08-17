import argparse
import json

import pysolr


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
    solr.add(items)

if __name__ == "__main__":
    main()
