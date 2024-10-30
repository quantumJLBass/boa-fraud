# scraper.py
import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Union
from urllib.parse import urljoin, urlparse

import probablepeople as pp
from bs4 import BeautifulSoup, Tag
from sqlalchemy.exc import IntegrityError

from utils.useollama import *
from utils.ziptest import *
from utils.utils import extract_jurisdiction_from_url,extract_company_number_from_url, random_wait,normalize_textblocks
from services.applogging import logger

from db.cache import (bulk_save_urls, catalog_cache, get_base_url_id,
                      load_cache, url_cached)
from gs import *
from settings.settings import *
from db.dbefclasses import  (Address, Event, Assertion, Attribute, Classification, Company, CompanyAddress, CompanyIndustryCode, CompanyOfficer, Filing, GazetteNotice, IdentifierDelegate, IndustryCode, Jurisdiction, LEIAddress, LEIData, LEIEntityDetail, Link, Officer, PeopleAddress, Person, PersonOfficer, Publication, RelatedRelationship, SubsidiaryRelationship, TotalShare, TrademarkRegistration) #, Base, Event, RoleType,AddressType,  URLCatalog



def ensure_url(
    url: str = None
) -> str:
    """
    Ensures that the given URL is not None and returns it.

    If the URL is None, it sets it to the current URL from the gs object.

    Parameters:
    ----------
    url : str, optional
        The URL to be checked. Defaults to None.

    Returns:
    -------
    str
        The URL that was passed in or the current URL from the gs object.

    Examples:
    ---------
    >>> ensure_url("https://example.com")
    'https://example.com'
    >>> ensure_url(None)
    'https://current.url.from.gs'
    """
    logger.info(f"{i()}🌎ENSURE URL ------ url: {url}")
    if url is None:
        url = gs.current_url
        logger.info(f"{i()}🌎ENSURE URL ------ WAS None now it's url: {url}")
    return url

def warm_cache(
    url: str = None
) -> None:
    """
    Pre-warm the cache by fetching and caching the SOAP objects for the given URL.

    This function initializes the WebDriver, pre-warms the cache for a single URL, and then processes the URL for additional links.

    Args:
        url (str): The URL to be cached.

    Returns:
        None
    """

    url = ensure_url(url)
    company_number = gs.current_company_number
    jurisdiction = gs.current_jurisdiction
    officer_urls = []

    section(f"🗃️🌎⛏️ CACHE WARMING ------ for URL: {url} 🌎⛏️", "yellow1", "center")
    section_soup = None

    logger.debug(f"{i()}📛📛 WRITE {type(gs.write)}")
    logger.debug(f"{i()}📛📛 READ {type(gs.read)}")
    if url_cached(url):
        logger.info(f"{i()}🗃️🌎✅ CACHE WARMING ------ URL already cached: {url}")
        section_soup = load_cache(url)
    else:
        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ for URL: {url}")
        jurisdiction = extract_jurisdiction_from_url(url)
        company_number = extract_company_number_from_url(url)
        section_soup = fetch_html(url)
        catalog_cache(url, section_soup, company_number, jurisdiction)

    if section_soup:
        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ Collecting officer URLs on the current page.")
        officer_urls.extend(extract_officer_urls(section_soup))
        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ Collected {len(officer_urls)} officer URLs.")

        next_page = section_soup.find('a', rel='next nofollow')
        while next_page:
            next_page_url = urljoin(url, next_page['href'])
            next_section_soup = fetch_html(next_page_url)
            officer_urls.extend(extract_officer_urls(next_section_soup))
            logger.info(f"{i()}🗃️🌎⏭️ CACHE WARMING ------ for next page: {next_page_url}")
            catalog_cache(next_page_url, next_section_soup, company_number, jurisdiction)
            logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ Fetched next page: {next_page_url}")

            next_page = next_section_soup.find('a', rel='next nofollow')

    if officer_urls:
        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ officer_urls: {officer_urls}")
        parent_url_id = get_base_url_id(company_number,jurisdiction)
        # Save officer URLs in bulk
        bulk_save_urls(officer_urls, company_number, jurisdiction, parent_url_id)

        # for officer_url in officer_urls:
        #     officer_section_soup = fetch_html(officer_url)
        #     catalog_cache(officer_url, officer_section_soup, company_number, jurisdiction)

