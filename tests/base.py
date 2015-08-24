import __builtin__
from contextlib import nested
import os
import tempfile
import unittest

import mock
from scrapy import http
from scrapy.http.response import html


class TestBase(unittest.TestCase):
    def setUp(self, spider_cls):
        self.spider = spider_cls()
        self.testdir = "tests/data"
        self.mock_dict = {
            self.spider.last_seen_filename: tempfile.NamedTemporaryFile(
                delete=False)}
        super(TestBase, self).setUp()

    def run(self, *args, **kwargs):
        """Runs a test substituting filehandles.

        open() will work with filehandles stored in self.mock_dict.
        """
        # save standard open func
        open_func = __builtin__.open
        os_path_exists_func = os.path.exists

        def myopen(*args, **kwargs):
            filename = args[0]
            try:
                new_args = [self.mock_dict[filename].name] + list(args[1:])
                return open_func(*new_args, **kwargs)
            except KeyError:
                return open_func(*args, **kwargs)

        def mypath_exists(*args, **kwargs):
            path = args[0]
            if path in self.mock_dict.keys():
                return True
            return os_path_exists_func(*args, **kwargs)

        mock_open = mock.MagicMock(side_effect=myopen)
        mock_path_exists = mock.MagicMock(side_effect=mypath_exists)
        with nested(mock.patch.object(__builtin__, "open", mock_open),
                    mock.patch.object(os.path, "exists", mock_path_exists)):
            return super(TestBase, self).run(*args, **kwargs)

    def tearDown(self):
        for f, temp in self.mock_dict.items():
            os.remove(temp.name)
        super(TestBase, self).tearDown()

    def fake_request(self, filename=None, url="http://www.example.com"):
        filename = filename or os.path.join(self.testdir,
                                            self.spider.name + ".html")
        request = http.Request(url=url)
        with open(filename) as f:
            response = html.HtmlResponse(request=request,
                                         body=f.read(), url=url)
            return response
