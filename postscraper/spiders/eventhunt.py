from postscraper.spiders import base


# a general code for automatic VK Spider creation.
Spider = base.create_vk_spider(
    name="eventhunt_vk", url="http://vk.com/myeventhunt", module=__name__)