def fetch_html(
    url: str
) -> BeautifulSoup:
    """
    Fetches the HTML content of a given URL, filters out unnecessary elements, and returns the parsed content.

    This function uses a web driver to fetch the HTML of a specified URL, checks for specific error patterns in the HTML content,
    and applies a series of filters to clean up the HTML before returning it. The filtering process involves:

    1. Removing the <div> with the class "row prefooter".
    2. Removing all <span> elements with the class "heading-help".
    3. Replacing <a> elements with the class "jurisdiction_filter" if they are within <dd> with the text of the link, otherwise removing them.
    4. Modifying the 'title' attribute of elements that start with "More Free And Open Company Data On ".
    5. Removing the <h3> element under the element with id "similarly_named".
    6. Removing links with `href` attributes ending in `exclude_inactive=true`.
    7. Replacing `> <` with `><` to remove extra spaces between HTML tags.
    8. Removing the string `class="container plain_background" id="page_container"`.
    9. Removing the string ` class="vcard" itemscope="" itemtype="http://schema.org/Corporation"`.
    10. Replacing the pattern `<div class="sidebar-item" id="groupings"><h4><span class="define">Corporate Grouping</span><span class="badge badge-info user_contributed small"><a data-original-title="This data has been user contributed" data-placement="top" href="/legal/glossary#user-contributed-data" rel="tooltip">User Contributed</a></span></h4><div class="tags"><div class="add_block"> None known. <a class="new_corporate_grouping_membership add label label-important" data-remote="true" href="/corporate_grouping_memberships/new\\?company_number=.*?" rel="nofollow">Add one now\\?</a></div></div><a href="/corporate_groupings" title="See all Corporate Groupings">See all corporate groupings</a></div>` with an empty string.
    11. Replacing the pattern `<div id="source"><strong>Source </strong><span class="publisher">.*?</span>, <a class="url external" href=".*?">.*?</a>, <span class="retrieved">.*?</span></div>` with an empty string.
    12. Replacing the pattern `title=".*?">` with `>`.
    13. Replacing the pattern `<dd class="registry_page"><a class="url external" href=".*?</a></dd>` with an empty string.
    14. Removing elements that are empty or contain only whitespace.
    15. Standardizing the HTML output by removing extra whitespace and formatting.
    16. Detecting and handling pages with no data by checking for an empty <tbody> and returning a "NO DATA" message.

    Args:
        url (str): The URL to fetch and cache.

    Returns:
        BeautifulSoup: The parsed and filtered content of the page, wrapped in a BeautifulSoup object,
                    or a simple message if no data is found.

    Raises:
        Exception: If the content contains specific error patterns like forbidden access or rate limiting.
    """
    forbidden_pattern = r'\u003Ctitle>Forbidden\u003C/title>\n    \u003Cmeta name="description" content="Request is denied'
    rate_limit_pattern = r'It appears this IP address may be accessing OpenCorporates at a higher than expected rate.'

    logger.info(f"{i()}🌎 Fetching URL: {url}")
    gs.current_driver.get(url)
    random_wait(1, 1)  # Wait for JavaScript to load

    if gs.current_driver.current_url != url:
        logger.error(f"{i()}🛑🧺🚨🚩FETCHING FAIL --- Redirected to URL? {url} wanted but pulled from {gs.current_driver.current_url}")
        return None

    page_source = gs.current_driver.page_source

    if re.search(forbidden_pattern, page_source):
        raise Exception(f"{i()}🛑🧺🚨🚩❌‼️‼️ FETCHING FAIL --- FORBIDDEN Request is denied at URL {url}")

    if re.search(rate_limit_pattern, page_source):
        raise Exception(f"{i()}🛑🧺🚨🚩FETCHING FAIL --- RATE LIMITED or rate limit content detected at URL {url}")

    soup = BeautifulSoup(page_source, 'html.parser')

    # Isolate the content within id="page_container"
    page_container = soup.find(id='page_container')
    if not page_container:
        logger.error(f"Page container with id='page_container' not found for URL {url}")
        return None

    # Filtering logic starts here
    # 1. Remove <div class="row prefooter">
    if prefooter_div := page_container.find('div', class_='row prefooter'):
        prefooter_div.decompose()

    # 2. Remove <span class="heading-help">
    for span in page_container.find_all('span', class_='heading-help'):
        span.decompose()

    # 3. Handle <a> elements with the class "jurisdiction_filter" within <dd>
    for link in page_container.find_all('a', class_='jurisdiction_filter'):
        if link.find_parent('dd'):
            link.find_parent('dd').replace_with(f'<dd>{link.get_text()}</dd>')
        else:
            link.decompose()

    # 4. Modify the title attribute
    for tag in page_container.find_all(title=re.compile(r'^More Free And Open Company Data On ')):
        new_title = re.sub(r'^More Free And Open Company Data On ', '', tag['title'])
        tag['title'] = new_title

    # 5. Remove the <h3> under #similarly_named
    if (samesection := page_container.find(id='similarly_named')) and (section_h3 := samesection.find('h3')):
        section_h3.decompose()

    # 6. Remove links with href ending in 'exclude_inactive=true'
    for link in page_container.find_all('a', href=True):
        if link['href'].endswith('exclude_inactive=true'):
            link.decompose()

    # 7. Replace `> <` with `><`
    standardized_html = re.sub(r'>\s+<', '><', str(page_container))

    # 8. Remove the string `class="container plain_background" id="page_container"`
    standardized_html = re.sub(r'class="container plain_background" id="page_container"', '', standardized_html)

    # 9. Remove the string ` class="vcard" itemscope="" itemtype="http://schema.org/Corporation"`
    standardized_html = re.sub(r' class="vcard" itemscope="" itemtype="http://schema.org/Corporation"', '', standardized_html)

    # 10. Remove the pattern for Corporate Groupings
    standardized_html = re.sub(
        r'<div class="sidebar-item" id="groupings"><h4><span class="define">Corporate Grouping</span><span class="badge badge-info user_contributed small"><a data-original-title="This data has been user contributed" data-placement="top" href="/legal/glossary#user-contributed-data" rel="tooltip">User Contributed</a></span></h4><div class="tags"><div class="add_block"> None known. <a class="new_corporate_grouping_membership add label label-important" data-remote="true" href="/corporate_grouping_memberships/new\\?company_number=.*?" rel="nofollow">Add one now\\?</a></div></div><a href="/corporate_groupings" title="See all Corporate Groupings">See all corporate groupings</a></div>',
        '', standardized_html
    )

    # 11. Remove the pattern for Source
    standardized_html = re.sub(
        r'<div id="source"><strong>Source </strong><span class="publisher">.*?</span>, <a class="url external" href=".*?">.*?</a>, <span class="retrieved">.*?</span></div>',
        '', standardized_html
    )

    # 12. Replace the pattern `title=".*?">` with `>`
    standardized_html = re.sub(r'title=".*?">', '>', standardized_html)

    # 13. Remove the pattern for registry page links
    standardized_html = re.sub(
        r'<dd class="registry_page"><a class="url external" href=".*?</a></dd>',
        '', standardized_html
    )

    # 14. Remove empty elements or elements with only whitespace recursively
    def remove_empty_elements(soup):
        empty_elements_found = True
        while empty_elements_found:
            empty_elements_found = False
            for element in soup.find_all(True):  # Find all tags
                if not element.text.strip() and not element.contents:
                    element.decompose()
                    empty_elements_found = True

    soup = BeautifulSoup(standardized_html, 'html.parser')
    remove_empty_elements(soup)

    # 15. Standardize the HTML output by removing extra whitespace and formatting
    standardized_html = re.sub(r'\s+', ' ', str(soup)).strip()

    # 16. Detect empty data page
    if (tbody := soup.find('tbody')) and not tbody.find_all(True):
        if len(standardized_html) < 1000:  # Arbitrary small length, adjust as needed
            standardized_html = '<h1>NO DATA</h1>'

    return BeautifulSoup(standardized_html, 'html.parser')
# The function fetch_html now focuses on the content within #page_container and applies the filtering there.

def load_html_content(
    url: str = None,
    attempt: int = 1
) -> BeautifulSoup:
    """
    Loads the HTML content of a given URL, checking the cache first and caching the content if not cached.

    Args:
        url (str): The URL to load.
        attempt (int): The current attempt number, for retrying on failure.

    Returns:
        BeautifulSoup: A BeautifulSoup object containing the parsed HTML content.
    """
    try:
        url = ensure_url(url)
        # Check if URL is cached
        if url_cached(url):
            logger.info(f"🔧🗃️ LOADING CACHE ----- Loading cached content for URL: {url}")
            return load_cache(url)

        # Fetch content if not cached
        logger.info(f"🔧🌐 FETCHING CONTENT ----- Fetching content for URL: {url}")
        # soup = fetch_html(url)

        # opening() we open/close on every 20th url
        warm_cache()
        # exiting()
        if url_cached(url):
            logger.info(f"🔧🗃️ LOADING CACHE ----- Loading cached content for URL: {url}")
            return load_cache(url)

        # return soup
    except Exception as e:
        logger.error(f"💥🚩 Error for URL {url}: {e}", exc_info=True)
        logger.error(f"{traceback.format_exc()}")
        if attempt < 3:
            logger.info(f"🔧🌐 RETRYING ----- Retrying ({attempt + 1}/3) for URL: {url}")
            return load_html_content(url, attempt + 1)
        else:
            logger.error(f"💥🚩 Failed to fetch URL {url} after 3 attempts")
            return None

def scrape_data(
    url: str = None
) -> dict:
    """
    Scrapes data from the given URL using the provided WebDriver.

    Args:
        url (str): The URL to scrape data from.

    Returns:
        dict: A dictionary containing the scraped data.

    Raises:
        None.

    This function scrapes data from the given URL using the provided WebDriver. It first logs the URL being scraped.
    It then fetches and parses the main content of the page. If the main content is found, it extracts links, the company name,
    attributes, and assertions from the parsed content. It then iterates over a list of URL patterns and for each pattern,
    it fetches and parses the corresponding section of the page. It extracts items from the section based on the pattern
    and appends them to a list. It continues this process until there are no more next pages. Finally, it returns the
    scraped data as a dictionary.

    Example usage:
    ```
    url = "https://example.com"
    data = scrape_data(url)
    ```
    """

    # logger.debug(f"{i()}📛📛 WRITE {type(gs.write)}")
    # logger.debug(f"{i()}📛📛 READ {type(gs.read)}")
    url = ensure_url(url)
    section("⛏️🖨️ SCRAPING THE URL 🖨️⛏️", "sea_green2", "center")
    section(f"Scraping URL: {url}", "chartreuse4", "center")
    data = {}

    soup = load_html_content(url)

    if not soup:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩SCRAPPING ISSUE--- Main content not found.")
        return data

    url_parts = urlparse(url).path.strip('/').split('/')

    if url_parts[0] == 'companies' and len(url_parts) == 3:
        # Base company URL
        logger.info(f"{i()}⛏️🖨️ SCRAPPING --- Extracting company data from base URL")
        data.update(extract_company_data(soup))
        data['Links'] = extract_links(soup, url)

        attributes_element = soup.find('dl', class_='attributes')
        if attributes_element:
            data['Attributes'] = extract_attributes(attributes_element)
        else:
            logger.debug(f"{i()}⛏️🖨️ SCRAPPING ISSUE --- Attributes section not found.")

        # Extract assertions
        assertions_element = soup.find('div', id='assertions')
        if assertions_element:
            data['Assertions'] = extract_assertions(assertions_element)
        else:
            logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩SCRAPPING ISSUE --- Assertions section not found.")

    elif url_parts[0] == 'companies' and len(url_parts) > 3:
        # Company sub-URL
        section_type = url_parts[-1]
        logger.info(f"{i()}⛏️🖨️ SCRAPPING --- Extracting data for section: {section_type}")

        if "filings" in section_type:
            data['Filings'] = extract_filings(soup)
        elif "events" in section_type:
            data['Events'] = extract_events(soup)
        elif "officers" in section_type:
            data['Officers'] = extract_officers(soup)
        elif "gazette_notices" in section_type:
            data['Gazette_Notices'] = extract_gazette_notices(soup)
        elif "total_shares" in section_type:
            data['Total_Shares'] = extract_total_shares(soup)
        elif any(rel_type in section_type for rel_type in ["branch", "subsidiary", "parent"]):
            data['Relationships'] = extract_relationships(soup, section_type)
        else:
            logger.warning(f"{i()}⛏️🖨️ 🛑🚨🚩SCRAPPING ISSUE --- Unknown section type: {section_type}")

    elif url_parts[0] == 'officers':
        # Officer URL
        logger.info(f"{i()}⛏️🖨️ SCRAPPING --- Extracting officer data")
        data['Officer'] = extract_officers(soup)

    else:
        logger.warning(f"{i()}⛏️🖨️ 🛑🚨🚩SCRAPPING ISSUE --- Unexpected URL structure: {url}")

    # Check for pagination
    next_page = soup.find('a', rel='next nofollow')
    if next_page:
        next_page_url = urljoin(url, next_page['href'])
        logger.info(f"{i()}⛏️🖨️ SCRAPPING --- Found next page: {next_page_url}")
        data.update(scrape_data(next_page_url))  # Recursively call scrape_data

    logger.debug(f"{i()}⛏️🖨️ SCRAPPING --- Scraped data: {data}")

    return data

