import datetime
import os
import unittest

from scraper.spiders import musicforums
from scraper import utils

from tests import base


class TestLastTimestamp(base.TestBase):
    def setUp(self):
        super(TestLastTimestamp, self).setUp(
            spider_cls=musicforums.MusicForumsSpider)

    def test_last_ts_prop(self):
        # check that on creation no ts is set
        self.assertIsNone(self.spider.last_ts)
        date = datetime.datetime.utcnow()
        date_str = utils.convert_date_to_str(date)
        # check that both datetime object and date_str can be set
        self.spider.last_ts = date
        self.assertEqual(datetime.datetime, type(self.spider.last_ts))
        self.spider.last_ts = date_str
        self.assertEqual(datetime.datetime, type(self.spider.last_ts))
        # last_ts is set after crawl job and the file exists as well
        self.assertIsNotNone(self.spider.last_ts)
        self.assertTrue(os.path.exists(self.spider.last_seen_filename))

    @unittest.skip("Find a way to test with pipeline")
    def test_fetch_new(self):
        """Check that no pages older that last_ts are fetched.

        Two subsequent runs should produce N and 0 items.
        """
        data = self.fake_request()
        requests = self.spider.parse(data)
        self.assertEqual(152, sum(1 for i in requests))
        data_old = self.fake_request()
        items_0 = self.spider.parse(data_old)
        self.assertEqual(0, sum(1 for i in items_0))
