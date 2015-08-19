import jinja2

from scraper import settings


def show_items(items):
    loader = jinja2.FileSystemLoader(settings.TEMPLATES_DIR)
    env = jinja2.Environment(loader=loader)
    template = env.get_template('show_items.html')
    return template.render({'items': items,
                            'static_dir': settings.STATIC_DIR})
