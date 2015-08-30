from postscraper.spiders import base


SpiderMeta = base.gen_vk_spider_class(
    name="muzvakansii_vk", owner_id=-76576860)


class VkSpider(SpiderMeta):
    pass
