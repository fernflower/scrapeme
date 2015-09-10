import os
import subprocess

from postscraper import mymailsender
from scrapy.settings import Settings
from postscraper import settings


mailer = mymailsender.MailSender.from_settings(
    Settings(settings.MAILER_SETTINGS))


def send_mail(spiders):
    # traverse through all data directories and collect email files
    # FIXME no dir guessing, use spider.email property!
    final_body = ""
    for name in spiders:
        email_file = os.path.join(settings.SCRAPED_DIR, name,
                                  settings.EMAIL_BODY_FILENAME)
        if not os.path.exists(email_file):
            continue
        with open(email_file) as f:
            final_body += f.read()
    if final_body != "":
        mailer.send(to=settings.MAIL_RECIPIENT_LIST,
                    subject="New items from scraper", body=final_body,
                    mimetype="text/html; charset=utf-8")


def main():
    spiders_list = subprocess.check_output(
        ['scrapy', 'list']).strip().split('\n')
    # FIXME use native calls to scrapy API, not subprocess
    ps = subprocess.Popen(('scrapy', 'list'),
                          stdout=subprocess.PIPE)
    subprocess.check_output(('xargs', '-n', '1', 'scrapy', 'crawl'),
                            stdin=ps.stdout)
    ps.wait()
    send_mail(spiders_list)


if __name__ == "__main__":
    main()
