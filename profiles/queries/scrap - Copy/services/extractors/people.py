import json
from typing import Dict, List, Union
from urllib.parse import urljoin

import probablepeople as pp
from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.database_handlers import catalog_people_address
from services.extractors.utils import ensure_soup
from services.url_handlers import (
    extract_company_number_from_url,
    extract_jurisdiction_from_url,
    load_html_content,
)
from settings.settings import i


def people(soup: Union[BeautifulSoup, Tag]) -> List[Dict[str, str]]:
    """
    Extracts people information from a BeautifulSoup object representing a section of HTML with people data.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML document.

    Returns:
        list: A list of dictionaries containing information about each person. Each dictionary has the following keys:
            - 'Name' (str): The name of the person.
            - 'Role' (str): The role of the person.
            - 'Status' (str): The status of the person ('active' or 'inactive').
            - 'Link' (str): The link associated with the person.
            - 'Start_Date' (str): The start date of the person's term.
            - 'Address' (str): The address of the person.
            - 'Type' (str): The type of the person ('person' or 'corporation').

    Raises:
        None

    Notes:
        - If the input soup object is invalid or does not have the 'find_all' method, an empty list is returned and a debug message is logged.
        - The function iterates over each 'li' element in the soup object and extracts the name, role, status, and link information.
        - If the text of the 'li' element contains a comma, the name and role are extracted using the 'rsplit' method. Otherwise, the entire text is considered as the name.
        - The status is determined based on whether the 'a' element within the 'li' element has the 'inactive' class.
        - The link is extracted from the 'href' attribute of the 'a' element, if it exists.
        - If the link exists, the function fetches the HTML for the person detail page and extracts the address and name, role, and status.
        - A person is either a person or a corporation. The type is determined using the ProbablePeople library. If the name is recognized as a person, the type is set to 'person'. If the name is recognized as a corporation, the type is set to 'corporation'.
    """
    from db.dbefclasses import CompanyPerson, Person, PersonOfficer

    if not ensure_soup(soup, "PEOPLE"):
        return []

    thesepeople = []

    for item in soup.find_all("li"):
        text = item.text.strip()
        if "," in text:
            name, role = map(str.strip, text.rsplit(",", 1))
        else:
            name, role = text, ""

        link_element = item.find("a")
        status = (
            "inactive"
            if link_element and "inactive" in link_element.get("class", [])
            else "active"
        )
        link = link_element["href"] if link_element else ""
        name = name.upper().replace(".", "")
        raw_data = name
        person_data = {
            "company_number": gs.current_company_number,
            "name": name,
            "role": role,
            "status": status,
            "link": urljoin(gs.current_url, link),
        }

        # Save person to the database
        person = Person(**person_data)
        person.catalog(data=person_data)

        parsed_pp, pp_type = "", ""
        try:
            parsed_pp, pp_type = pp.tag(name)
            logger.debug(f"{i()}👨🏬〽️✍️Parsed Person Data: {parsed_pp}")
            logger.debug(f"{i()}👨🏬〽️✍️Person Type: {pp_type}")
        except pp.RepeatedLabelError as e:
            logger.error(
                f"{i()}🔹🚨🚩👨🏬〽️✍️🛑Error in normalize_address (ProbablePeople): {e}"
            )

        if pp_type == "Person":
            person_data.update(
                {
                    "given_name": parsed_pp.get("GivenName", ""),
                    "surname": parsed_pp.get("Surname", ""),
                    "middle_name": parsed_pp.get("MiddleName", ""),
                    "prefix": parsed_pp.get("PrefixMarital", "")
                    or parsed_pp.get("PrefixOther", ""),
                    "suffix": parsed_pp.get("SuffixGenerational", "")
                    or parsed_pp.get("SuffixOther", ""),
                    "raw_data": raw_data,
                }
            )
            person = Person(**person_data)
            person.catalog(data=person_data)

            person_officer_data = {
                "person": person,
                "role": role,
                "status": status,
            }
            person_officer = PersonOfficer(**person_officer_data)
            person_officer.catalog(data=person_officer_data)
        elif pp_type == "Corporation":
            company_number = extract_company_number_from_url(link)
            if company_number:
                company_person_data = {
                    "company_number": company_number,
                    "person": person,
                    "role": role,
                    "status": status,
                }
                company_person = CompanyPerson(**company_person_data)
                company_person.catalog(data=company_person_data)

        if link:
            person_detail_soup = load_html_content(person_data["link"])

            if address_element := person_detail_soup.find("div", class_="address"):
                address = address_element.text.strip()
                person_data["address"] = address
                catalog_people_address(address, person.id)

            name_element = person_detail_soup.find("h1")
            if name_element:
                person_data["name"] = name_element.text.strip()

            role_element = person_detail_soup.find("h2")
            if role_element:
                person_data["role"] = role_element.text.strip()

            status_element = person_detail_soup.find("div", class_="status")
            if status_element:
                person_data["status"] = status_element.text.strip()

            start_date_element = person_detail_soup.find("div", class_="start_date")
            if start_date_element:
                person_data["start_date"] = start_date_element.text.strip()

        thesepeople.append(person_data)
        logger.debug(
            f"{i()}🧑‍💼 PEOPLE -- Saved person to database: {json.dumps(person_data, indent=2)}"
        )

    if not thesepeople:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩PEOPLE -- No people extracted.")

    section("EXITING --- SCRAPING PEOPLE", color="green", justification="center")

    return thesepeople
