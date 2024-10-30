import copy
import re
import traceback
from typing import List, Optional, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag
from sqlalchemy.exc import IntegrityError

import db
import gs
from services.applogging import logger, section
from services.webdriver import random_wait
from settings.settings import i


def ensure_url(url: str = None) -> str:
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


def warm_cache(url: str = None) -> None:
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
    company_urls = []
    section(
        f"jurisdiction:{jurisdiction} company_number: {company_number}", "red", "center"
    )
    section(f"🗃️🌎⛏️ CACHE WARMING ------ for URL: {url} 🌎⛏️", "yellow1", "center")
    section_soup = None

    if db.cache.url_cached(url):
        logger.info(f"{i()}🗃️🌎✅ CACHE WARMING ------ URL already cached: {url}")
        section_soup = db.cache.load_cache(url)
    else:
        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ for URL: {url}")
        if "officers" not in url:
            if not company_number or not jurisdiction:
                jurisdiction = extract_jurisdiction_from_url(url)
                company_number = extract_company_number_from_url(url)
        else:
            logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ IS AN OFFICERS URL")

        section_soup = fetch_html(url)
        if not company_number or not jurisdiction:
            logger.info(
                f"{i()}🗃️🌎 CACHE WARMING ------ one of these are none; jurisdiction: {jurisdiction} or company_number: {company_number}"
            )
            parent_url = get_parent_url(section_soup)
            jurisdiction = extract_jurisdiction_from_url(parent_url)
            company_number = extract_company_number_from_url(parent_url)

        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ company_number: {company_number}")
        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ jurisdiction: {jurisdiction}")
        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ section_soup: {section_soup}")
        db.cache.catalog_cache(url, section_soup, company_number, jurisdiction)

    if section_soup:
        logger.info(
            f"{i()}🗃️🌎 CACHE WARMING ------ Collecting officer URLs on the current page."
        )
        officer_urls.extend(extract_officer_urls(section_soup))
        company_urls.extend(extract_company_urls(section_soup))
        logger.info(
            f"{i()}🗃️🌎 CACHE WARMING ------ Collected {len(officer_urls)} officer URLs."
        )

        next_page = section_soup.find("a", rel="next nofollow")
        while next_page:
            next_page_url = urljoin(url, next_page["href"])
            next_section_soup = fetch_html(next_page_url)
            if next_section_soup:
                officer_urls.extend(extract_officer_urls(next_section_soup))
                company_urls.extend(extract_company_urls(next_section_soup))
                logger.info(
                    f"{i()}🗃️🌎⏭️ CACHE WARMING ------ for next page: {next_page_url}"
                )
                db.cache.catalog_cache(
                    next_page_url, next_section_soup, company_number, jurisdiction
                )
                logger.info(
                    f"{i()}🗃️🌎 CACHE WARMING ------ Fetched next page: {next_page_url}"
                )

                next_page = next_section_soup.find("a", rel="next nofollow")

    if company_urls:
        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ company_urls: {company_urls}")
        for company_url in company_urls:
            addcompanyurls(company_url)

    if officer_urls:
        parent_url_id = db.cache.get_base_url_id(company_number, jurisdiction)
        logger.info(f"{i()}🗃️🌎 CACHE WARMING ------ officer_urls: {officer_urls}")
        logger.info(
            f"{i()}🔧🗃️ CACHE WARMING BULK SAVING URLS ------ Parent ID: {parent_url_id}"
        )
        logger.info(
            f"{i()}🔧🗃️ CACHE WARMING BULK SAVING URLS ------ Company Number: {company_number}"
        )
        logger.info(
            f"{i()}🔧🗃️ CACHE WARMING BULK SAVING URLS ------ Jurisdiction: {jurisdiction}"
        )
        # Save officer URLs in bulk
        db.cache.bulk_save_urls(
            officer_urls, company_number, jurisdiction, parent_url_id
        )

        # for officer_url in officer_urls:
        #     officer_section_soup = fetch_html(officer_url)
        #     catalog_cache(officer_url, officer_section_soup, company_number, jurisdiction)


