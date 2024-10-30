import re
from typing import Dict, List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from services.url_handlers import (
    extract_company_number_from_url,
    extract_jurisdiction_from_url,
)
from settings.settings import i

# from utils.useollama import


def relationships(
    soup: Union[BeautifulSoup, Tag], url: str = None
) -> List[Dict[str, str]]:
    """
    Extracts relationships information from a BeautifulSoup object representing a section of HTML with relationships data.

    This function processes the given BeautifulSoup object to extract relationship information.
    If the object is invalid, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with relationships data.
        pattern (str): The pattern used to identify the relationship type.

    Returns:
        list: A list of dictionaries containing the extracted relationship information, where each dictionary represents a relationship. Each dictionary contains the following keys:
            - 'Company' (str): The name of the company.
            - 'Company ID' (str): The ID of the company.
            - 'Jurisdiction' (str): The jurisdiction of the relationship.
            - 'Status' (str): The status of the relationship.
            - 'Type' (str): The type of the relationship.
            - 'Link' (str): The link associated with the relationship.
            - 'Start Date' (str): The start date of the relationship.
            - 'End Date' (str): The end date of the relationship.
            - 'statement_link' (str): The link to the relationship statement.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <table>
        ...   <tbody>
        ...     <tr>
        ...       <td><a class="company" href="/company/1">Example Company</a></td>
        ...       <td><a class="jurisdiction_filter" href="/jurisdiction/1">Example Jurisdiction</a></td>
        ...       <td><span class="status">Active</span></td>
        ...     </tr>
        ...   </tbody>
        ... </table>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_relationships(soup, "company_relationship_object")
        [{'Company': 'Example Company (Example Jurisdiction - 1)', 'Company ID': '1', 'Jurisdiction': 'Example Jurisdiction', 'Status': 'Active', 'Type': 'Company', 'Link': 'https://example.com/company/1', 'Start Date': '', 'End Date': '', 'statement_link': ''}]
    """
    from db.dbefclasses import RelatedRelationship, SubsidiaryRelationship

    if not ensure_soup(soup, "RELATIONSHIPS"):
        return []

    theserelationships = []
    if "branch_relationship_object" in url:
        relationship_type = "Parent"  # the listed company is the parent for the company in the url who is the branch
    elif "branch_relationship_subject" in url:
        relationship_type = "Branch"  # the listed company is the branch of the company in the url who is the parent
    elif "subsidiary_relationship_object" in url:
        relationship_type = "Parent"  # the listed company is the parent for the company in the url who is the subsidiary
    elif "subsidiary_relationship_subject" in url:
        relationship_type = "Subsidiary"  # the listed company is the subsidiary of the company in the url who is the parent
    else:
        relationship_type = (
            url.split("/")[-1]
            .replace("_relationship_", "")
            .replace("_", " ")
            .capitalize()
        )

    # company_number = gs.current_company_number
    # jurisdiction = gs.current_jurisdiction

    tbody = soup.find("tbody")
    if not tbody:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩RELATIONSHIPS -- No tbody found in soup.")
        return theserelationships

    tr_items = tbody.find_all("tr")
    for tr in tr_items:
        company_element = tr.find("a", class_="company")
        status_element = tr.find("span", class_="status")

        if company_element:
            company_name = company_element.text.strip()
            company_url = urljoin(gs.current_url, company_element["href"])
            related_company_id = extract_company_number_from_url(company_url)
            related_jurisdiction = extract_jurisdiction_from_url(company_url)
        else:
            company_text = tr.find("td").text.strip()
            company_name = re.sub(r"\([^)]*\)", "", company_text).strip()
            related_company_id = None
            related_jurisdiction = None
            if "(" in company_text and ")" in company_text:
                related_jurisdiction = company_text.split("(")[-1].split(")")[0]

        status = status_element.text.strip() if status_element else "Active"

        start_date_element = tr.find("span", class_="start_date")
        end_date_element = tr.find("span", class_="end_date")
        start_date = start_date_element.text.strip() if start_date_element else None
        end_date = end_date_element.text.strip() if end_date_element else None

        statement_element = tr.find_all("td")[-1].find("a")
        statement_link = (
            urljoin(gs.current_url, statement_element["href"])
            if statement_element
            else None
        )

        relationship_data = {
            "company_number": gs.current_company_number,
            "related_company": company_name,
            "related_company_id": related_company_id,
            "jurisdiction_code": related_jurisdiction,
            "status": status,
            "type": relationship_type,
            "link": company_url if company_element else None,
            "start_date": start_date,
            "end_date": end_date,
            "statement_link": statement_link,
        }

        if relationship_type in ["Parent", "Branch"]:
            relationship = RelatedRelationship(**relationship_data)
            relationship.catalog(data=relationship_data)
        elif relationship_type == "Subsidiary":
            subsidiary_relationship = SubsidiaryRelationship(**relationship_data)
            subsidiary_relationship.catalog(data=relationship_data)

        # Catalog URLs
        # if company_url:
        #     catalog_url(company_url, related_company_id, related_jurisdiction, gs.current_url)
        # if statement_link:
        #     catalog_url(statement_link, gs.current_company_number, jurisdiction, gs.current_url)

        theserelationships.append(relationship_data)

    if not theserelationships:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩RELATIONSHIPS -- No relationships extracted.")

    section("EXITING --- SCRAPING RELATIONSHIPS", color="green", justification="center")

    return theserelationships


# def relationships(
#     soup: Union[BeautifulSoup, Tag]
# ) -> List[Dict[str, str]]:
#     """
#     Extracts relationships information from a BeautifulSoup object representing a section of HTML with relationships data.

#     This function processes the given BeautifulSoup object to extract relationship information.
#     If the object is invalid, it returns an empty list.

#     Args:
#         soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with relationships data.

#     Returns:
#         list: A list of dictionaries containing the extracted relationship information, where each dictionary represents a relationship.

#     Example:
#         >>> from bs4 import BeautifulSoup
#         >>> html = '''
#         ... <div class="relationship">
#         ...     <h3>Parent Company</h3>
#         ...     <p>Company XYZ</p>
#         ... </div>
#         ... '''
#         >>> soup = BeautifulSoup(html, 'html.parser')
#         >>> relationships(soup)
#         [{'Type': 'Parent Company', 'Name': 'Company XYZ'}]
#     """
#     section("SCRAPING RELATIONSHIPS")
#     if not soup or not hasattr(soup, 'find_all'):
#         logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩RELATIONSHIPS -- Invalid soup object in relationships.")
#         return []

#     logger.debug(f"{i()}⛏️🖨️ RELATIONSHIPS -- Extracting data out of a string {len(soup.text) if soup else 0} long")
#     logger.debug(f"{i()}⛏️🖨️ RELATIONSHIPS -- Extracting from {soup.prettify()}")

#     theserelationships = []

#     for item in soup.find_all('div', class_='relationship'):
#         relationship_type = item.find('h3').text.strip() if item.find('h3') else ''
#         relationship_name = item.find('p').text.strip() if item.find('p') else ''

#         relationship_data = {
#             'company_number': gs.current_company_number,
#             'type': relationship_type,
#             'name': relationship_name
#         }
#         relationship = RelatedRelationship(**relationship_data)
#         relationship.catalog_record(data=relationship_data)
#         theserelationships.append(relationship_data)
#         logger.debug(f"{i()}🔗 RELATIONSHIPS -- Saved relationship to database: {relationship_type} - {relationship_name}")

#     if not theserelationships:
#         logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩RELATIONSHIPS -- No relationships extracted.")

#     return theserelationships
