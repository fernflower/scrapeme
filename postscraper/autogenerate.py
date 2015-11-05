import os

from postscraper import exc
from postscraper import settings
from postscraper.spiders import base


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