def has_data(soup: Union[BeautifulSoup, Tag]) -> bool:
    """_summary_

    Args:
        soup (Union[BeautifulSoup, Tag]): _description_

    Returns:
        bool: _description_
    """
    # if isinstance(html_content, (BeautifulSoup, Tag)):
    #     html_content = str(html_content)
    # elif not isinstance(html_content, str):
    #     logger.info(f"{i()}💥💥💥CATALOG HTML ----- Cataloging cache data for URL: {url}")
    #     logger.info(f"{i()}💥💥💥CATALOG HTML ----- html_content: {type(html_content)}")
    #     raise ValueError("html_content must be a string or BeautifulSoup object")

    # Convert the soup object to a string to perform a broad check
    soup_str = str(soup)

    # Broad check: If '</thead></table>' exists, it's an empty data page, return False
    if "</thead></table>" in soup_str:
        return False

    # Ensure gs.current_url is a string before testing membership
    current_url = str(gs.current_url) if gs.current_url else ""

    # Check for empty tables (with or without tbody)
    if (
        (
            soup.find_all("tbody")
            and all(not tbody.find_all("tr") for tbody in soup.find_all("tbody"))
        )
        or (
            soup.find_all("table")
            and all(not table.find_all("tr") for table in soup.find_all("table"))
        )
        or ("events" in current_url and "No events" in soup.get_text())
        or ("filings" in current_url and "Sorry, no filings for" in soup.get_text())
    ):
        return False

    # Sections to check for presence but no associated data
    empty_sections = [
        ("Branches", "data-table-branch_relationship_subject"),
        ("Home company", "data-table-branch_relationship_object"),
        ("Parent companies", "data-table-subsidiary_relationship_object"),
        ("Subsidiaries", "data-table-subsidiary_relationship_subject"),
        ("Mergers", "data-table-merger_subject"),
        ("Mergers", "data-table-merger_object"),
        ("Statements of control", "data-table-control_statement_subject"),
        ("Statements of control", "data-table-control_statement_object"),
        ("Total Shares", "data-table-total_shares_object"),
        ("Total Shares", "data-table-total_shares_subject"),
        ("Shares issued", "data-table-share_parcel_object"),
        ("Shareholdings in other companies", "data-table-share_parcel_subject"),
        ("Trademark registrations", "data-table-trademark_registration"),
        ("Industry codes", "data-table-industry_code"),
        ("Alternate registration statements", "data-table-alternate_registration"),
        ("Subsequent registration statements", "data-table-subsequent_registration"),
        ("Identifiers", "data-table-identifier_delegate"),
        ("Gazette notices", "data-table-gazette_notice_delegate"),
        ("Supplier relationships", "data-table-supplier_relationship"),
    ]

    # Check if any of these sections exist but have no table data
    for section_name, section_id in empty_sections:
        htmlsection = soup.find(id=section_id)
        if htmlsection and section_name in htmlsection.get_text():
            table = htmlsection.find("table")
            if table and not table.find_all("tr"):  # Table exists but has no rows
                return False
            elif not table:  # Section exists, but no table is present
                return False

    return True


def remove_empty_elements(soup: Union[BeautifulSoup, Tag]) -> BeautifulSoup:
    """_summary_

    Args:
        soup (Union[BeautifulSoup, Tag]): _description_

    Returns:
        BeautifulSoup: _description_
    """

    def clean(element):
        # Make a copy of children to avoid modifying the list while iterating over it
        for child in list(element.children):
            if isinstance(child, Tag):
                # Recursively clean children
                clean(child)
                # After cleaning children, check if the current tag is empty
                if (
                    not child.text.strip()
                ):  # No need to check contents separately; text.strip() suffices
                    child.decompose()
            # Remove navigable strings that are purely whitespace
            elif isinstance(child, NavigableString) and not child.strip():
                child.extract()

    # Start cleaning from the root
    clean(soup)
    return soup


