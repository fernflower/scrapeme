from postscraper.spiders import base


SpiderMeta = base.gen_vk_spider_class(
    name="eventhunt_vk", owner_id=-55051302)


class VkSpider(SpiderMeta):
    pass
