from typing import Union

from bs4 import BeautifulSoup, Tag

from services.applogging import logger, section
from settings.settings import i


def ensure_soup(soup: Union[BeautifulSoup, Tag], extractor_type: str) -> bool:
    """
    Checks the validity of the BeautifulSoup object and logs the extraction process.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with data.
        extractor_type (str): The type of extractor (e.g., 'FILINGS').

    Returns:
        bool: True if the soup object is valid and contains data, False otherwise.
    """
    section(f"SCRAPING {extractor_type}", color="orange1", justification="right")
    if not soup or not hasattr(soup, "find_all"):
        logger.debug(
            f"{i()}⛏️🖨️ 🛑🚨🚩{extractor_type} -- Invalid soup object in {extractor_type.lower()}."
        )
        return False
    if "Sorry, no filings for" in soup.text:
        logger.debug(
            f"{i()}⛏️🖨️ 🛑🚨🚩{extractor_type} -- No {extractor_type.lower()} found."
        )
        return False

    logger.debug(
        f"{i()}⛏️🖨️ {extractor_type} -- Extracting data out of a string {len(soup.text)} long"
    )
    logger.debug(f"{i()}⛏️🖨️ {extractor_type} -- Extracting from {soup.prettify()}")
    return True