def fetch_html(url: str) -> BeautifulSoup:
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
    rate_limit_pattern = r"It appears this IP address may be accessing OpenCorporates at a higher than expected rate."

    service_unavailable_pattern = r'\u003Ctitle>Service Unavailable\u003C/title>\n    \u003Cmeta name="description" content="No server is available to handle the request'

    logger.info(f"{i()}🌎 Fetching URL: {url}")
    gs.current_driver.get(url)
    random_wait(1, 1)  # Wait for JavaScript to load

    if gs.current_driver.current_url != url:
        logger.warning(
            f"{i()}🛑🧺🚨🚩FETCHING FAIL --- Redirected to URL? {url} wanted but pulled from {gs.current_driver.current_url}"
        )
        return None

    page_source = gs.current_driver.page_source

    if re.search(forbidden_pattern, page_source):
        raise Exception(
            f"{i()}🛑🧺🚨🚩❌‼️‼️ FETCHING FAIL --- FORBIDDEN Request is denied at URL {url}"
        )

    if re.search(rate_limit_pattern, page_source):
        raise Exception(
            f"{i()}🛑🧺🚨🚩FETCHING FAIL --- RATE LIMITED or rate limit content detected at URL {url}"
        )

    if re.search(service_unavailable_pattern, page_source):
        raise Exception(
            f"{i()}🌎🌎🛑🧺🚨🚩 FETCHING FAIL --- SERVICE UNAVAILABLE at URL {url}"
        )

    soup = BeautifulSoup(page_source, "html.parser")

    # Isolate the content within id="page_container"
    page_container = soup.find(id="page_container")
    if not page_container:
        logger.warning(
            f"{i()} Page container with id='page_container' not found for URL {url}"
        )
        return None

    # Filtering logic starts here
    # 1. Remove <div class="row prefooter">
    if prefooter_div := page_container.find("div", class_="row prefooter"):
        prefooter_div.decompose()

    # 2. Remove <span class="heading-help">
    for span in page_container.find_all("span", class_="heading-help"):
        span.decompose()

    # 3. Handle <a> elements with the class "jurisdiction_filter" within <dd>
    for link in page_container.find_all("a", class_="jurisdiction_filter"):
        if link.find_parent("dd"):
            link.find_parent("dd").replace_with(f"<dd>{link.get_text()}</dd>")
        else:
            link.decompose()

    # 4. Modify the title attribute
    for tag in page_container.find_all(
        title=re.compile(r"^More Free And Open Company Data On ")
    ):
        new_title = re.sub(r"^More Free And Open Company Data On ", "", tag["title"])
        tag["title"] = new_title

    # 5. Remove the <h3> under #similarly_named
    if (samesection := page_container.find(id="similarly_named")) and (
        section_h3 := samesection.find("h3")
    ):
        section_h3.decompose()

    # 6. Remove links with href ending in 'exclude_inactive=true'
    for link in page_container.find_all("a", href=True):
        if link["href"].endswith("exclude_inactive=true"):
            link.decompose()

    # 7. Replace `> <` with `><`
    standardized_html = re.sub(r">\s+<", "><", str(page_container))

    # 8. Remove the string `class="container plain_background" id="page_container"`
    standardized_html = re.sub(
        r'class="container plain_background" id="page_container"', "", standardized_html
    )

    # 9. Remove the string ` class="vcard" itemscope="" itemtype="http://schema.org/Corporation"`
    standardized_html = re.sub(
        r' class="vcard" itemscope="" itemtype="http://schema.org/Corporation"',
        "",
        standardized_html,
    )

    # 10. Remove the pattern for Corporate Groupings
    standardized_html = re.sub(
        r'<div class="sidebar-item" id="groupings"><h4><span class="define">Corporate Grouping</span><span class="badge badge-info user_contributed small"><a data-original-title="This data has been user contributed" data-placement="top" href="/legal/glossary#user-contributed-data" rel="tooltip">User Contributed</a></span></h4><div class="tags"><div class="add_block"> None known. <a class="new_corporate_grouping_membership add label label-important" data-remote="true" href="/corporate_grouping_memberships/new\\?company_number=.*?" rel="nofollow">Add one now\\?</a></div></div><a href="/corporate_groupings" title="See all Corporate Groupings">See all corporate groupings</a></div>',
        "",
        standardized_html,
    )

    # 11. Remove the pattern for Source
    standardized_html = re.sub(
        r'<div id="source"><strong>Source </strong><span class="publisher">.*?</span>, <a class="url external" href=".*?">.*?</a>, <span class="retrieved">.*?</span></div>',
        "",
        standardized_html,
    )

    # 12. Replace the pattern `title=".*?">` with `>`
    standardized_html = re.sub(r'title=".*?">', ">", standardized_html)

    # 13. Remove the pattern for registry page links
    standardized_html = re.sub(
        r'<dd class="registry_page"><a class="url external" href=".*?</a></dd>',
        "",
        standardized_html,
    )

    # 14. Remove empty elements or elements with only whitespace recursively

    soup = BeautifulSoup(standardized_html, "html.parser")
    remove_empty_elements(soup)

    # 15. Standardize the HTML output by removing extra whitespace and formatting
    standardized_html = re.sub(r"\s+", " ", str(soup)).strip()

    # 16. Detect empty data page. note: that we are ok to pass the soap and work it because we already sealed the strings
    if not has_data(soup):
        standardized_html = "<h1>NO DATA</h1>"

    return BeautifulSoup(standardized_html, "html.parser")


