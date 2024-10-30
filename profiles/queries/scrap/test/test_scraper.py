# test/test_scraper.py
import os
import re
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from urllib.parse import parse_qs, urlparse
import unittest
from unittest.mock import patch

# Import the function you want to test
from scraper import extract_cache_path

class TestExtractCachePath(unittest.TestCase):
    def setUp(self):
        self.base_url = 'https://opencorporates.com/'
        self.current_url = 'https://opencorporates.com/companies/us_ut/123456'
        self.cache_folder = 'soap_cache'

    @patch('scraper.globals.current_url', new='https://opencorporates.com/companies/us_ut/123456')
    @patch('scraper.CACHE_FOLDER', new='soap_cache')
    def test_extract_cache_path_companies(self):
        url = 'https://opencorporates.com/companies/us_ut/123456/officers'
        expected_path = 'soap_cache\\us_ut\\123456\\companies_us_ut_123456_officers.txt'
        self.assertEqual(extract_cache_path(url), expected_path)

    @patch('scraper.globals.current_url', new='https://opencorporates.com/companies/us_ut/123456')
    @patch('scraper.CACHE_FOLDER', new='soap_cache')
    def test_extract_cache_path_officers(self):
        url = 'https://opencorporates.com/officers/456789'
        expected_path = 'soap_cache\\us_ut\\123456\\officers_456789.txt'
        self.assertEqual(extract_cache_path(url), expected_path)

    @patch('scraper.globals.current_url', new='https://opencorporates.com/companies/us_ut/123456')
    @patch('scraper.CACHE_FOLDER', new='soap_cache')
    def test_extract_cache_path_with_page(self):
        url = 'https://opencorporates.com/companies/us_ut/123456/officers?page=2'
        expected_path = 'soap_cache\\us_ut\\123456\\companies_us_ut_123456_officers_page_2.txt'
        self.assertEqual(extract_cache_path(url), expected_path)

    @patch('scraper.globals.current_url', new='https://opencorporates.com/companies/us_ut/123456')
    @patch('scraper.CACHE_FOLDER', new='soap_cache')
    def test_extract_cache_path_invalid_url(self):
        url = 'httsps:a//example.com/invalid'
        with self.assertRaises(ValueError):
            extract_cache_path(url)

if __name__ == '__main__':
    unittest.main()
