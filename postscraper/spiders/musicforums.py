# -*- coding: utf-8 -*-
import datetime

from postscraper.spiders import base
from postscraper import settings


SpiderCls = base.create_site_spider(
    name="musicforums",
    url=(u"http://www.musicforums.ru/rabota/?filtr&"
         u"filter=city:%CC%EE%F1%EA%E2%E0;work_type:1;"),
    module=__name__,
    selectors_dict={
        "post_css": "tr [class^=striped]",
        "text_xpath": "(//span[contains(@class, 'body')])[1]/text()",
        # relative to post
        "title_xpath": "./td/a/text()",
        "link_xpath": "./td/a/@href",
        "date_xpath": u".//a[contains(@title, 'Обновлено')]/text()"})


class Spider(SpiderCls):
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
        dt_with_year = datetime.datetime(year=datetime.datetime.now().year,
                                         month=dt.month,
                                         day=dt.day,
                                         hour=dt.hour,
                                         minute=dt.minute,
                                         second=dt.second)
        return dt_with_year.strftime(settings.DATE_FORMAT)