# The function fetch_html now focuses on the content within #page_container and applies the filtering there.


def load_html_content(url: str = None, attempt: int = 1) -> BeautifulSoup:
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
        if db.cache.url_cached(url):
            logger.info(
                f"{i()} 🔧🗃️ LOADING CACHE ----- Loading cached content for URL: {url}"
            )
            return db.cache.load_cache(url)

        # Fetch content if not cached
        logger.info(
            f"{i()} 🔧🌎 FETCHING CONTENT ----- Fetching content for URL: {url}"
        )
        # soup = fetch_html(url)

        # opening() we open/close on every 20th url
        warm_cache()
        # exiting()
        if db.cache.url_cached(url):
            logger.info(
                f"{i()} 🔧🗃️ LOADING CACHE ----- Loading cached content for URL: {url}"
            )
            return db.cache.load_cache(url)

        # return soup
    except Exception as e:
        logger.error(f"{i()} 💥🚩 Error for URL {url}: {e}", exc_info=True)
        logger.error(f"{i()} {traceback.format_exc()}")
        if attempt < 3:
            logger.info(
                f"{i()} 🔧🌐 RETRYING ----- Retrying ({attempt + 1}/3) for URL: {url}"
            )
            return load_html_content(url, attempt + 1)
        else:
            logger.error(f"{i()} 💥🚩 Failed to fetch URL {url} after 3 attempts")
            return None


def get_parent_url(
    soup: Union[BeautifulSoup, Tag], target_selector: Optional[str] = "a.company"
) -> Optional[str]:
    """
    Extracts the parent URL from the given soup object, with an optional target selector for flexibility.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the page source.
        target_selector (Optional[str]): The CSS selector to target a specific element for the parent URL.
                                        Defaults to 'a.company.branch.active'.

    Returns:
        Optional[str]: The URL found for the parent entity, or None if not found.
    """
    soup_copy = copy.copy(soup)
    parent_url = None

    # Look for the element using the target selector
    if target_element := soup_copy.select_one(target_selector):
        parent_url = urljoin(gs.current_url, target_element["href"])
        logger.info(f"{i()}🌎 CACHE WARMING ------ Parent URL found: {parent_url}")
    else:
        logger.warning(
            f"{i()}🌎 CACHE WARMING ------ No parent URL found using selector: {target_selector}"
        )

    return parent_url


