import re
from typing import List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def control_statement(
    soup: Union[BeautifulSoup, Tag], main_url: str = None
) -> List[Dict[str, Union[str, List[str]]]]:
    """
    Extracts control statement information from the given BeautifulSoup object.

    Args:
        soup (Union[BeautifulSoup, Tag]): The BeautifulSoup object containing the HTML to parse.
        main_url (str, optional): The main URL of the page. Defaults to None.

    Returns:
        List[Dict[str, Union[str, List[str]]]]: A list of dictionaries containing control statement information.

    Raises:
        None

    Example:
        control_statements = control_statement(soup, "https://example.com")
    """
    from db.dbefclasses import ControlStatement, ControlMechanism, ControlStatementMechanism

    control_statements = []
    if not ensure_soup(soup, "CONTROL STATEMENT"):
        return []

    control_statement_div = soup.find("div", id="data-table-control_statement_subject")
    if not control_statement_div:
        logger.warning(f"{i()}🛑 Control statement div not found.")
        return []

    table = control_statement_div.find("table", class_="table-condensed")
    if not table:
        logger.warning(f"{i()}🛑 Control statement table not found.")
        return []

    # Fetch all existing mechanisms
    all_mechanisms = ControlMechanism.query.all()
    mechanism_dict = {mechanism.mechanism: mechanism for mechanism in all_mechanisms}

    for row in table.find_all("tr")[1:]:  # Skip header row
        columns = row.find_all("td")
        if len(columns) < 5:
            continue

        description = columns[1].text.strip()
        mechanisms = [mech.strip() for mech in columns[2].text.strip().split(",")]
        statement_link = urljoin(main_url, columns[4].find("a")["href"]) if columns[4].find("a") else None

        # Extract company information
        controlling_company = columns[1].find_all("a")[0]
        controlled_company = columns[1].find_all("a")[1]

        control_statement_data = {
            "company_number": gs.current_company_number,
            "controlled_company_name": controlled_company.text.strip(),
            "controlled_company_number": extract_company_number_from_url(controlled_company["href"]),
            "controlled_company_jurisdiction": extract_jurisdiction_from_url(controlled_company["href"]),
            "controlling_company_name": controlling_company.text.strip(),
            "controlling_company_number": extract_company_number_from_url(controlling_company["href"]),
            "controlling_company_jurisdiction": extract_jurisdiction_from_url(controlling_company["href"]),
            "start_date": None,  # To be extracted from statement_link
            "end_date": None,  # To be extracted from statement_link
            "mechanisms": ", ".join(mechanisms),
            "statement_link": statement_link,
            "raw_data": str(row),
        }

        # TODO: Extract start_date and end_date from statement_link

        # Save control statement to the database
        control_statement = ControlStatement(**control_statement_data)
        control_statement.catalog(data=control_statement_data)

        # Create associations between control statement and existing mechanisms
        for mechanism in mechanisms:
            if mechanism in mechanism_dict:
                association = ControlStatementMechanism(
                    control_statement_id=control_statement.id,
                    mechanism_id=mechanism_dict[mechanism].id
                )
                association.catalog()
            else:
                logger.warning(f"{i()}🛑 Mechanism '{mechanism}' not found in the database.")

        control_statements.append(control_statement_data)

    return control_statements
