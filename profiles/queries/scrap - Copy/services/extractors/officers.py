import json
import re
from typing import Dict, List, Union
from urllib.parse import urljoin

import probablepeople as pp
from bs4 import BeautifulSoup, Tag

import gs
from services import extractors as extract
from services.applogging import logger, section
from services.database_handlers import catalog_company_address, catalog_people_address
from services.extractors.utils import ensure_soup
from services.url_handlers import (
    extract_company_number_from_url,
    extract_jurisdiction_from_url,
    load_html_content,
)
from settings.settings import i


def officers(soup: Union[BeautifulSoup, Tag]) -> List[Dict[str, str]]:
    """
    Extracts officers information from a BeautifulSoup object representing a section of HTML with officers data.

    This function processes the given BeautifulSoup object to extract officer information.
    If the object is invalid, it returns an empty list.

    Args:
        soup (BeautifulSoup): The BeautifulSoup object representing the HTML document.

    Returns:
        list: A list of dictionaries containing information about each officer. Each dictionary has the following keys:
            - 'Name' (str): The name of the officer.
            - 'Role' (str): The role of the officer.
            - 'Status' (str): The status of the officer ('active' or 'inactive').
            - 'Link' (str): The link associated with the officer.
            - 'Start_Date' (str): The start date of the officer's term.
            - 'Address' (str): The address of the officer.
            - 'Type' (str): The type of the officer ('person' or 'corporation').

    Raises:
        None

    Notes:
        - If the input soup object is invalid or does not have the 'find_all' method, an empty list is returned and a debug message is logged.
        - The function iterates over each 'li' element in the soup object and extracts the name, role, status, and link information.
        - If the text of the 'li' element contains a comma, the name and role are extracted using the 'rsplit' method. Otherwise, the entire text is considered as the name.
        - The status is determined based on whether the 'a' element within the 'li' element has the 'inactive' class.
        - The link is extracted from the 'href' attribute of the 'a' element, if it exists.
        - If the link exists, the function fetches the HTML for the officer detail page and extracts the address and name, role, and status.
        - An officer is either a person or a corporation. The type is determined using the ProbablePeople library. If the name is recognized as a person, the type is set to 'person'. If the name is recognized as a corporation, the type is set to 'corporation'. we would have then an officer record and that would have a tie to either the person or company. The officer record would have the role, status, and link. The person or company would have its details and ties to address, officers, companys. The person would have the given name, surname, middle name, prefix, and suffix. The company would have the jurisdiction and events and details.
    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <ul>
        ...   <li><a href="/officer/1">John Doe, CEO</a></li>
        ...   <li><a href="/officer/2" class="inactive">Jane Smith, CFO</a></li>
        ... </ul>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> officers(soup)
        [{'Name': 'John Doe', 'Role': 'Director', 'Status': 'active', 'Link': 'https://example.com/officer/1', 'Address': '123 Main St', 'Start_Date': '2022-01-01'},
        {'Name': 'Jane Smith', 'Role': 'Manager', 'Status': 'inactive', 'Link': 'https://example.com/officer/2', 'Address': '456 Elm St', 'Start_Date': '2015-11-18'}]
    """

    from db.dbefclasses import Company, CompanyOfficer, Officer, Person, PersonOfficer

    if not ensure_soup(soup, "OFFICERS"):
        return []

    theseofficers = []

    def process_officer_item(item):
        """
        Process each individual officer item from the list, extract details like name, role, status, and follow
        up with a request for full officer details if necessary.
        """
        person = None
        company = None
        text = item.text.strip()
        occurrence_number = ""
        working_url = str(gs.current_url)
        if ".com/officers" in working_url:
            occurrence_number = working_url.split("/")[-1]
        # Extract name and role, either split by comma or the entire text as the name.
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

        # Extract occurrence number from the link if available.
        if not occurrence_number and link:
            occurrence_number = link.split("/")[-1]

        name = name.upper().replace(".", "")
        raw_data = name

        # Create a base officer data dictionary.
        officer_data = {
            "company_number": gs.current_company_number,
            "name": name,
            "role": role,
            "status": status,
            "link": urljoin(gs.current_url, link),
            "occurrence_number": occurrence_number,
        }

        # Save officer to the database.
        officer = Officer(**officer_data)
        officer.catalog(data=officer_data)

        # Parse the name to determine if it's a person or corporation.
        parsed_pp, pp_type = "", ""
        try:
            parsed_pp, pp_type = pp.tag(name)
        except pp.RepeatedLabelError as e:
            logger.error(f"{i()}🔹Error in name parsing (ProbablePeople): {e}")

        # Handle person-related officer data.
        if pp_type == "Person":
            person_data = {
                "name": name,
                "given_name": parsed_pp.get("GivenName", ""),
                "surname": parsed_pp.get("Surname", ""),
                "middle_name": parsed_pp.get("MiddleName", ""),
                "prefix": parsed_pp.get("PrefixMarital", "")
                or parsed_pp.get("PrefixOther", ""),
                "suffix": parsed_pp.get("SuffixGenerational", "")
                or parsed_pp.get("SuffixOther", ""),
                "raw_data": raw_data,
            }
            person = Person(**person_data)
            person.catalog(data=person_data)

            person_officer_data = {
                "person_id": person.id,
                "officer_id": officer.id,
                "role": role,
            }
            person_officer = PersonOfficer(**person_officer_data)
            person_officer.catalog(data=person_officer_data)

        # Handle company-related officer data.
        elif pp_type == "Corporation":
            company_number = extract_company_number_from_url(link)
            if company_number:
                company_data = {
                    "company_number": company_number,
                    "company_name": name,
                    "jurisdiction": extract_jurisdiction_from_url(link),
                }
                company = Company.fetch(
                    where=[Company.company_number == company_number], limit=1
                )
                if not company:
                    company = Company(**company_data)
                    company.catalog(data=company_data)

                company_officer_data = {
                    "company_number": company_number,
                    "officer_id": officer.id,
                    "role": role,
                }
                company_officer = CompanyOfficer(**company_officer_data)
                company_officer.catalog(data=company_officer_data)

        # If the officer has a link, load the detailed officer page to get full data.
        if link:
            officer_detail_soup = load_html_content(officer_data["link"])

            # Extract address from the officer detail page.
            if address_element := officer_detail_soup.find("dd", class_="address"):
                address = address_element.text.strip()
                officer_data["address"] = address
                if pp_type == "Person":
                    catalog_people_address(address, person.id)
                elif pp_type == "Corporation":
                    catalog_company_address(address, company.company_number)

            # Extract and update other fields if available.
            if name_element := officer_detail_soup.find("h1"):
                officer_data["name"] = name_element.text.strip()
            if role_element := officer_detail_soup.find("dt", string="Position"):
                officer_data["role"] = role_element.find_next_sibling("dd").text.strip()
            if status_element := officer_detail_soup.find("span", class_="status"):
                officer_data["status"] = status_element.text.strip()
            if start_date_element := officer_detail_soup.find(
                "div", class_="start_date"
            ):
                officer_data["start_date"] = start_date_element.text.strip()

            # Update the officer record with the new data.
            officer.catalog(data=officer_data)

        theseofficers.append(officer_data)

    # Process different types of officer lists: 'attribute_item' and 'officer'
    for item in soup.find_all("li", class_="attribute_item"):
        process_officer_item(item)

    for item in soup.find_all("li", class_="officer"):
        process_officer_item(item)

    if not theseofficers:
        logger.debug(f"{i()}⛏️🖨️ No officers extracted.")

    section("EXITING --- SCRAPING OFFICERS", color="green", justification="center")

    return theseofficers
