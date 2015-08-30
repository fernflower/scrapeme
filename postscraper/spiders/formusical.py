from postscraper.spiders import base


SpiderMeta = base.gen_vk_spider_class(
    name="formusical_vk", owner_id=-33576030)


class VkSpider(SpiderMeta):
    boards_to_crawl = [27643700]
