import os

import scrapy

from postscraper import settings


class D3Spider(scrapy.Spider):
    name = "d3"
    allowed_domains = ["d3.ru"]
    start_urls = ["https://d3.ru/"]

    POST_XPATH = "//div[contains(concat(' ', @data-post_type, ' '), 'post')]"
    # relative to post
    TITLE_XPATH = ("./div[contains(concat(' ', @class, ' '), 'dt')]"
                   "//h3/a[not(@class='b-post_snippet_icon')]/text()")

    def parse(self, response):
        name = response.url.split('/')[2] + '.html'
        dirname = os.path.join(settings.SCRAPED_DIR, self.name)
        path = os.path.join(dirname, name)
        # if no SCRAPED_DIR/postscrapername directory exists, create one
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(path, 'wb') as f:
            f.write(response.body)
        for sel in response.xpath(self.POST_XPATH):
            title = sel.xpath(self.TITLE_XPATH)[0].extract().strip()
            print(title)
