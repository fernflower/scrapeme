from postscraper.spiders import base


# a general code for automatic VK Spider creation.
Spider = base.create_vk_spider(
    name="work_for_musicians", url="http://vk.com/work_for_musicians",
    module=__name__)