def extract_officer_urls(
    soup: Union[BeautifulSoup, Tag]
) -> List[str]:
    """
    Extracts officer URLs from the given soup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the page source.

    Returns:
        List[str]: A list of officer detail URLs.
    """
    soup_copy = copy.deepcopy(soup)
    officer_urls = []
    if focused := soup_copy.find('div', class_='sidebar'):
        focused.decompose()
    officer_elements = soup_copy.find_all('a', href=True)
    for element in officer_elements:
        href = element['href']
        logger.info(f"{i()}🌎 CACHE WARMING ------ officer link found: {href}")
        if "/officers/" in href:
            officer_urls.append(urljoin(gs.current_url, href))
    logger.info(f"{i()}🌎 CACHE WARMING ------ all the links: {officer_urls}")
    return officer_urls

def extract_company_data(
    soup: Union[BeautifulSoup, Tag]
) -> Dict[str, Union[str, Dict[str, str], List[Dict[str, str]]]]:
    """
    Extracts company data from a given BeautifulSoup object representing a company's HTML page.

    Parameters:
    ----------
    soup : BeautifulSoup or Tag
        The BeautifulSoup object representing the HTML document.

    Returns:
    -------
    dict
        A dictionary containing the extracted company data, including the company name, attributes, and assertions.

    This function takes a BeautifulSoup object as input and extracts company data from it. It identifies and extracts
    the company name, attributes, and other relevant data, and saves the company data to the database if it does not
    already exist.

    Example usage:
    ----------
    soup = BeautifulSoup(html_content, 'html.parser')
    company_data = extract_company_data(soup)
    print(company_data)
    """
    section("SCRAPING COMPANY DATA")
    # logger.debug(f"{i()}📛📛 WRITE {type(gs.write)}")
    # logger.debug(f"{i()}📛📛 READ {type(gs.read)}")
    company_data = {}

    if not soup or not hasattr(soup, 'find_all'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩COMPANY DATA -- Invalid soup object in extract_company_data.")
        return company_data

    logger.debug(f"{i()}⛏️🖨️ COMPANY DATA -- Extracting data from the company page")

    # Extract the company name
    name_element = soup.find('h1', class_="wrapping_heading")
    logger.debug(f"{i()}⛏️🖨️ COMPANY DATA -- Company Name element: {str(name_element)[:750]}")
    if name_element:
        company_name = name_element.text.replace('\n', ' ').replace('branch', 'BRANCH').strip()
        company_name += f" ({gs.current_jurisdiction} - {gs.current_company_number})"
        logger.debug(f"{i()}⛏️🖨️ COMPANY DATA -- Company Name: {company_name}")
        company_data['Company Name'] = company_name

    # Extract attributes
    attributes_element = soup.find('dl', class_='attributes')
    logger.debug(f"{i()}⛏️🖨️ COMPANY DATA -- Attributes element: {attributes_element}")
    if attributes_element:

        # logger.debug(f"{i()}📛📛 WRITE {type(gs.write)}")
        # logger.debug(f"{i()}📛📛 READ {type(gs.read)}")
        attributes = extract_attributes(attributes_element)
        company_data['Attributes'] = attributes
    else:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩COMPANY DATA ISSUE -- Attributes section not found.")
        attributes = {}

    # Extract specific company details
    status = attributes.get('Status', '')
    incorporation_date = attributes.get('Incorporation Date', '')
    company_type = attributes.get('Company Type', '')
    jurisdiction = attributes.get('Jurisdiction', '')

    # Get jurisdiction_id
    logger.info(f"{i()} the type of gs.read: {type(gs.read)}")
    logger.info(f"{i()} the type of Jurisdiction: {type(Jurisdiction)}")
    jurisdiction_record = None
    with gs.read() as readsession:
        jurisdiction_record = readsession.query(Jurisdiction).filter_by(name=jurisdiction).one_or_none()
        jurisdiction_id = jurisdiction_record.id if jurisdiction_record else None

    # Save company data to the database using Company model
    company_data = {
        'company_number': gs.current_company_number,
        'company_name': company_name,
        'status': status,
        'incorporation_date': incorporation_date,
        'company_type': company_type,
        'jurisdiction_id': jurisdiction_id,
        'jurisdiction': jurisdiction_record
    }
    company = Company(**company_data)
    company.catalog_record(data=company_data)
    logger.info(f"{i()}🏢📊 COMPANY DATA -- Company data saved to database: {company_name}")

    return company_data

def extract_links(
    content: Union[BeautifulSoup, Tag],
    main_url: str
) -> List[str]:
    """
    Extracts and filters links from the given BeautifulSoup content.

    This function processes the given BeautifulSoup object to extract links from <a> tags.
    It filters out the main URL and links that match any exclude patterns.

    Args:
        content (BeautifulSoup): The HTML content to extract links from.
        main_url (str): The main URL to exclude from the extracted links.

    Returns:
        list: A list of filtered links.

    Raises:
        None, but logs any errors encountered during the extraction process.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <div>
        ...   <a href="https://example.com/page1">Page 1</a>
        ...   <a href="https://example.com/page2">Page 2</a>
        ...   <a href="https://example.com">Main</a>
        ...   <a href="mailto:someone@example.com">Email</a>
        ... </div>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_links(soup, "https://example.com")
        ['https://example.com/page1', 'https://example.com/page2']
    """
    section("SCRAPING LINKS")
    if not content or not hasattr(content, 'find_all'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩LINKS -- Invalid content object in extract_links.")
        return []

    logger.debug(f"{i()}⛏️🖨️ LINKS -- Extracting links from content string {len(content.text) if content else 0} long")
    logger.debug(f"{i()}⛏️🖨️ LINKS -- Extracting from {content.prettify()}")

    links = {link['href'] for link in content.find_all('a', href=True)
            if link['href'] and link['href'] != main_url
            and not any(re.match(pattern, link['href']) for pattern in EXCLUDE_PATTERNS)}

    if not links:
        logger.debug(f"{i()}🛑🚨🚩LINKS -- No links extracted.")
    else:

        for link in links:
            full_url = urljoin(main_url, link)

            # Use catalog_record to handle insertion or update
            link_data = {
                'company_number': gs.current_company_number,
                'link': full_url
            }
            link = Link(**link_data)
            link.catalog_record(data=link_data)
            logger.debug(f"{i()}🔗 LINKS -- Cataloged link in Link table: {full_url}")

    return list(links)

def extract_attributes(
    attributes: Union[BeautifulSoup, Tag]
) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Extracts attributes from a BeautifulSoup object representing a section of HTML with <dt> and <dd> tags.

    This function processes each <dt> (definition term) and corresponding <dd> (definition description) pair found within the
    given `attributes` section. It normalizes the text content of each <dd> tag, ensuring that text blocks are clean and
    formatted properly. If a <dd> tag contains address information, it joins the address lines with a comma and a space.
    If a <dd> tag contains a list (<ul>), it extracts the list items (<li>), joins them with a space, and ensures proper
    spacing between each list item. The function also handles the "Branch" attribute, renaming it to "Parent", extracting
    the company name and URL, and formatting them appropriately.

    Args:
        attributes (BeautifulSoup): A BeautifulSoup object representing the section of HTML containing <dt> and <dd> tags.

    Returns:
        dict: A dictionary where each key is the text of a <dt> tag and the corresponding value is either a string or a dictionary.
            If the <dd> tag contains address information, the address lines are joined with a comma and a space.
            If the <dd> tag contains a list, the list items are joined with a space.
            If the <dt> tag is "Branch", the key is renamed to "Parent" and the value is a dictionary with the company name and URL.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <dl class="attributes">
        ...   <dt>Inactive Directors / Officers</dt>
        ...   <dd>
        ...     <ul>
        ...       <li>S CRAIG ADAMS, member</li>
        ...       <li>SCOTT CARLSTON, agent</li>
        ...       <li>SCOTT CARLSTON, member</li>
        ...       <li>SCOTT CARLSTON, registered agent</li>
        ...     </ul>
        ...   </dd>
        ... </dl>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> attributes = soup.find('dl', class_='attributes')
        >>> extract_attributes(attributes)
        {'Inactive Directors / Officers': 'S CRAIG ADAMS, member SCOTT CARLSTON, agent SCOTT CARLSTON, member SCOTT CARLSTON, registered agent'}

    Notes:
        - This function assumes that each <dt> tag has a corresponding <dd> tag within the `attributes` section.
        - The function utilizes helper functions `normalize_textblocks` and `normalize_address` to ensure text consistency.
        - If the text content of a <dd> tag includes address information, additional normalization is performed to standardize the address format.
    """
    section("SCRAPING ATTRIBUTES")
    if not attributes or not hasattr(attributes, 'find_all'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩ATTRIBUTES -- Invalid attributes object in extract_attributes.")
        return {}

    logger.debug(f"{i()}⛏️🖨️ ATTRIBUTES -- Extracting data from attributes string {len(attributes.text) if attributes else 0} long")
    logger.debug(f"{i()}⛏️🖨️ ATTRIBUTES -- Extracting from {str(attributes.prettify())[:35]}")

    data = {}

    for dt, dd in zip(attributes.find_all('dt'), attributes.find_all('dd')):
        dt_text = dt.text.strip()

        if not dt_text or dt_text in ['Company Number', 'Jurisdiction']:
            continue  # Skip 'Company Number' and 'Jurisdiction'

        if 'Incorporation Date' in dt_text or 'Dissolution Date' in dt_text:
            # Use regex to extract date in 'DD Month YYYY' format and convert it to 'YYYY-MM-DD'
            date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', dd.text)
            if date_match:
                day, month, year = date_match.groups()
                # Convert to YYYY-MM-DD format
                month = month[:3]  # Abbreviate month to the first 3 letters
                month_number = datetime.strptime(month, '%b').month
                dd_text = f"{year}-{month_number:02d}-{int(day):02d}"
            else:
                dd_text = ''  # Handle the case where the date format is unexpected

        elif 'Address' in dt_text:
            parts_of_address = [part for part in dd.stripped_strings]
            dd_text = ', '.join(parts_of_address)
            # dd_text = normalize_address(dd_text)
            catalog_address_record(dd_text)

        elif dd.find('ul'):
            dd_text = ' '.join([li.text.strip() for li in dd.find_all('li')])
        else:
            dd_text = normalize_textblocks(dd.text)

        if 'Branch' in dt_text:
            a_tag = dd.find('a')
            if a_tag:
                company_name = a_tag.text.strip().replace(' (US)', '').replace('Branch of ','')
                company_url = a_tag['href']
            else:
                company_name, company_url = dd.text.strip().replace('Branch of ',''), ''
            data['Parent'] = {'company_name': company_name, 'url': company_url}

            # Save parent company information
            # company_data = {
            #     'company_name': company_name,
            #     'company_number': gs.current_company_number,
            #     'jurisdiction': gs.current_jurisdiction,  # extract_jurisdiction_from_url(company_url)
            # }
            # company = Company(**company_data)
            # company.catalog_record(data=company_data)
        else:
            data[dt_text] = dd_text

        attribute_data = {
            'company_number': gs.current_company_number,
            'name': dt_text,
            'value': dd_text
        }
        attribute = Attribute(**attribute_data)
        attribute.catalog_record(data=attribute_data)

    if not data:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩ATTRIBUTES -- No attributes extracted.")

    return data

def extract_assertions(
    assertions: Union[BeautifulSoup, Tag]
) -> Dict[str, List[Dict[str, str]]]:
    """
    Extracts assertions information from a BeautifulSoup object representing a section of HTML with assertions data.

    This function processes the given BeautifulSoup object to extract assertions information.
    If the object is invalid, it returns an empty dictionary.

    Args:
        assertions (BeautifulSoup): A BeautifulSoup object representing the section of HTML with assertions data.

    Returns:
        dict: A dictionary where each key is the name of an assertion group, and the corresponding value is a list of dictionaries representing the assertions in that group. Each assertion dictionary contains the following keys:
            - "Title" (str): The title of the assertion.
            - "Link" (str): The link of the assertion.
            - "Description" (str): The description of the assertion.
    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <div class="assertion_group">
        ...   <h3>Group 1</h3>
        ...   <div class="assertion">
        ...     <a href="/assertion/1">Assertion Title 1</a>
        ...     <p class="description">Description 1</p>
        ...   </div>
        ...   <div class="assertion">
        ...     <a href="/assertion/2">Assertion Title 2</a>
        ...     <p class="description">Description 2</p>
        ...   </div>
        ... </div>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_assertions(soup)
        {'Group 1': [{'Title': 'Assertion Title 1', 'Link': '/assertion/1', 'Description': 'Description 1'},
                    {'Title': 'Assertion Title 2', 'Link': '/assertion/2', 'Description': 'Description 2'}]}
    """
    section("SCRAPING ASSERTIONS")
    if not assertions or not hasattr(assertions, 'find_all'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩ASSERTIONS -- Invalid assertions object in extract_assertions.")
        return {}

    logger.debug(f"{i()}⛏️🖨️ ASSERTIONS -- Extracting data out of a string {len(assertions.text) if assertions else 0} long")
    logger.debug(f"{i()}⛏️🖨️ ASSERTIONS -- Extracting from {assertions.prettify()}")

    data = {}


    groups = assertions.find_all('div', class_='assertion_group')
    for group in groups:
        group_name = group.find('h3').text.strip()
        assertions_list = []
        for assertion in group.find_all('div', class_='assertion'):
            title_element = assertion.find('a')
            title = title_element.text.strip() if title_element else ''
            link = urljoin(gs.current_url, title_element['href']) if title_element else ''
            description_element = assertion.find('p', class_='description')
            description = description_element.text.strip() if description_element else ''

            if 'Address' in title:
                catalog_company_address(gs.current_company_number, description)
                description = normalize_address(description)

            assertion_data = {
                'company_number': gs.current_company_number,
                'title': title,
                'link': link,
                'description': description
            }
            assertion = Assertion(**assertion_data)
            assertion.catalog_record(data=assertion_data)

        if not assertions_list:
            logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩ASSERTIONS -- No assertions found in group {group_name}")

        data[group_name] = assertions_list

    if not data:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩ASSERTIONS -- No assertions extracted.")

    return data

def extract_filings(
    soup: Union[BeautifulSoup, Tag]
) -> List[Dict[str, str]]:
    """
    Extracts filing information from a BeautifulSoup object representing a section of HTML with filing data.

    This function processes the given BeautifulSoup object to extract filing information and saves it to the database.
    If the object is invalid or contains the message 'Sorry, no filings for', it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with filing data.

    Returns:
        list: A list of dictionaries containing the extracted filing information, where each dictionary represents a filing.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <div class="filing">
        ...     <div class="dateline">2023-01-01</div>
        ...     <div class="subhead">Filing description</div>
        ... </div>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_filings(soup)
        [{'Date': '2023-01-01', 'Description': 'Filing description', 'Link': ''}]
    """
    section("SCRAPING FILINGS")
    if not soup or not hasattr(soup, 'find_all'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩FILINGS -- Invalid soup object in extract_filings.")
        return []
    if 'Sorry, no filings for' in soup.text:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩FILINGS -- No filings found.")
        return []

    logger.debug(f"{i()}⛏️🖨️ FILINGS -- Extracting data out of a string {len(soup.text)} long")
    logger.debug(f"{i()}⛏️🖨️ FILINGS -- Extracting from {soup.prettify()}")

    filings = []

    for item in soup.find_all('div', class_='filing'):
        date_element = item.find('div', class_='dateline')
        link_element = item.find('a')
        description_element = item.find('div', class_='subhead')
        date = date_element.text.strip() if date_element else ''
        link = urljoin(gs.current_url, link_element['href']) if link_element else ''
        description = description_element.text.strip() if description_element else ''

        filing_data = {
            'company_number': gs.current_company_number,
            'date': date,
            'description': description,
            'link': link
        }
        filing = Filing(**filing_data)
        filing.catalog_record(data=filing_data)
        filings.append(filing)
        logger.debug(f"{i()}🗃️ FILINGS -- Saved filing to database: {date} - {description}")

    if not filings:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩FILINGS -- No filings extracted.")
    else:
        logger.info(f"{i()}⛏️🖨️ FILINGS -- Extracted and saved {len(filings)} filings.")

    return filings

def extract_events(
    soup: Union[BeautifulSoup, Tag]
) -> List[Dict[str, str]]:
    """
    Extracts events information from a BeautifulSoup object representing a section of HTML with events data.

    This function processes the given BeautifulSoup object to extract event information.
    If the object is invalid or there is a mismatch between the number of <dt> and <dd> tags, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with events data.

    Returns:
        list: A list of dictionaries containing the extracted event information, where each dictionary represents an event.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <dl>
        ...   <dt>2023-01-01</dt>
        ...   <dd><a href="https://example.com/event">Event description</a></dd>
        ... </dl>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_events(soup)
        [{'Date': '2023-01-01', 'Description': 'Event description', 'Link': 'https://example.com/event'}]
    """
    section("SCRAPING COMPANY EVENTS")
    if not soup or not hasattr(soup, 'find'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩COMPANY EVENTS -- Invalid soup object in extract_events.")
        return []

    logger.debug(f"{i()}⛏️🖨️ COMPANY EVENTS -- Extracting data out of a string {len(soup.text) if soup else 0} long")
    logger.debug(f"{i()}⛏️🖨️ COMPANY EVENTS -- Extracting from {soup.prettify()[:750]}")

    events = []

    event_list = soup.find('dl', class_='oc-events-timeline')
    if event_list:
        dt_elements = event_list.find_all('dt')
        dd_elements = event_list.find_all('dd')

        for dt, dd in zip(dt_elements, dd_elements):
            date = dt.text.strip().replace('On ', '')
            description = dd.text.strip()
            link = dd.find('a')['href'] if dd.find('a') else None

            event_data = {
                'company_number': gs.current_company_number,
                'start_date': date,  # Assuming the date is the start date
                'description': description,
                'link': urljoin(gs.current_url, link) if link else None
            }

            # Create an Event object and save it to the database
            event = Event(**event_data)
            event.catalog_record(data=event_data)
            events.append(event)

            logger.debug(f"{i()}🗃️ COMPANY EVENTS -- Saved event to database: {date} - {description}")

        # officer_data = {
        #     'company_number': gs.current_company_number,
        #     'name': name,
        #     'role': role,
        #     'status': status,
        #     'link': urljoin(gs.current_url, link)
        # }

        # # Save officer to the database
        # officer = Officer(**officer_data)
        # officer.catalog_record(data=_data)

            # Catalog the event link URL
            # if link:
            #     catalog_url(event_data['link'], gs.current_company_number, gs.current_jurisdiction, gs.current_url)

    if not events:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩COMPANY EVENTS -- No company events extracted.")

    return events

def extract_officers(
    soup: Union[BeautifulSoup, Tag]
) -> List[Dict[str, str]]:
    """
    Extracts officers information from a BeautifulSoup object representing a section of HTML with officers data.

    This function processes the given BeautifulSoup object to extract officer information.
    If the object is invalid, it returns an empty list.


    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML document.

    Returns:
        list: A list of dictionaries containing information about each officer. Each dictionary has the following keys:
            - 'Name' (str): The name of the officer.
            - 'Role' (str): The role of the officer.
            - 'Status' (str): The status of the officer ('active' or 'inactive').
            - 'Link' (str): The link associated with the officer.
            - 'Start_Date' (str): The start date of the officer's term.
            - 'Address' (str): The address of the officer.
            - 'Type' (str): The type of the officer ('person' or 'corporation').

    Raises:
        None

    Notes:
        - If the input soup object is invalid or does not have the 'find_all' method, an empty list is returned and a debug message is logged.
        - The function iterates over each 'li' element in the soup object and extracts the name, role, status, and link information.
        - If the text of the 'li' element contains a comma, the name and role are extracted using the 'rsplit' method. Otherwise, the entire text is considered as the name.
        - The status is determined based on whether the 'a' element within the 'li' element has the 'inactive' class.
        - The link is extracted from the 'href' attribute of the 'a' element, if it exists.
        - If the link exists, the function fetches the HTML for the officer detail page and extracts the address and name, role, and status.
    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <ul>
        ...   <li><a href="/officer/1">John Doe, CEO</a></li>
        ...   <li><a href="/officer/2" class="inactive">Jane Smith, CFO</a></li>
        ... </ul>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_officers(soup, "https://example.com", driver)
        [{'Name': 'John Doe', 'Role': 'Director', 'Status': 'active', 'Link': 'https://example.com/officer/1', 'Address': '123 Main St', 'Start_Date': '2022-01-01'},
        {'Name': 'Jane Smith', 'Role': 'Manager', 'Status': 'inactive', 'Link': 'https://example.com/officer/2', 'Address': '456 Elm St', 'Start_Date': '2015-11-18'}]
    """
    section("SCRAPING OFFICERS")
    if not soup or not hasattr(soup, 'find_all'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩OFFICERS -- Invalid soup object in extract_officers.")
        return []

    logger.debug(f"{i()}⛏️🖨️ 🧑‍💼OFFICERS -- Extracting data out of a string {len(soup.text) if soup else 0} long")
    logger.debug(f"{i()}⛏️🖨️ 🧑‍💼OFFICERS -- Extracting from {soup.prettify()}")

    officers = []

    for item in soup.find_all('li'):
        text = item.text.strip()
        if "," in text:
            name, role = map(str.strip, text.rsplit(",", 1))
        else:
            name, role = text, ""

        link_element = item.find('a')
        status = 'inactive' if link_element and 'inactive' in link_element.get('class', []) else 'active'
        link = link_element['href'] if link_element else ''
        name = name.upper().replace('.', '')

        officer_data = {
            'company_number': gs.current_company_number,
            'name': name,
            'role': role,
            'status': status,
            'link': urljoin(gs.current_url, link)
        }

        # Save officer to the database
        officer = Officer(**officer_data)
        officer.catalog_record(data=officer_data)

        parsed_pp, pp_type = '', ''
        try:
            parsed_pp, pp_type = pp.tag(name)
            logger.debug(f"{i()}👨🏬〽️✍️Parsed Person Data: {parsed_pp}")
            logger.debug(f"{i()}👨🏬〽️✍️Person Type: {pp_type}")
        except pp.RepeatedLabelError as e:
            logger.error(f"{i()}🔹🚨🚩👨🏬〽️✍️🛑Error in normalize_address (ProbablePeople): {e}")
            logger.error(f"{i()}🔹🚨🚩👨🏬〽️✍️🛑Original String: {e.original_string}")
            logger.error(f"{i()}🔹🚨🚩👨🏬〽️✍️🛑Parsed String: {e.parsed_string}")
            logger.error(traceback.format_exc())

        officer_data['type'] = pp_type

        if pp_type == 'person':
            # Create or update Person record
            person_data = {
                'full_name': name,
                'raw_data': json.dumps(parsed_pp)
            }
            person_data.update(parsed_pp)
            person = Person(**person_data)
            person.catalog_record(data=person_data)

            # Create PersonOfficer relationship
            person_officer_data = {
                'person_id': person.id,
                'officer_id': officer.id
            }
            person_officer = PersonOfficer(**person_officer_data)
            person_officer.catalog_record(data=person_officer_data)
        elif pp_type == 'company':
            # Create or update Company record
            company_data = {
                'company_name': name,
                'jurisdiction': extract_jurisdiction_from_url(officer_data['link'])
            }
            company = Company(**company_data)
            company.catalog_record(data=company_data)

            # Create CompanyOfficer relationship
            company_officer_data = {
                'company_number': company.company_number,
                'officer_id': officer.id
            }
            company_officer = CompanyOfficer(**company_officer_data)
            company_officer.catalog_record(data=company_officer_data)

        # if link exists, fetch and parse for address, name, role, starting date and status
        if link:
            detail_url = urljoin(gs.current_url, link)
            detail_soup = load_html_content(detail_url)
            officer_data['link'] = detail_url
            # Extract address
            address_element = detail_soup.find('dd', class_='address') if detail_soup else None
            address = address_element.text.strip() if address_element else None
            if address:
                if pp_type == 'person':
                    catalog_people_address(address,person.id)
                elif pp_type == 'company':
                    catalog_company_address(address,company.company_number)

            # Extract start date
            start_date_element = detail_soup.find('dd', class_='start_date') if detail_soup else None
            officer_data['start_date'] = start_date_element.text.strip() if start_date_element else None

            # Update officer record with new data
            officer = Officer(**officer_data).catalog_record(data=officer_data)

        officers.append(officer)

    if not officers:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩OFFICERS -- No officers extracted.")

    return officers

def extract_relationships(
    soup: Union[BeautifulSoup, Tag], pattern: str
) -> List[Dict[str, str]]:
    """
    Extracts relationships information from a BeautifulSoup object representing a section of HTML with relationships data.

    This function processes the given BeautifulSoup object to extract relationship information.
    If the object is invalid, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with relationships data.
        pattern (str): The pattern used to identify the relationship type.

    Returns:
        list: A list of dictionaries containing the extracted relationship information, where each dictionary represents a relationship. Each dictionary contains the following keys:
            - 'Company' (str): The name of the company.
            - 'Company ID' (str): The ID of the company.
            - 'Jurisdiction' (str): The jurisdiction of the relationship.
            - 'Status' (str): The status of the relationship.
            - 'Type' (str): The type of the relationship.
            - 'Link' (str): The link associated with the relationship.
            - 'Start Date' (str): The start date of the relationship.
            - 'End Date' (str): The end date of the relationship.
            - 'statement_link' (str): The link to the relationship statement.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <table>
        ...   <tbody>
        ...     <tr>
        ...       <td><a class="company" href="/company/1">Example Company</a></td>
        ...       <td><a class="jurisdiction_filter" href="/jurisdiction/1">Example Jurisdiction</a></td>
        ...       <td><span class="status">Active</span></td>
        ...     </tr>
        ...   </tbody>
        ... </table>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_relationships(soup, "company_relationship_object")
        [{'Company': 'Example Company (Example Jurisdiction - 1)', 'Company ID': '1', 'Jurisdiction': 'Example Jurisdiction', 'Status': 'Active', 'Type': 'Company', 'Link': 'https://example.com/company/1', 'Start Date': '', 'End Date': '', 'statement_link': ''}]
    """
    section("SCRAPING RELATIONSHIPS")
    logger.debug(f"{i()}⛏️🖨️ RELATIONSHIPS -- STARTING Extracting relationships...pattern {pattern}")
    if not soup or not hasattr(soup, 'find'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩RELATIONSHIPS -- Invalid soup object in extract_relationships.")
        return []

    logger.debug(f"{i()}⛏️🖨️ RELATIONSHIPS -- Extracting data out of a string {len(soup.text) if soup else 0} long")
    logger.debug(f"{i()}⛏️🖨️ RELATIONSHIPS -- Extracting from {soup.prettify()}")

    relationships = []
    if 'branch_relationship_object' in pattern:
        relationship_type = 'Parent'
    elif 'branch_relationship_subject' in pattern:
        relationship_type = 'Branch'
    elif 'subsidiary_relationship_object' in pattern:
        relationship_type = 'Parent'
    elif 'subsidiary_relationship_subject' in pattern:
        relationship_type = 'Subsidiary'
    else:
        relationship_type = pattern.split('/')[-1].replace('_relationship_', '').replace('_', ' ').capitalize()

    # company_number = gs.current_company_number
    # jurisdiction = gs.current_jurisdiction


    tbody = soup.find('tbody')
    if not tbody:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩RELATIONSHIPS -- No tbody found in soup.")
        return relationships

    tr_items = tbody.find_all('tr')
    for tr in tr_items:
        company_element = tr.find('a', class_='company')
        status_element = tr.find('span', class_='status')

        if company_element:
            company_name = company_element.text.strip()
            company_url = urljoin(gs.current_url, company_element['href'])
            related_company_id = extract_company_number_from_url(company_url)
            related_jurisdiction = extract_jurisdiction_from_url(company_url)
        else:
            company_text = tr.find('td').text.strip()
            company_name = re.sub(r'\([^)]*\)', '', company_text).strip()
            related_company_id = None
            related_jurisdiction = None
            if '(' in company_text and ')' in company_text:
                related_jurisdiction = company_text.split('(')[-1].split(')')[0]

        status = status_element.text.strip() if status_element else 'Active'

        start_date_element = tr.find('span', class_='start_date')
        end_date_element = tr.find('span', class_='end_date')
        start_date = start_date_element.text.strip() if start_date_element else None
        end_date = end_date_element.text.strip() if end_date_element else None

        statement_element = tr.find_all('td')[-1].find('a')
        statement_link = urljoin(gs.current_url, statement_element['href']) if statement_element else None

        relationship_data = {
            'company_number': gs.current_company_number,
            'related_company': company_name,
            'related_company_id': related_company_id,
            'jurisdiction_code': related_jurisdiction,
            'status': status,
            'type': relationship_type,
            'link': company_url if company_element else None,
            'start_date': start_date,
            'end_date': end_date,
            'statement_link': statement_link
        }


        if relationship_type in ['Parent', 'Branch']:
            relationship = RelatedRelationship(**relationship_data)
            relationship.catalog_record(data=relationship_data)
        elif relationship_type == 'Subsidiary':
            subsidiary_relationship = SubsidiaryRelationship(**relationship_data)
            subsidiary_relationship.catalog_record(data=relationship_data)

        # Catalog URLs
        # if company_url:
        #     catalog_url(company_url, related_company_id, related_jurisdiction, gs.current_url)
        # if statement_link:
        #     catalog_url(statement_link, gs.current_company_number, jurisdiction, gs.current_url)

        relationships.append(relationship_data)

    if not relationships:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩RELATIONSHIPS -- No relationships extracted.")

    return relationships

def extract_identifiers(
    soup: Union[BeautifulSoup, Tag]
) -> List[Dict[str, str]]:
    """
    Extracts identifier information from a BeautifulSoup object representing a table with identifier data.

    This function processes the given BeautifulSoup object to extract identifier information.
    If the object is invalid or there are insufficient columns in a row, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing a table with identifier data.

    Returns:
        list: A list of dictionaries containing the extracted identifier information, where each dictionary represents an identifier.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <tbody>
        ...   <tr>
        ...     <td>Identifier System 1</td>
        ...     <td>12345</td>
        ...     <td>Category 1</td>
        ...   </tr>
        ...   <tr>
        ...     <td>Identifier System 2</td>
        ...     <td>67890</td>
        ...     <td>Category 2</td>
        ...   </tr>
        ... </tbody>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_identifiers(soup)
        [{'company_number': '12345678', 'identifier_system': 'Identifier System 1', 'identifier': '12345', 'categories': 'Category 1'},
         {'company_number': '12345678', 'identifier_system': 'Identifier System 2', 'identifier': '67890', 'categories': 'Category 2'}]
    """
    section("SCRAPING IDENTIFIERS")
    if not soup or not hasattr(soup, 'find'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩IDENTIFIERS -- Invalid soup object in extract_identifiers.")
        return []

    logger.debug(f"{i()}⛏️🖨️ IDENTIFIERS -- Extracting data out of a string {len(soup.text) if soup else 0} long")
    logger.debug(f"{i()}⛏️🖨️ IDENTIFIERS -- Extracting from {soup.prettify()}")

    identifiers = []

    tbody = soup.find('tbody')
    if tbody:
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 3:
                identifier_data = {
                    'company_number': gs.current_company_number,
                    'identifier_system': cells[0].text.strip(),
                    'identifier': cells[1].text.strip(),
                    'categories': cells[2].text.strip()
                }
                identifier = IdentifierDelegate(**identifier_data)
                identifier.catalog_record(data=identifier_data)
                identifiers.append(identifier_data)

    if not identifiers:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩IDENTIFIERS -- No identifiers extracted.")

    return identifiers

def extract_total_shares(
    soup: Union[BeautifulSoup, Tag]
) -> List[Dict[str, str]]:
    """
    Extracts total share information from a BeautifulSoup object representing a table with total share data.

    This function processes the given BeautifulSoup object to extract total share information.
    If the object is invalid or there are insufficient columns in a row, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing a table with total share data.

    Returns:
        list: A list of dictionaries containing the extracted total share information, where each dictionary represents a total share.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <tbody>
        ...   <tr>
        ...     <td>1000</td>
        ...     <td>Share Class 1</td>
        ...   </tr>
        ...   <tr>
        ...     <td>2000</td>
        ...     <td>Share Class 2</td>
        ...   </tr>
        ... </tbody>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_total_shares(soup)
        [{'company_number': '12345678', 'number': '1000', 'share_class': 'Share Class 1'},
         {'company_number': '12345678', 'number': '2000', 'share_class': 'Share Class 2'}]
    """
    section("SCRAPING TOTAL SHARES")
    if not soup or not hasattr(soup, 'find'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩TOTAL SHARES -- Invalid soup object in extract_total_shares.")
        return []

    logger.debug(f"{i()}⛏️🖨️ TOTAL SHARES -- Extracting data out of a string {len(soup.text) if soup else 0} long")
    logger.debug(f"{i()}⛏️🖨️ TOTAL SHARES -- Extracting from {soup.prettify()}")

    total_shares = []

    tbody = soup.find('tbody')
    if tbody:
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                total_share_data = {
                    'company_number': gs.current_company_number,
                    'number': cells[0].text.strip(),
                    'share_class': cells[1].text.strip()
                }
                total_share = TotalShare(**total_share_data)
                total_share.catalog_record(data=total_share_data)
                total_shares.append(total_share_data)

    if not total_shares:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩TOTAL SHARES -- No total shares data extracted.")

    return total_shares

def extract_gazette_notices(
    soup: Union[BeautifulSoup, Tag]
) -> List[Dict[str, str]]:
    """
    Extracts gazette notice information from a BeautifulSoup object representing a table with gazette notice data.

    This function processes the given BeautifulSoup object to extract gazette notice information.
    If the object is invalid or there are insufficient columns in a row, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing a table with gazette notice data.

    Returns:
        list: A list of dictionaries containing the extracted gazette notice information, where each dictionary represents a gazette notice.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <tbody>
        ...   <tr>
        ...     <td>2023-01-01</td>
        ...     <td>Publication 1</td>
        ...     <td>Notice 1</td>
        ...     <td><a href="details_link">Details</a></td>
        ...   </tr>
        ...   <tr>
        ...     <td>2023-01-02</td>
        ...     <td>Publication 2</td>
        ...     <td>Notice 2</td>
        ...     <td><a href="details_link2">Details</a></td>
        ...   </tr>
        ... </tbody>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_gazette_notices(soup)
        [{'company_number': '12345678', 'date': '2023-01-01', 'publication_id': '1', 'notice': 'Notice 1', 'link': 'https://url/details_link', 'classification_id': '1'},
         {'company_number': '12345678', 'date': '2023-01-02', 'publication_id': '2', 'notice': 'Notice 2', 'link': 'https://url/details_link2', 'classification_id': '2'}]
    """
    section("SCRAPING GAZETTE NOTICES")
    if not soup or not hasattr(soup, 'find'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩GAZETTE NOTICES -- Invalid soup object in extract_gazette_notices.")
        return []

    logger.debug(f"{i()}⛏️🖨️ GAZETTE NOTICES -- Extracting data out of a string {len(soup.text) if soup else 0} long")
    logger.debug(f"{i()}⛏️🖨️ GAZETTE NOTICES -- Extracting from {soup.prettify()}")

    notices = []

    tbody = soup.find('tbody')
    if tbody:
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 4:
                pub_name = cells[1].text.strip()
                publication_company_record= None
                with gs.read() as readsession:
                    publication_company_record = readsession.query(Company).filter_by(name=pub_name).first()

                publication_data = {
                    'name': pub_name,
                    'company_number': publication_company_record.company_number if publication_company_record else None
                }
                publication = Publication(**publication_data)
                publication.catalog_record(data=publication_data)

                class_name = cells[3].text.strip() if cells[3].text.strip() else None
                classification = Classification(**{'classification': class_name}).catalog_record(data={'classification': class_name})

                gazette_notice_data = {
                    'company_number': gs.current_company_number,
                    'date': cells[0].text.strip(),
                    'publication_id': publication.id if publication else None,
                    'notice': cells[2].text.strip(),
                    'link': urljoin(gs.current_url, details_link['href']) if (details_link := cells[-1].find('a')) else None,
                    'classification_id': classification.id if classification else None
                }
                gazette_notice = GazetteNotice(**gazette_notice_data)
                gazette_notice.catalog_record(data=gazette_notice_data)
                notices.append(gazette_notice_data)

    if not notices:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩GAZETTE NOTICES -- No gazette notices extracted.")

    return notices

def extract_trademarks(
    soup: Union[BeautifulSoup, Tag]
) -> List[Dict[str, str]]:
    """
    Extracts trademark information from a BeautifulSoup object representing a table with trademark data.

    This function processes the given BeautifulSoup object to extract trademark information.
    If the object is invalid or there are insufficient columns in a row, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing a table with trademark data.

    Returns:
        list: A list of dictionaries containing the extracted trademark information, where each dictionary represents a trademark.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <tbody>
        ...   <tr>
        ...     <td>Trademark 1</td>
        ...     <td>2023-01-01</td>
        ...     <td>Registered</td>
        ...   </tr>
        ...   <tr>
        ...     <td>Trademark 2</td>
        ...     <td>2023-01-02</td>
        ...     <td>Cancelled</td>
        ...   </tr>
        ... </tbody>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_trademarks(soup)
        [{'company_number': '12345678', 'trademark': 'Trademark 1', 'registration_date': '2023-01-01', 'status': 'Registered'},
         {'company_number': '12345678', 'trademark': 'Trademark 2', 'registration_date': '2023-01-02', 'status': 'Cancelled'}]
    """
    section("SCRAPING TRADEMARKS")
    if not soup or not hasattr(soup, 'find'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩TRADEMARKS -- Invalid soup object in extract_trademarks.")
        return []

    logger.debug(f"{i()}⛏️🖨️ TRADEMARKS -- Extracting data out of a string {len(soup.text) if soup else 0} long")
    logger.debug(f"{i()}⛏️🖨️ TRADEMARKS -- Extracting from {soup.prettify()}")

    trademarks = []

    tbody = soup.find('tbody')
    if tbody:
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 3:
                trademark_data = {
                    'company_number': gs.current_company_number,
                    'trademark': cells[0].text.strip(),
                    'registration_date': cells[1].text.strip(),
                    'status': cells[2].text.strip()
                }
                trademark = TrademarkRegistration(**trademark_data)
                trademark.catalog_record(data=trademark_data)
                trademarks.append(trademark_data)

    if not trademarks:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩TRADEMARKS -- No trademarks extracted.")

    return trademarks

def extract_lei_data(
    soup: Union[BeautifulSoup, Tag]
) -> Dict[str, Any]:
    """
    Extracts LEI (Legal Entity Identifier) data from the provided BeautifulSoup object.

    :param soup: A BeautifulSoup object containing the HTML content to extract LEI data from.
    :type soup: Union[BeautifulSoup, Tag]
    :return: A dictionary containing LEI data.
    :rtype: Dict[str, Any]
    """
    section("SCRAPING LEI DATA")
    if not soup or not hasattr(soup, 'find'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩LEI DATA -- Invalid soup object in extract_lei_data.")
        return {}

    logger.debug(f"{i()}⛏️🖨️ LEI DATA -- Extracting data out of a string {len(soup.text) if soup else 0} long")
    logger.debug(f"{i()}⛏️🖨️ LEI DATA -- Extracting from {soup.prettify()}")

    lei_data = {}

    lei_element = soup.find('dl', class_='lei-data')
    if lei_element:
        dt_elements = lei_element.find_all('dt')
        dd_elements = lei_element.find_all('dd')

        for dt, dd in zip(dt_elements, dd_elements):
            key = dt.text.strip().lower().replace(' ', '_')
            value = dd.text.strip()
            lei_data[key] = value

        # Save to database
        lei_data_record = LEIData(**{
            'id': lei_data.get('lei'),
            'lei': lei_data.get('lei'),
            'status': lei_data.get('status'),
            'creation_date': lei_data.get('creation_date'),
            'registered_as': lei_data.get('registered_as'),
            'category': lei_data.get('category'),
            'legal_form_id': lei_data.get('legal_form_id'),
            'legal_form_other': lei_data.get('legal_form_other'),
            'associated_lei': lei_data.get('associated_lei'),
            'associated_name': lei_data.get('associated_name'),
            'expiration_date': lei_data.get('expiration_date'),
            'expiration_reason': lei_data.get('expiration_reason'),
            'successor_lei': lei_data.get('successor_lei'),
            'successor_name': lei_data.get('successor_name'),
            'sub_category': lei_data.get('sub_category')
        })
        lei_data_record.catalog_record(data=lei_data_record)

        # Extract and save LEI entity details
        entity_name = lei_data.get('registered_as')
        if entity_name:
            lei_data = {
                'id': lei_data.get('lei'),
                'lei': lei_data.get('lei'),
                'legal_name': entity_name,
                'language': 'en'  # Assuming English, adjust if necessary
            }
            lei_entity_detail = LEIEntityDetail(**lei_data)
            lei_entity_detail.catalog_record(data=lei_data)

        # Extract and save LEI address
        address_element = soup.find('address', class_='lei-address')
        if address_element:
            address_lines = [line.strip() for line in address_element.stripped_strings]
            lei_address_data = {
                'lei': lei_data.get('lei'),
                'address_type': 'registered',  # Assuming registered address, adjust if necessary
                'language': 'en',  # Assuming English, adjust if necessary
                'address_lines': ', '.join(address_lines)
            }
            lei_address = LEIAddress(**lei_address_data)
            lei_address.catalog_record(data=lei_address_data)

    if not lei_data:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩LEI DATA -- No LEI data extracted.")

    return lei_data

def extract_industry_codes(
    soup: Union[BeautifulSoup, Tag]
) -> List[Dict[str, str]]:
    """
    Extracts industry codes from the provided BeautifulSoup object.

    :param soup: A BeautifulSoup object containing the HTML content to extract industry codes from.
    :type soup: Union[BeautifulSoup, Tag]
    :return: A list of dictionaries containing industry code information.
    :rtype: List[Dict[str, str]]
    """
    section("SCRAPING INDUSTRY CODES")
    if not soup or not hasattr(soup, 'find'):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩INDUSTRY CODES -- Invalid soup object in extract_industry_codes.")
        return []

    logger.debug(f"{i()}⛏️🖨️ INDUSTRY CODES -- Extracting data out of a string {len(soup.text) if soup else 0} long")
    logger.debug(f"{i()}⛏️🖨️ INDUSTRY CODES -- Extracting from {soup.prettify()}")

    industry_codes = []


    tbody = soup.find('tbody')
    if tbody:
        for row in tbody.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 3:
                industry_code_data = {
                    'code': cells[0].text.strip(),
                    'description': cells[1].text.strip(),
                    'code_scheme': cells[2].text.strip()
                }
                industry_code = IndustryCode(**industry_code_data)
                industry_code.catalog_record(data=industry_code_data)

                cic = {
                    'company_number': gs.current_company_number,
                    'industry_code_id': industry_code.id
                }
                company_industry_code = CompanyIndustryCode(**cic)
                company_industry_code.catalog_record(data=cic)

                industry_codes.append(industry_code)

    if not industry_codes:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩INDUSTRY CODES -- No industry codes extracted.")

    return industry_codes



md_contents = """
---
tags:
- MOCs
entry-taxonomic-rank: family
---
```folder-overview
id: {ID}
folderPath: ""
title: "{folderName} overview"
showTitle: true
depth: 4
style: list
includeTypes:
- folder
- all
disableFileTag: true
sortBy: name
sortByAsc: true
showEmptyFolders: false
onlyIncludeSubfolders: false
storeFolderCondition: true
showFolderNotes: true
disableCollapseIcon: true
```
"""

def catalog_address_record(
    address: str
) -> int:
    """
    Inserts or updates an address in the database and returns the address ID.

    Args:
        address (str): The address string to be inserted or updated.

    Returns:
        int: The ID of the inserted or existing address.
    """
    normalized_address = normalize_address(address)

    addresses_dir = Path(__file__).resolve().parent.parent.parent / 'addresses-test'
    good_address, address_obj = lookup_zipcode(normalized_address)
    folder_path = Path(addresses_dir) / good_address  # Create a path object for the folder
    subfolder = folder_path / 'files'
    subfolder.mkdir(parents=True, exist_ok=True)  # Create the directory

    # Create the markdown file inside the folder
    markdown_file_path = folder_path / f"{good_address}.md"
    with markdown_file_path.open('w', encoding='utf-8') as file:
        file.write(md_contents)

    address_id = None

    try:
        with gs.write() as writesession:
            # Attempt to insert the address into the database
            writesession.add(address_obj)
            writesession.commit()
            address_id = address_obj.id  # Get the address ID after insertion
            logger.info(f"{i()}✅🏠 ADDRESS INSERTED ----- {folder_path} with ID {address_id}")
    except IntegrityError:
        with gs.write() as writesession:
            writesession.rollback()
            existing_address = writesession.query(Address).filter_by(normalized_address=good_address).first()
            if existing_address:
                address_id = existing_address.id  # Retrieve the ID of the existing address
            logger.info(f"{i()}🔄🏠 ADDRESS EXISTS ----- {folder_path} with ID {address_id}")
        logger.error(f"{traceback.format_exc()}")
    except Exception as e:
        with gs.write() as writesession:
            writesession.rollback()
        logger.error(f"{i()}💥🚩 ERROR INSERTING ADDRESS ----- {folder_path}: {str(e)}")
        logger.error(f"{traceback.format_exc()}")

    return address_id

def catalog_company_address(
    address: str,
    company_number: str
) -> None:
    """
    Catalogs a company address by inserting or updating the address and creating a CompanyAddress record.

    Args:
        address (str): The address string to be cataloged.
        company_number (str): The company number associated with the address.
    """
    address_id = catalog_address_record(address)

    if address_id:
        address_data = {
            'address_id': address_id,
            'company_number': company_number
        }
        company_address = CompanyAddress(**address_data)
        company_address.catalog_record(data=address_data)

def catalog_people_address(
    address: str,
    person_id: int
) -> None:
    """
    Catalogs a person's address by inserting or updating the address and creating a PeopleAddress record.

    Args:
        address (str): The address string to be cataloged.
        person_id (int): The person ID associated with the address.
    """
    address_id = catalog_address_record(address)

    if address_id:
        address_data = {
            'address_id': address_id,
            'person_id': person_id
        }
        people_address = PeopleAddress(**address_data)
        people_address.catalog_record(data=address_data)
