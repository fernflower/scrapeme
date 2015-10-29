from postscraper.spiders import base


# a general code for automatic VK Spider creation.
Spider = base.create_vk_spider(
    name="eventhunt_vk", owner_id=-55051302, module=__name__)
