# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PostItem(scrapy.Item):
    title = scrapy.Field()
    link = scrapy.Field()
    text = scrapy.Field()
    # date is stored as string
    date = scrapy.Field()
    # crawler name where the item came from
    source = scrapy.Field()
