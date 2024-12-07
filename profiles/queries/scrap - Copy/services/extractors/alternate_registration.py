import re
from typing import List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def alternate_registration(
    soup: Union[BeautifulSoup, Tag], main_url: str = None
) -> List[str]:
    """
        ***

    Args:
        ***

    Returns:
        ***

    Raises:
        ***

    Example:
        ***
    """
    from db.dbefclasses import Link

    if not ensure_soup(soup, "FILINGS"):
        return []

    theselinks = set()
    section("SCRAPING ALTERNATE REGISTRATION", color="orange1", justification="right")
    if not soup or not hasattr(soup, "find_all"):
        logger.debug(
            f"{i()}⛏️🖨️ alternate_registration -- Invalid content object in alternate_registration."
        )
        return []

    section(
        "EXITING --- SCRAPING ALTERNATE REGISTRATION",
        color="green",
        justification="center",
    )

    return list(theselinks)
