from typing import Dict, List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.database_handlers import catalog_company_address
from services.extractors.utils import ensure_soup
from settings.settings import i
from utils.useollama import clean_zip_code, normalize_address


def assertions(soup: Union[BeautifulSoup, Tag]) -> Dict[str, List[Dict[str, str]]]:
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
        >>> assertions(soup)
        {'Group 1': [{'Title': 'Assertion Title 1', 'Link': '/assertion/1', 'Description': 'Description 1'},
                    {'Title': 'Assertion Title 2', 'Link': '/assertion/2', 'Description': 'Description 2'}]}
    """
    from db.dbefclasses import Assertion

    if not ensure_soup(soup, "ASSERTIONS"):
        return []

    data = {}

    groups = soup.find_all("div", class_="assertion_group")
    for group in groups:
        group_name = group.find("h3").text.strip()
        assertions_list = []
        for assertion in group.find_all("div", class_="assertion"):
            title_element = assertion.find("a")
            title = title_element.text.strip() if title_element else ""
            link = (
                urljoin(gs.current_url, title_element["href"]) if title_element else ""
            )
            description_element = assertion.find("p", class_="description")
            description = (
                description_element.text.strip() if description_element else ""
            )

            if "Address" in title:

                parts_of_address = [part for part in description]
                # Remove any empty strings from the list before joining the parts
                parts_of_address = [
                    clean_zip_code(part.strip())
                    for part in parts_of_address
                    if part.strip()
                ]

                address_str = ", ".join(parts_of_address)

                logger.debug(f"{i()}⛏️🖨️ Address -- {title}: {address_str}")
                # dd_text = normalize_address(dd_text)
                address_obj = catalog_company_address(address_str, gs.current_company_number)
                if address_obj:
                    standardized_address = address_obj.normalized_address
                    # Use standardized_address as needed

                description = standardized_address

            assertion_data = {
                "company_number": gs.current_company_number,
                "title": title,
                "link": link,
                "description": description,
            }
            assertion = Assertion(**assertion_data)
            assertion.catalog(data=assertion_data)

        if not assertions_list:
            logger.debug(
                f"{i()}⛏️🖨️ 🛑🚨🚩ASSERTIONS -- No assertions found in group {group_name}"
            )

        data[group_name] = assertions_list

    if not data:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩ASSERTIONS -- No assertions extracted.")

    section("EXITING --- SCRAPING ASSERTIONS", color="green", justification="center")

    return data
