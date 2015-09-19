from postscraper.spiders import base


# a general code for automatic VK Spider creation.
spider = base.create_vk_spider(
    name="formusical_vk", owner_id=-33576030, boards=[27643700],
    module=__name__)
