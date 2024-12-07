import re
from typing import List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import EXCLUDE_PATTERNS, i


def supplier_relationship(
    soup: Union[BeautifulSoup, Tag], main_url: str = None
) -> List[str]:
    """
    Extracts supplier relationship information from a BeautifulSoup object representing a section of HTML with supplier data.

    This function processes the given BeautifulSoup object to extract supplier relationship information.
    If the object is invalid or the information is not found, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with supplier data.
        main_url (str, optional): The main URL to resolve relative links.

    Returns:
        list: A list containing the extracted supplier relationship information.

    Raises:
        ValueError: If the BeautifulSoup object is invalid.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <div id="government_approved_suppliers">
        ...     <div class="assertion government_approved_supplier" id="assertion_2757261">
        ...         <div class="subhead"><a href="/data/2757261">Approved US Government Supplier</a></div>
        ...     </div>
        ... </div>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> supplier_relationship(soup)
        ['Approved US Government Supplier']
    """
    from db.dbefclasses import Link

    theselinks = set()
    if not ensure_soup(soup, "SUPPLIER RELATIONSHIP"):
        return []

    # Extract supplier relationship information
    supplier_section = soup.find("div", id="government_approved_suppliers")
    if supplier_section:
        for supplier in supplier_section.find_all(
            "div", class_="assertion government_approved_supplier"
        ):
            subhead = supplier.find("div", class_="subhead")
            if subhead and subhead.find("a"):
                supplier_name = subhead.find("a").text.strip()
                supplier_link = subhead.find("a")["href"]
                theselinks.add(supplier_name)
                # Save to database using Assertion model
                assertion_record = Assertion(
                    company_number=gs.current_company_number,
                    title="Supplier Relationship",
                    description=supplier_name,
                    link=supplier_link
                )
                assertion_record.catalog(
                    data={
                        "title": "Supplier Relationship",
                        "description": supplier_name,
                        "link": supplier_link
                    }
                )
                logger.debug(
                    f"{i()}📊 SUPPLIER RELATIONSHIP -- Saved supplier relationship to assertions table: {supplier_name}, link: {supplier_link}"
                )
    else:
        logger.debug(
            f"{i()}⛏️🖨️ 🛑🚨🚩SUPPLIER RELATIONSHIP -- No supplier relationship information found."
        )

    section(
        "EXITING --- SCRAPING SUPPLIER RELATIONSHIP",
        color="green",
        justification="center",
    )

    return list(theselinks)
