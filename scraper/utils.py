from datetime import datetime

from scraper import settings


def convert_to_datetime(date_str):
    return datetime.strptime(date_str, settings.DATE_FORMAT)


def convert_date_to_str(date):
    return date.strftime(settings.DATE_FORMAT)
