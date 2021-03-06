import json
import logging
import os

from postscraper import exc
from postscraper import settings
from postscraper.spiders import base


LOG = logging.getLogger(__name__)


def gen_spider(spider_data, module):
    """Generates a spider from spider_data dict.

    If any problem occures raises GenerateSpiderError.
    """
    if spider_data.pop('type') != 'vk':
        raise exc.SpiderException(
            'Autogeneration of non-vk spiders not supported!')
    # inject module data
    spider_data['module'] = module
    # transfer all unicode values to str
    spider_data = {k: v.encode('utf-8') if isinstance(v, unicode) else v
                   for k, v in spider_data.items()}
    try:
        return base.create_vk_spider(**spider_data)
    except Exception as e:
        raise exc.GenerateSpiderError('Error during auto generation: %s'
                                      % e.message)


def gen_spider_code(spider_data, module, imports=True, num=0):
    """Generates a text for a spider module out of given data.
    Make sure that spider_data has been verified somewhere else
    """
    # try to instantiate a spider class first
    gen_spider(spider_data, module)
    # generate module code
    txt = "" if not imports else 'from postscraper.spiders import base\n\n\n'
    txt += (('spider_%d = base.create_vk_spider(' % num) + ", ".join(
        ["%s=%s" % (key,
                    value if not isinstance(value, basestring)
                    else '"' + value + '"')
            for key, value in spider_data.items()]) + ')\n\n\n')
    return txt


def create_spider_module(filename, spiders_list):
    new_file = os.path.join(settings.NEWSPIDER_MODULE.replace('.', '/'),
                            filename + '.py')
    if os.path.exists(new_file):
        raise exc.SpiderException(
            "Spider modules can't be overwritten: %s already exists" % new_file)
    with open(new_file, 'w') as f:
        module = settings.NEWSPIDER_MODULE + '.' + filename
        for i, spider_dict in enumerate(spiders_list):
            f.write(gen_spider_code(spider_dict, module=module, num=i,
                                    imports=(i == 0)))


def add_user_spider_json(spider_data):
    spider = gen_spider(spider_data,
                        # XXX here even a fake module will do, fix one day
                        module=settings.AUTOGENERATED_SPIDERS_FILE)
    spider_json = spider.to_dict()
    with open(settings.USER_SPIDERS_FILE, 'a') as f:
        json.dump(spider_json, f, separators=(',', ': '), indent=2)
        f.write(settings.SPIDER_SEPARATOR)
    return spider_json


def load_spiders_from_json(filename, write=False):
    # convert data to json first
    """Load spiders from 'filename'.json.

    Return a list of autogenerated spiders.
    Physical modules will be created with 'write'=True.
    """
    if not os.path.exists(filename):
        LOG.warn("No file with user spiders '%s' found" % filename)
        return []
    with open(filename) as f:
        data = f.read().strip().split(settings.SPIDER_SEPARATOR)
        spiders_data = [json.loads(s) for s in data]
    if write:
        raise NotImplemented("Write func not implemented yet")
    spiders = [gen_spider(sd,
                          module=settings.NEWSPIDER_MODULE + '.%s' % sd['name'])
               for sd in spiders_data]
    return spiders
