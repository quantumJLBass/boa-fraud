# test/test_scraper_all.py
import unittest
from unittest.mock import patch, MagicMock
import os
import json
from bs4 import BeautifulSoup
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scraper import (
    save_data_intermediate,
    extract_cache_path,
    cache_exists,
    load_cached_urls,
    save_cached_urls,
    update_cached_url_status,
    load_cache,
    save_cache,
    warm_cache,
    warm_officer_cache,
    fetch_html,
    load_html_content,
    scrape_data,
    extract_officer_urls,
    extract_company_id_from_url,
    extract_links,
    extract_attributes,
    extract_assertions,
    extract_filings,
    extract_events,
    extract_officers,
    extract_relationships
)
import gs

class TestScraperFunctions(unittest.TestCase):

    def setUp(self):
        self.base_url = 'https://opencorporates.com/'
        self.current_url = 'https://opencorporates.com/companies/us_ut/123456'
        self.cache_folder = 'soap_cache'
        gs.current_url = self.current_url

        # Load HTML files
        self.load_html_files()

    def load_html_files(self):
        self.main_html = self.read_file('test/mock-site/main-url-companies_us_mt_F007307.txt')
        self.filings_html = self.read_file('test/mock-site/sub-url-companies_us_mt_F007307_fillings.txt')
        self.filings_html_page_2 = self.read_file('test/mock-site/sub-url-companies_us_mt_F007307_fillings_page_2.txt')
        self.officers_html = self.read_file('test/mock-site/sub-url-companies_us_mt_F007307_officers.txt')
        self.officers_html_page_2 = self.read_file('test/mock-site/sub-url-companies_us_mt_F007307_officers_page_2.txt')
        self.relationships_html = self.read_file('test/mock-site/sub-url-companies_us_mt_F007307_statements_branch_relationship_object.txt')
        self.events_html = self.read_file('test/mock-site/sub-url-companies_us_mt_F007307_events.txt')

    def read_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    @patch('scraper.requests.get')
    def test_fetch_html(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = self.main_html
        mock_get.return_value = mock_response

        driver = MagicMock()
        soup = fetch_html(self.current_url, driver)
        self.assertIsInstance(soup, BeautifulSoup)
        self.assertTrue(soup.find('div'))

    def test_extract_cache_path(self):
        url = 'https://opencorporates.com/companies/us_ut/123456/officers'
        expected_path = 'soap_cache/us_ut/123456/companies_us_ut_123456_officers.txt'
        self.assertEqual(extract_cache_path(url), expected_path)

    @patch('os.path.exists')
    def test_cache_exists(self, mock_exists):
        mock_exists.return_value = True
        url = 'https://opencorporates.com/companies/us_ut/123456/officers'
        self.assertTrue(cache_exists(url))

    def test_save_data_intermediate(self):
        data = {'key1': 'value1'}
        filename = 'test_data.json'
        save_data_intermediate(data, filename)
        with open(filename, 'r') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, data)
        os.remove(filename)

    def test_load_cached_urls(self):
        filename = 'test_cached_urls.json'
        with open(filename, 'w') as f:
            json.dump([], f)
        self.assertEqual(load_cached_urls(), [])
        os.remove(filename)

    def test_save_cached_urls(self):
        cached_urls = [{'url': 'https://opencorporates.com/companies/us_ut/123456'}]
        filename = 'test_cached_urls.json'
        save_cached_urls(cached_urls)
        with open(filename, 'r') as f:
            loaded_data = json.load(f)
        self.assertEqual(loaded_data, cached_urls)
        os.remove(filename)

    def test_update_cached_url_status(self):
        cached_urls = [{'url': self.current_url, 'sub_urls': [], 'officers': []}]
        with patch('scraper.load_cached_urls', return_value=cached_urls), \
             patch('scraper.save_cached_urls') as mock_save:
            update_cached_url_status(self.current_url, sub_url='https://opencorporates.com/companies/us_ut/123456/officers')
            self.assertTrue(any(sub['sub_url'] == 'https://opencorporates.com/companies/us_ut/123456/officers' for sub in cached_urls[0]['sub_urls']))
            mock_save.assert_called_once()

    @patch('scraper.extract_cache_path', return_value='non_existent_cache_path')
    @patch('os.path.exists', return_value=False)
    def test_load_cache(self, mock_exists, mock_extract):
        self.assertIsNone(load_cache(self.current_url))

    @patch('scraper.extract_cache_path', return_value='test_cache.txt')
    def test_save_cache(self, mock_extract):
        url = 'https://opencorporates.com/companies/us_ut/123456'
        html = '<html></html>'
        save_cache(url, html)
        with open('test_cache.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, html)
        os.remove('test_cache.txt')

    @patch('scraper.load_cached_urls', return_value=[])
    @patch('scraper.save_cached_urls')
    @patch('scraper.cache_exists', return_value=False)
    @patch('scraper.fetch_html', return_value=BeautifulSoup('<html></html>', 'html.parser'))
    def test_warm_cache(self, mock_fetch, mock_exists, mock_save, mock_load):
        urls = ['https://opencorporates.com/companies/us_ut/123456']
        driver = MagicMock()
        warm_cache(urls, driver)
        self.assertTrue(mock_fetch.called)

    @patch('scraper.cache_exists', return_value=False)
    @patch('scraper.fetch_html', return_value=BeautifulSoup('<html></html>', 'html.parser'))
    def test_warm_officer_cache(self, mock_fetch, mock_exists):
        url = 'https://opencorporates.com/companies/us_ut/123456'
        driver = MagicMock()
        section_soup = BeautifulSoup('<html></html>', 'html.parser')
        warm_officer_cache(url, driver, section_soup)
        self.assertTrue(mock_fetch.called)

    def test_extract_officer_urls(self):
        soup = BeautifulSoup('<html><a href="/officers/123">Officer 123</a></html>', 'html.parser')
        officer_urls = extract_officer_urls(soup)
        self.assertIn('https://opencorporates.com/officers/123', officer_urls)

    def test_extract_company_id_from_url(self):
        url = 'https://opencorporates.com/companies/us_ut/123456'
        company_id = extract_company_id_from_url(url)
        self.assertEqual(company_id, '123456')

    def test_extract_links(self):
        soup = BeautifulSoup('<html><a href="https://opencorporates.com/page1">Page 1</a></html>', 'html.parser')
        links = extract_links(soup, self.base_url)
        self.assertIn('https://opencorporates.com/page1', links)

    def test_extract_attributes(self):
        soup = BeautifulSoup('<html><dt>Key</dt><dd>Value</dd></html>', 'html.parser')
        attributes = extract_attributes(soup)
        self.assertEqual(attributes['Key'], 'Value')

    def test_extract_assertions(self):
        soup = BeautifulSoup('<html><div class="assertion_group"><h3>Group 1</h3><div class="assertion"><a href="/assertion/1">Title</a><p class="description">Description</p></div></div></html>', 'html.parser')
        assertions = extract_assertions(soup)
        self.assertIn('Group 1', assertions)

    def test_extract_filings(self):
        soup = BeautifulSoup(self.filings_html, 'html.parser')
        filings = extract_filings(soup)
        self.assertGreater(len(filings), 0)

    def test_extract_filings_page_2(self):
        soup = BeautifulSoup(self.filings_html_page_2, 'html.parser')
        filings = extract_filings(soup)
        self.assertGreater(len(filings), 0)

    def test_extract_events(self):
        soup = BeautifulSoup(self.events_html, 'html.parser')
        events = extract_events(soup)
        self.assertGreater(len(events), 0)
        self.assertEqual(events[0]['Date'], 'Before 2019-02-05')

    def test_extract_officers(self):
        soup = BeautifulSoup(self.officers_html, 'html.parser')
        driver = MagicMock()
        officers = extract_officers(soup, self.base_url, driver)
        self.assertGreater(len(officers), 0)
        self.assertEqual(officers[0]['Name'], 'CORPORATION SERVICE COMPANY')

    def test_extract_officers_page_2(self):
        soup = BeautifulSoup(self.officers_html_page_2, 'html.parser')
        driver = MagicMock()
        officers = extract_officers(soup, self.base_url, driver)
        self.assertGreater(len(officers), 0)
        self.assertEqual(officers[0]['Name'], 'ANTHONY M PADINHA')

    def test_extract_relationships(self):
        soup = BeautifulSoup(self.relationships_html, 'html.parser')
        relationships = extract_relationships(soup, 'company_relationship_object')
        self.assertEqual(relationships[0]['Company'], 'Wells Fargo Services Company')

if __name__ == '__main__':
    unittest.main()
