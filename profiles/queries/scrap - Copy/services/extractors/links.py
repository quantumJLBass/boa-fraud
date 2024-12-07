import re
from typing import List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import EXCLUDE_PATTERNS, i


def links(soup: Union[BeautifulSoup, Tag], main_url: str = None) -> List[str]:
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
        >>> links(soup, "https://example.com")
        ['https://example.com/page1', 'https://example.com/page2']
    """
    from db.dbefclasses import Link

    if not ensure_soup(soup, "LINKS"):
        return []
    try:
        theselinks = {
            link["href"]
            for link in soup.find_all("a", href=True)
            if link["href"]
            and link["href"] != main_url
            and not any(re.match(pattern, link["href"]) for pattern in EXCLUDE_PATTERNS)
        }

        if not theselinks:
            logger.debug(f"{i()}🛑🚨🚩LINKS -- No links extracted.")
        else:
            for link in theselinks:
                full_url = (
                    urljoin(main_url, link) if not link.startswith("http") else link
                )

                # Use catalog_record to handle insertion or update
                link_data = {
                    "company_number": gs.current_company_number,
                    "link": full_url,
                }
                link = Link(**link_data)
                link.catalog(data=link_data)
                logger.debug(
                    f"{i()}🔗 LINKS -- Cataloged link in Link table: {full_url}"
                )

    except Exception as e:
        logger.error(f"{i()}🛑🚨 Error extracting links: {str(e)}")

    section("EXITING --- SCRAPING LINKS", color="green", justification="center")

    return list(theselinks)
