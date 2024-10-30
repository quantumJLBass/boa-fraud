from typing import Dict, List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services import extractors as extract
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def filings(soup: Union[BeautifulSoup, Tag]) -> List[Dict[str, str]]:
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
        >>> filings(soup)
        [{'Date': '2023-01-01', 'Description': 'Filing description', 'Link': ''}]
    """
    from db.dbefclasses import Filing

    if not ensure_soup(soup, "FILINGS"):
        return []

    thesefilings = []
    people = extract.people(soup)
    for item in soup.find_all("div", class_="filing"):
        date_element = item.find("div", class_="dateline")
        link_element = item.find("a")
        description_element = item.find("div", class_="subhead")
        date = date_element.text.strip() if date_element else ""
        link = urljoin(gs.current_url, link_element["href"]) if link_element else ""
        description = description_element.text.strip() if description_element else ""

        filing_data = {
            "company_number": gs.current_company_number,
            "date": date,
            "description": description,
            "link": link,
        }
        filing = Filing(**filing_data)
        filing.catalog(data=filing_data)
        thesefilings.append(filing)
        logger.debug(
            f"{i()}🗃️ FILINGS -- Saved filing to database: {date} - {description}"
        )

    if not thesefilings:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩FILINGS -- No filings extracted.")
    else:
        logger.info(
            f"{i()}⛏️🖨️ FILINGS -- Extracted and saved {len(thesefilings)} filings."
        )

    section("EXITING --- SCRAPING FILINGS", color="green", justification="center")

    return thesefilings
