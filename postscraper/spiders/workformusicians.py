from postscraper.spiders import base


# a general code for automatic VK Spider creation.
Spider = base.create_vk_spider(
    name="work_for_musicians", owner_id=-278407, module=__name__)
