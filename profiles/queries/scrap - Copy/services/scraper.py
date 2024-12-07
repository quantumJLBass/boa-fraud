# scraper.py
from urllib.parse import urljoin, urlparse

import services.extractors as extract
from gs import *
from services.applogging import logger
from services.url_handlers import ensure_url, load_html_content
from settings.settings import *
from utils.useollama import *
from utils.ziptest import *


def scrape_data(url: str = None) -> dict:
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
    section("⛏️🖨️ SCRAPING THE URL 🖨️⛏️", "sea_green2", "right")
    section(f"Scraping URL: {url}", "chartreuse4", "center")
    data = {}

    soup = load_html_content(url)

    if not soup:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩SCRAPPING ISSUE--- Main content not found.")
        return data

    url_parts = urlparse(url).path.strip("/").split("/")

    if url_parts[0] == "companies" and len(url_parts) == 3:
        # Base company URL
        logger.info(f"{i()}⛏️🖨️ SCRAPPING --- Extracting company data from base URL")
        data.update(extract.company_data(soup, url))

    elif url_parts[0] == "companies" and len(url_parts) > 3:
        # Company sub-URL
        section_type = url_parts[-1]
        logger.info(
            f"{i()}⛏️🖨️ SCRAPPING --- Extracting data for section: {section_type}"
        )
        # this needs to be fixed where we have extractors for each section type as we are missing many from the URL_PATTERNS and this also doesn't account for the paged parts of the sections although we may not need to since we cached the paging pages for things like the filings and events

        if "filings" in url:
            data["Filings"] = extract.filings(soup)
        if "events" in url:
            data["Events"] = extract.events(soup)
        if "officers" in url:
            data["Officers"] = extract.officers(soup)
        if "industry_codes" in url:
            data["industry_codes"] = extract.industry_codes(soup)
        elif "merger" in url:
            data["merger"] = extract.merger(soup)
        elif "identifier_delegate" in url:
            data["identifier_delegate"] = extract.identifier_delegate(soup)
        elif "control_statement" in url:
            data["control_statement"] = extract.control_statement(soup)
        elif "alternate_registration" in url:
            data["alternate_registration"] = extract.alternate_registration(soup)
        elif "supplier_relationship" in url:
            data["supplier_relationship"] = extract.supplier_relationship(soup)
        elif "subsequent_registrations" in url:
            data["subsequent_registrations"] = extract.subsequent_registrations(soup)
        elif "gazette_notices" in url:
            data["Gazette_Notices"] = extract.gazette_notices(soup)
        elif "total_shares" in url:
            data["Total_Shares"] = extract.total_shares(soup)
        elif "share_parcel" in url:
            data["share_parcel"] = extract.share_parcel(soup)
        elif any(
            rel_type in url for rel_type in ["branch", "subsidiary"]
        ):  # this is not right.. no url has branch, subsidiary, parent in it that would be usable
            data["Relationships"] = extract.relationships(soup, url)
        else:
            logger.warning(
                f"{i()}⛏️🖨️ 🛑🚨🚩SCRAPPING ISSUE --- Unknown section type: {section_type}"
            )

    elif url_parts[0] == "officers":
        # Officer URL
        logger.info(f"{i()}⛏️🖨️ SCRAPPING --- Extracting officer data")
        data["Officer"] = extract.officers(soup)

    else:
        logger.warning(
            f"{i()}⛏️🖨️ 🛑🚨🚩SCRAPPING ISSUE --- Unexpected URL structure: {url}"
        )

    # Check for pagination
    next_page = soup.find("a", rel="next nofollow")
    if next_page:
        next_page_url = urljoin(url, next_page["href"])
        logger.info(f"{i()}⛏️🖨️ SCRAPPING --- Found next page: {next_page_url}")
        data.update(scrape_data(next_page_url))  # Recursively call scrape_data

    logger.debug(f"{i()}⛏️🖨️ SCRAPPING --- Scraped data: {data}")

    return data
