import re
from datetime import datetime
from typing import Dict, Union

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.database_handlers import catalog_company_address
from services.extractors.utils import ensure_soup
from settings.settings import i
from utils.useollama import clean_zip_code
from utils.utils import normalize_textblocks


def attributes(
    soup: Union[BeautifulSoup, Tag]
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
        Dict[str, Union[str, Dict[str, str]]]: A dictionary where each key is the text of a <dt> tag and the corresponding value is either a string or a dictionary.
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
        >>> attributes(attributes)
        {'Inactive Directors / Officers': 'S CRAIG ADAMS, member SCOTT CARLSTON, agent SCOTT CARLSTON, member SCOTT CARLSTON, registered agent'}

    Notes:
        - This function assumes that each <dt> tag has a corresponding <dd> tag within the `attributes` section.
        - The function utilizes helper functions `normalize_textblocks` and `normalize_address` to ensure text consistency.
        - If the text content of a <dd> tag includes address information, additional normalization is performed to standardize the address format.
    """
    from db.dbefclasses import Attribute

    if not ensure_soup(soup, "ATTRIBUTES"):
        return []

    dt_tags = soup.find_all("dt")
    dd_tags = soup.find_all("dd")

    if not dt_tags or not dd_tags:
        logger.debug(f"{i()}🛑🚨 No attributes found in the provided HTML.")
        return {}

    data = {}

    for dt, dd in zip(dt_tags, dd_tags):
        dt_text = dt.text.strip()

        if not dt_text or dt_text in ["Company Number", "Jurisdiction"]:
            continue  # Skip 'Company Number' and 'Jurisdiction'

        if "Incorporation Date" in dt_text or "Dissolution Date" in dt_text:
            logger.debug(f"{i()}⛏️🖨️ ATTRIBUTES -- {dt_text}: {dd.text}")
            # Use regex to extract date in 'DD Month YYYY' format and convert it to 'YYYY-MM-DD'
            date_match = re.search(r"(\d{1,2})\s+(\w+)\s+(\d{4})", dd.text)
            if date_match:
                try:
                    day, month, year = date_match.groups()
                    # Convert to YYYY-MM-DD format
                    month_number = datetime.strptime(month[:3], "%b").month
                    dd_text = f"{year}-{month_number:02d}-{int(day):02d}"
                except ValueError as e:
                    logger.error(f"Error parsing date: {e}")
                    dd_text = ""  # Handle unexpected date format
            else:
                dd_text = ""  # Handle the case where the date format is unexpected
            logger.debug(f"{i()}⛏️🖨️ ATTRIBUTES -- {dt_text}: {dd_text} (processed)")

        elif "Address" in dt_text:
            parts_of_address = [part for part in dd.stripped_strings]
            # Remove any empty strings from the list before joining the parts
            parts_of_address = [
                clean_zip_code(part.strip())
                for part in parts_of_address
                if part.strip()
            ]

            dd_text = ", ".join(parts_of_address)

            logger.debug(f"{i()}⛏️🖨️ Address -- {dt_text}: {dd_text}")
            # dd_text = normalize_address(dd_text)
            address_obj = catalog_company_address(dd_text, gs.current_company_number)
            if address_obj:
                standardized_address = address_obj.normalized_address
                # Use standardized_address as needed
            logger.debug(f"{i()}⛏️🖨️ Address -- {dt_text}: {standardized_address} (processed)")

        elif dd.find("ul"):
            dd_text = " ".join([li.text.strip() for li in dd.find_all("li")])
        else:
            dd_text = normalize_textblocks(dd.text)

        if "Branch" in dt_text:
            a_tag = dd.find("a")
            if a_tag:
                company_name, company_url = (
                    a_tag.text.strip().replace(" (US)", "").replace("Branch of ", ""),
                    a_tag["href"],
                )
            else:
                company_name, company_url = (
                    dd.text.strip().replace("Branch of ", ""),
                    "",
                )

            logger.debug(f"{i()}⛏️🖨️ Branch of -- {company_name}: {company_url}")
            data["Parent"] = {"company_name": company_name, "url": company_url}
        else:
            data[dt_text] = dd_text

        attribute_data = {
            "company_number": gs.current_company_number,
            "name": dt_text,
            "value": dd_text,
        }
        attribute = Attribute(**attribute_data)
        try:
            attribute.catalog(data=attribute_data)
        except Exception as e:
            logger.error(f"Error cataloging attribute: {e}")

    if not data:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩ATTRIBUTES -- No attributes extracted.")

    section("EXITING --- SCRAPING ATTRIBUTES", color="green", justification="center")

    return data
