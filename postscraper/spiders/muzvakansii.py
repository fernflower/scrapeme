from postscraper.spiders import base


# a general code for automatic VK Spider creation.
spider = base.create_vk_spider(
    name="muzvakansii_vk", owner_id=-76576860, module=__name__)
