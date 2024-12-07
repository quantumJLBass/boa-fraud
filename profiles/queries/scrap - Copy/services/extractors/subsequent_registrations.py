import re
from typing import List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def subsequent_registrations(
    soup: Union[BeautifulSoup, Tag], main_url: str = None
) -> List[dict]:
    """
    Extracts subsequent registration information from a BeautifulSoup object and saves it as assertions.

    This function processes the given BeautifulSoup object to extract subsequent registration
    information, typically found in a <dd> element with class "subsequent_registrations".
    It extracts company names and their corresponding links, then saves this information
    as assertions in the database.

    Args:
        soup (Union[BeautifulSoup, Tag]): A BeautifulSoup object representing the HTML content.
        main_url (str, optional): The base URL to be used for creating absolute URLs. Defaults to None.

    Returns:
        List[dict]: A list of dictionaries containing the extracted subsequent registration information.
                    Each dictionary has keys 'title', 'description', and 'link'.

    Raises:
        AttributeError: If the soup object doesn't have the expected structure.

    Example:
        >>> html = '''
        ... <dd class="subsequent_registrations">
        ...   <ul class="attribute_list">
        ...     <li class="attribute_item">
        ...       <a class="company currently_registered" href="/companies/de/M1201_HRB78291">
        ...         Goldman, Sachs Management GP GmbH (M1201_HRB78291)
        ...       </a>
        ...     </li>
        ...   </ul>
        ... </dd>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> subsequent_registrations(soup, 'https://example.com')
        [{'title': 'Subsequent Registration',
          'description': 'Goldman, Sachs Management GP GmbH (M1201_HRB78291)',
          'link': 'https://example.com/companies/de/M1201_HRB78291'}]
    """
    from db.dbefclasses import Assertion

    subsequent_regs = []
    if not ensure_soup(soup, "SUBSEQUENT REGISTRATIONS"):
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩SUBSEQUENT REGISTRATIONS -- No valid soup object.")
        return subsequent_regs

    try:
        dd_element = soup.find('dd', class_='subsequent_registrations')
        if dd_element:
            for li in dd_element.find_all('li', class_='attribute_item'):
                a_tag = li.find('a', class_='company')
                if a_tag:
                    company_name = a_tag.text.strip()
                    link = a_tag.get('href')
                    if main_url and link:
                        link = urljoin(main_url, link)

                    assertion_data = {
                        'company_number': gs.current_company_number,
                        'title': 'Subsequent Registration',
                        'description': company_name,
                        'link': link
                    }
                    subsequent_regs.append(assertion_data)

                    # Create and catalog Assertion object
                    assertion_obj = Assertion(**assertion_data)
                    assertion_obj.catalog(data=assertion_data)

        if not subsequent_regs:
            logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩SUBSEQUENT REGISTRATIONS -- No subsequent registrations found.")
    except AttributeError as e:
        logger.error(f"{i()}⛏️🖨️ 🛑🚨🚩SUBSEQUENT REGISTRATIONS -- Error parsing soup: {str(e)}")

section(
        "EXITING --- SCRAPING SUBSEQUENT REGISTRATIONS",
        color="green",
        justification="center",
    )

    return list(theselinks)
