import re
from typing import List, Union

from bs4 import BeautifulSoup, Tag

import gs
from db.dbefclasses import CompanyAKA
from services.applogging import logger
from services.extractors.utils import ensure_soup
from settings.settings import i


def company_akas(soup: Union[BeautifulSoup, Tag]) -> List[str]:
    """
    Extracts and saves the previous names (AKAs) of the company from the HTML document.

    Parameters:
    ----------
    soup : BeautifulSoup or Tag
        The BeautifulSoup object representing the HTML document.

    Returns:
    -------
    list
        A list of previous names (AKAs) if found, otherwise an empty list.
    """
    akas = []

    if not ensure_soup(soup, "COMPANY AKAS"):
        return []

    # Function to extract name, type, start date, and end date from a name line
    def extract_name_details(name_line: str):
        name = name_line.split("(")[0].strip()
        details = re.search(r"\(([^,]+), ([^,]+), ([^,]+) - ([^,]+)\)", name_line)
        if details:
            type_ = details.group(1).strip()
            start_date = details.group(3).strip()
            end_date = (
                details.group(4).strip() if details.group(4).strip() != "-" else None
            )
        else:
            type_ = "historical"
            start_date = None
            end_date = None
        return name, type_, start_date, end_date

    # Extract previous names
    previous_names_element = soup.find("dd", class_="previous_names")
    if previous_names_element:
        name_lines = previous_names_element.find_all("li", class_="name_line")
        for name_line in name_lines:
            name = name_line.text.strip()
            akas.append(name)
            aka_data = {
                "company_number": gs.current_company_number,
                "aka": name,
                "type": "historical",
            }
            company_aka = CompanyAKA(**aka_data)
            try:
                company_aka.catalog(data=aka_data)
                logger.info(f"{i()}🏢📊✅ Previous name saved: {name}")
            except Exception as e:
                logger.error(f"Error saving previous name: {e}")
    else:
        logger.debug(f"{i()}🛑 Previous names section not found.")

    # Extract alternative names
    alternative_names_element = soup.find("dd", class_="alternative_names")
    if alternative_names_element:
        name_lines = alternative_names_element.find_all("li", class_="name_line")
        for name_line in name_lines:
            name, type_, start_date, end_date = extract_name_details(
                name_line.text.strip()
            )
            akas.append(name)
            aka_data = {
                "company_number": gs.current_company_number,
                "aka": name,
                "type": type_,
                "start_date": start_date,
                "end_date": end_date,
            }
            company_aka = CompanyAKA(**aka_data)
            try:
                company_aka.catalog(data=aka_data)
                logger.info(f"{i()}🏢📊✅ Alternative name saved: {name}")
            except Exception as e:
                logger.error(f"Error saving alternative name: {e}")
    else:
        logger.debug(f"{i()}🛑 Alternative names section not found.")

    return akas
