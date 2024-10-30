import re
from typing import Dict, List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def merger(
    soup: Union[BeautifulSoup, Tag], main_url: str = None
) -> List[Dict[str, Union[str, None]]]:
    """
    Extracts merger information from the given BeautifulSoup object.

    Args:
        soup (Union[BeautifulSoup, Tag]): The BeautifulSoup object containing the HTML to parse.
        main_url (str, optional): The main URL of the page. Defaults to None.

    Returns:
        List[Dict[str, Union[str, None]]]: A list of dictionaries containing merger information.

    Raises:
        None

    Example:
        mergers = merger(soup, "https://example.com")
    """
    from db.dbefclasses import Jurisdiction, Merger

    mergers = []
    if not ensure_soup(soup, "MERGERS"):
        return []

    merger_div = soup.find("div", id="data-table-merger_subject")
    if not merger_div:
        logger.warning(f"{i()}🛑 Merger div not found.")
        return []

    table = merger_div.find("table", class_="table-condensed")
    if not table:
        logger.warning(f"{i()}🛑 Merger table not found.")
        return []

    for row in table.find_all("tr")[1:]:  # Skip header row
        columns = row.find_all("td")
        if len(columns) < 4:
            continue

        merged_company_info = columns[0]
        surviving_company_info = columns[1]

        merged_company_link = merged_company_info.find("a", class_="company")
        surviving_company_link = surviving_company_info.find("a", class_="company")

        # TODO: Extract jurisdiction
        merged_jurisdiction = extract_jurisdiction(merged_company_info)
        jurisdiction_id = None  # TODO: Fetch jurisdiction ID from database

        merger_data = {
            "company_number": gs.current_company_number,
            "merged_company_name": (
                merged_company_link.text.strip() if merged_company_link else None
            ),
            "merged_company_id": (
                merged_company_link["href"].split("/")[-1]
                if merged_company_link
                else None
            ),
            "surviving_company_name": (
                surviving_company_link.text.strip() if surviving_company_link else None
            ),
            "surviving_company_id": (
                surviving_company_link["href"].split("/")[-1]
                if surviving_company_link
                else None
            ),
            "jurisdiction_id": jurisdiction_id,
            "statement_link": (
                urljoin(main_url, columns[3].find("a")["href"])
                if columns[3].find("a")
                else None
            ),
            "start_date": None,  # TODO: Extract start date of merger existence
            "end_date": None,  # TODO: Extract end date of merger existence
            "raw_data": str(row),
        }

        merger_obj = Merger(**merger_data)
        merger_obj.catalog(data=merger_data)
        mergers.append(merger_data)

    if not mergers:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩MERGERS -- No mergers extracted.")

    section("EXITING --- SCRAPING MERGERS", color="green", justification="center")

    return mergers


def extract_jurisdiction(info_column: Tag) -> str:

    jurisdiction_link = info_column.find("a", class_="jurisdiction_filter")
    if jurisdiction_link:
        return jurisdiction_link["href"].split("/")[-1]
    return None


def parse_date(date_string: str) -> str:

    try:
        return parse(date_string).strftime("%Y-%m-%d")
    except ValueError:
        return None
