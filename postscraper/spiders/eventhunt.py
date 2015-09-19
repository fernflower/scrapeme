from postscraper.spiders import base


# a general code for automatic VK Spider creation.
spider = base.create_vk_spider(
    name="eventhunt_vk", owner_id=-55051302, module=__name__)
