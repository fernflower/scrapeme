import datetime
import json

import scrapy

from postscraper.spiders import base
import postscraper.items
from postscraper import utils


SpiderMeta = base.gen_vk_spider_class(
    name="eventhunt_vk", owner_id = -55051302)


class VkSpider(SpiderMeta):
    pass
