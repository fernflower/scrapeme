# -*- coding: utf-8 -*-
import datetime

from scraper.spiders import base
from scraper import settings

SpiderMeta = base.gen_spider_class(
    name="musicforums", allowed_domains=["musicforums.ru"],
    start_urls=[u"http://www.musicforums.ru/rabota/?filtr&"
                u"filter=city:%CC%EE%F1%EA%E2%E0;work_type:1;"])


class MusicForumsSpider(SpiderMeta):
    post_css = "tr [class^=striped]"
    text_xpath = "//span[contains(@class, 'body')]/text()"
    # relative to post
    title_xpath = "./td/a/text()"
    link_xpath = "./td/a/@href"
    date_xpath = u".//a[contains(@title, 'Обновлено')]/@href"

    def process_date(self, sel):
        date = self.select(sel, 'date')[0].extract().strip()
        seconds = date.split('#N')[-1]
        # FIXME return datetime in order to load in solr
        dt = datetime.datetime.fromtimestamp(int(seconds))
        return dt.strftime(settings.DATE_FORMAT)