def extract_urls(
    soup: Union[BeautifulSoup, Tag],
    target_selector: Optional[str] = None,
    url_filter: Optional[str] = None,
) -> List[str]:
    """
    Extracts distinct URLs from the given soup object, with optional parameters for
    targeting a specific element and filtering URLs based on a substring.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the page source.
        target_selector (Optional[str]): The CSS selector to target a specific part of the HTML.
                                        If None, the whole document is searched. Default is None.
        url_filter (Optional[str]): A substring to filter URLs. If None, no filtering is applied.
                                    Default is None.

    Returns:
        List[str]: A list of distinct URLs matching the specified filter (if provided).
    """
    soup_copy = copy.copy(soup)
    urls = set()  # Using a set to ensure distinct URLs

    # If a target selector is provided, search within that target, otherwise search the whole soup
    if target_selector:
        target = soup_copy.select_one(target_selector)
        if target:
            soup_copy = target
        else:
            logger.warning(
                f"{i()}🌎 CACHE WARMING ------ Target selector '{target_selector}' not found."
            )

    # Find all 'a' tags with 'href' attributes
    url_elements = soup_copy.find_all("a", href=True)
    for element in url_elements:
        href = element["href"]
        logger.info(f"{i()}🌎 CACHE WARMING ------ link found: {href}")

        # Apply optional URL filter
        if url_filter:
            if url_filter in href:
                urls.add(urljoin(gs.current_url, href))
                logger.info(
                    f"{i()}🌎 CACHE WARMING ------ URL passed filter '{url_filter}': {href}"
                )
            else:
                logger.info(f"{i()}🌎 CACHE WARMING ------ URL filtered out: {href}")
        else:
            urls.add(urljoin(gs.current_url, href))

    distinct_urls = list(urls)
    logger.info(f"{i()}🌎 CACHE WARMING ------ all distinct links: {distinct_urls}")
    return distinct_urls


def extract_officer_urls(soup: Union[BeautifulSoup, Tag]) -> List[str]:
    """
    Extracts officer URLs from the given soup object.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the page source.

    Returns:
        List[str]: A list of officer detail URLs.
    """
    soup_copy = copy.copy(soup)
    officer_urls = []
    # if focused := soup_copy.find('div', class_='sidebar'):
    #     focused.decompose()
    officer_elements = soup_copy.find_all("a", href=True)
    for element in officer_elements:
        href = element["href"]
        # Check if the href contains "/officers"
        if "/officers" in href:
            # Allow if it contains "page", but exclude if it contains "occupation", "position", "nationality", or "q="
            if (
                "occupation=" not in href
                and "position=" not in href
                and "nationality=" not in href
                and "q=" not in href
            ) and "opencorporates.com" in href:
                logger.info(
                    f"{i()}🌎➕➕ CACHE WARMING ------ officer link found: {href}"
                )
                officer_urls.append(urljoin(gs.current_url, href))
    logger.info(f"{i()}🌎 CACHE WARMING ------ all the links: {officer_urls}")
    return officer_urls


def extract_company_urls(soup: Union[BeautifulSoup, Tag]) -> List[str]:
    """
    Extracts company URLs from the given soup object, excluding specific keywords in the href.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object containing the page source.

    Returns:
        List[str]: A list of company detail URLs.
    """
    company_urls = []
    # Find all anchor tags with href attribute
    link_elements = soup.find_all("a", href=True)

    # Iterate through each link element
    for element in link_elements:
        href = element["href"]

        # Check if the href meets the inclusion criteria
        if (
            "/companies" in href
            and all(
                keyword not in href
                for keyword in ["officers", "statements", "events", "filings"]
            )
            and (
                "occupation=" not in href
                and "position=" not in href
                and "nationality=" not in href
                and "q=" not in href
            )
        ) and "opencorporates.com" in href:
            logger.info(f"{i()}🌎➕➕ CACHE WARMING ------ link found: {href}")
            company_urls.append(urljoin("https://opencorporates.com/", href))

    logger.info(f"{i()}🌎 CACHE WARMING ------ all the links: {company_urls}")
    return company_urls


