from scraper.spiders import base

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
