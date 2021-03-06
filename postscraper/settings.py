# -*- coding: utf-8 -*-

import postscraper.secret_settings as secret_settings

# Scrapy settings for postscraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'postscraper'

SPIDER_MODULES = ['postscraper.spiders']
NEWSPIDER_MODULE = 'postscraper.spiders'
AUTOGENERATED_SPIDERS_FILE = 'autogenerated'
USER_SPIDERS_FILE = 'user_spiders.json'
# a separater in USER_SPIDERS_FILE and export/import output/input
SPIDER_SEPARATOR = '\n\n'

# custom settings section
SCRAPED_DIR = "data"
DATE_FORMAT = "%d-%m-%Y %H:%M:%S"
SOLR_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SOLR_URL = "http://localhost:8080/solr"
SOLR_TIMEOUT = 10
LAST_SEEN_FILENAME = "last"
EMAIL_BODY_FILENAME = "email_text"
TEMPLATES_DIR = "templates"
# mailer settings
MAILER_SETTINGS = secret_settings.MY_MAILER_SETTINGS
MAIL_RECIPIENT_LIST = secret_settings.MY_MAIL_RECIPIENT_LIST
# FIXME move queries out of global settings someday
QUERY = u"бас,контрабас,jazz,джаз,скрипка,аккордеон,кахон,французский,музыкант"
# max number of posts to output per source
QUERY_ROWS = 100
# days from now that a post remains actual (later won't be shown and may be
# deleted)
POSTS_TTL = 21
VK_APP_ID = 5090679
VK_REDIRECT_URL = "http://scraper.kreda.today/authorized"
VK_USER_LOGIN = secret_settings.MY_VK_USER_LOGIN
VK_USER_PASSWORD = secret_settings.MY_VK_USER_PASSWORD
FLASK_SECRET_KEY = secret_settings.MY_FLASK_SECRET_KEY
VK_LOGIN_ATTEMPT = 5


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'postscraper (+http://www.yourdomain.com)'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS=32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY=0.3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN=16
#CONCURRENT_REQUESTS_PER_IP=16

# Disable cookies (enabled by default)
#COOKIES_ENABLED=False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED=False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
    #'postscraper.middlewares.SolrInjectMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'postscraper.middlewares.MyCustomDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'postscraper.pipelines.RemoveDuplicatesPipeline': 300,
    'postscraper.pipelines.SendMailPipeline': 500,
    # solr inject has to be after sendMail as injection is done in
    # close_spider() and these funcs are called in reverse order
    'postscraper.pipelines.SolrInjectPipeline': 700,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# NOTE: AutoThrottle will honour the standard settings for concurrency and delay
#AUTOTHROTTLE_ENABLED=True
# The initial download delay
#AUTOTHROTTLE_START_DELAY=5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY=60
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG=False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED=True
#HTTPCACHE_EXPIRATION_SECS=0
#HTTPCACHE_DIR='httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES=[]
#HTTPCACHE_STORAGE='scrapy.extensions.httpcache.FilesystemCacheStorage'