def extract_company_number_from_url(url: str = None) -> Union[str, None]:
    """
    Extracts the company number from a given URL using regex.

    Parameters:
    ----------
    url : str, optional
        The URL from which to extract the company number. Defaults to gs.current_url.

    Returns:
    -------
    str or None
        The extracted company number, or None if no company number is found.

    This function takes a URL as input and extracts the company number from it using a regex pattern.
    It matches patterns like 'us_mo/00345772' or 'us_il/CORP_66442861' and extracts the company number part.

    Example usage:
    ----------
    url = "https://opencorporates.com/companies/us_mo/00345772"
    company_number = extract_company_number_from_url(url)
    print(company_number)  # Output: 00345772
    """
    try:
        url = ensure_url(url)
        # Define the regex pattern to match the company number
        pattern = re.compile(r"/companies/[a-z]{2}(?:_[a-z]{2})?/([^/]+)")

        # Search for the pattern in the URL
        match = pattern.search(url)

        if match:
            # Extract and return the company number
            company_number = match.group(1)
            logger.debug(f"{i()}🗃️🌎 Extracted company number: {company_number}")
            return company_number
        else:
            logger.debug(f"{i()}🗃️🌎 No company number found in URL: {url}")
            return None
    except Exception as e:
        logger.error(f"{i()}🛑🧺🚨 Error extracting company number from URL: {e}")
        logger.error(f"{i()} {traceback.format_exc()}")
        return None


