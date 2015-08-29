# -*- coding: utf-8 -*-
import datetime

from postscraper.spiders import base
from postscraper import settings

SpiderMeta = base.gen_spider_class(
    name="musicforums", allowed_domains=["musicforums.ru"],
    start_urls=[u"http://www.musicforums.ru/rabota/?filtr&"
                u"filter=city:%CC%EE%F1%EA%E2%E0;work_type:1;"])


class MusicForumsSpider(SpiderMeta):
    post_css = "tr [class^=striped]"
    text_xpath = "(//span[contains(@class, 'body')])[1]/text()"
    # relative to post
    title_xpath = "./td/a/text()"
    link_xpath = "./td/a/@href"
    date_xpath = u".//a[contains(@title, 'Обновлено')]/text()"

    def process_date(self, sel):
        date = self.select(sel, 'date')[0].extract().strip()
        # musicforums stores date as %d-%m %H:%M (ex. 28-08 19:53)
        date_format = "%d-%m %H:%M"
        dt = datetime.datetime.strptime(date, date_format)
        return dt.strftime(settings.DATE_FORMAT)