def extract_jurisdiction(url: str = None) -> Union[str, None]:
    """_summary_

    Args:
        url (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Define regex pattern to extract the jurisdiction code (group 1) after '/companies/'
    if url is None:
        raise ValueError("URL is required")

    pattern = r"/companies/([a-z]{2}(?:_[a-z]{2})?)/"

    # Search for the pattern in the given URL
    match = re.search(pattern, url)

    if match:
        # Return the captured jurisdiction code
        return match.group(1)
    else:
        # Return None if no jurisdiction code is found (e.g., URL doesn't contain /companies/)
        return None


def extract_jurisdiction_from_url(url: str = None) -> Union[str, None]:
    """
    Extracts the jurisdiction from a given URL.

    Parameters:
    ----------
    url : str, optional
        The URL from which to extract the jurisdiction. Defaults to gs.current_url.

    Returns:
    -------
    str or None
        The extracted jurisdiction name, or None if no jurisdiction is found.

    This function takes a URL as input and extracts the jurisdiction from it. It splits the URL and matches the
    jurisdiction code (e.g., 'us_mo') to retrieve the corresponding jurisdiction name from the database.

    Example usage:
    ----------
    url = "https://opencorporates.com/companies/us_mo/00345772"
    jurisdiction = extract_jurisdiction_from_url(url)
    print(jurisdiction)  # Output: Missouri
    """
    from db.dbefclasses import Jurisdiction

    try:
        if "opencorporates.com/companies" not in url:
            logger.debug(f"{i()}🗃️🚨🚨🌎 No jurisdiction in url: {url}")
            return None

        url = ensure_url(url)
        # Extract the jurisdiction code from the URL
        jurisdiction_code = extract_jurisdiction(
            url
        )  # Extract 'us_**' part from the URL

        logger.debug(f"{i()}🗃️🌎 jurisdiction_code parsed from url: {jurisdiction_code}")

        if jurisdiction_code is not None:
            # Query the database for the jurisdiction name
            # jurisdiction_record = None
            # with gs.read() as readsession:
            #     # jurisdiction_record = readsession.query(Jurisdiction).filter_by(code=).first()
            jurisdiction_record = Jurisdiction.fetch(
                limit=1, where=f"code = '{jurisdiction_code}'"
            )
            logger.debug(f"{i()}🗃️🚨🚨🌎 jurisdiction_record: {jurisdiction_record}")
            if len(jurisdiction_record) == 1:
                jurisdiction_name = jurisdiction_record[0][2]
                logger.debug(f"{i()}🗃️🌎 Extracted jurisdiction: {jurisdiction_name}")
                return jurisdiction_name

            logger.debug(
                f"{i()}🗃️🌎 No jurisdiction found for code: {jurisdiction_code}"
            )
            return None
        else:
            logger.debug(f"{i()}🛑🧺🚨 No jurisdiction code found in URL: {url}")
            return None
    except Exception as e:
        logger.error(f"{i()}🛑🧺🚨 Error extracting jurisdiction from URL: {e}")
        logger.error(f"{traceback.format_exc()}")
        return None


def addcompanyurls(base_url):
    """
    Inserts a list of base URLs into the database, and then inserts derived URLs using URL_PATTERNS with the base URL's ID as the parent_id.
    """

    from db.dbefclasses import URLCatalog

    URL_PATTERNSs = [
        "/statements/subsidiary_relationship_object",
        "/statements/subsidiary_relationship_subject",
        "/statements/branch_relationship_subject",  # has these branches - the children
        "/statements/branch_relationship_object",  # Is a branch of - the partent
        "/statements/total_shares_object",
        "/statements/total_shares_subject",
        "/statements/share_parcel_object",
        "/statements/share_parcel_subject",
        "/statements/merger_object",
        "/statements/merger_subject",
        "/statements/trademark_registration",
        "/statements/identifier_delegate",
        "/statements/gazette_notice_delegate",
        "/statements/control_statement_subject",
        "/statements/control_statement_object",
        "/statements/industry_code",
        "/statements/supplier_relationship",
        "/statements/subsequent_registration",
        "/statements/alternate_registration",
        "/filings",
        "/events",
        "/officers",
    ]

    try:

        # Initialize base_url_id to ensure it's defined before usage
        base_url_id = None

        # Extract company ID and jurisdiction
        company_number = extract_company_number_from_url(base_url)
        jurisdiction = extract_jurisdiction_from_url(base_url)
        existing_base_url = None

        with gs.read() as readsession:
            # Check if the base URL already exists
            existing_base_url = (
                readsession.query(URLCatalog).filter_by(url=base_url).first()
            )
            if existing_base_url:
                base_url_id = (
                    existing_base_url.id
                )  # Extract base_url_id while still in the session
                logger.info(
                    f"{i()}🔍🌎📬✅ Base URL existed: {base_url} with ID: {base_url_id}, Company Number: {company_number}, Jurisdiction: {jurisdiction}"
                )

        if not existing_base_url:
            # Insert the base URL
            new_base_url_record = URLCatalog(
                url=base_url,
                company_number=company_number,
                jurisdiction=jurisdiction,
                completed=False,
            )

            with gs.write() as writesession:
                writesession.add(new_base_url_record)
                writesession.commit()
                # Access ID after commit
                writesession.refresh(
                    new_base_url_record
                )  # Ensures it's refreshed and bound
                base_url_id = new_base_url_record.id
            logger.info(
                f"{i()}🔍🌎📬✅ Base URL saved: {base_url} with ID: {base_url_id}, Company Number: {company_number}, Jurisdiction: {jurisdiction}"
            )

        # Insert derived URLs using the base URL as the parent_id
        for pattern in URL_PATTERNSs:
            derived_url = f"{base_url}{pattern}"
            existing_derived_url = None
            with gs.read() as readsession:
                existing_derived_url = (
                    readsession.query(URLCatalog).filter_by(url=derived_url).first()
                )
            if not existing_derived_url:
                derived_url_record = URLCatalog(
                    url=derived_url,
                    company_number=company_number,
                    jurisdiction=jurisdiction,
                    completed=False,
                    parent_id=base_url_id,
                )
                with gs.write() as writesession:
                    writesession.add(derived_url_record)
                logger.info(
                    f"{i()}🔍🌎📬 Derived URL saved: {derived_url} with parent ID: {base_url_id}, Company Number: {company_number}, Jurisdiction: {jurisdiction}"
                )
            else:
                logger.info(
                    f"{i()}🔍🌎📬 Derived URL existed: {derived_url} with parent ID: {base_url_id}, Company Number: {company_number}, Jurisdiction: {jurisdiction}"
                )

    except IntegrityError as e:
        with gs.write() as writesession:
            writesession.rollback()
        logger.error(f"{i()}🛑🧺🚨 Error inserting URLs: {e}")
        logger.error(f"{traceback.format_exc()}")
