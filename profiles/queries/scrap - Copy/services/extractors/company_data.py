from typing import Dict, Optional, Union  # List,

from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse

import gs
from db.dbefclasses import Company, Jurisdiction
from services import extractors as extract
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i

# from sqlalchemy.orm import object_session


def get_jurisdiction(jurisdiction_name: str) -> Optional[Jurisdiction]:
    """
    Retrieves a random jurisdiction record from the database based on the jurisdiction name.

    Parameters:
    ----------
    jurisdiction_name : str
        The name of the jurisdiction to look up.

    Returns:
    -------
    Jurisdiction or None
        The jurisdiction record if found, otherwise None.
    """
    if not jurisdiction_name:
        return None

    logger.info(f"{i()}📊 Fetching random jurisdiction: {jurisdiction_name}")

    jurisdiction_record = Jurisdiction.fetch(
        limit=1,
        where=[f"name='{jurisdiction_name}'"],
        sort_by="id",  # Fetch a random record
    )

    return jurisdiction_record


def extract_company_name(soup: Union[BeautifulSoup, Tag]) -> Optional[str]:
    """
    Extracts the company name from the HTML document.

    Parameters:
    ----------
    soup : BeautifulSoup or Tag
        The BeautifulSoup object representing the HTML document.

    Returns:
    -------
    str or None
        The company name if found, otherwise None.
    """
    name_element = soup.find("h1", class_="wrapping_heading")
    if not name_element:
        logger.warning(f"{i()}🛑 Company name not found.")
        return None

    company_name = (
        name_element.text.replace("\n", " ").replace("branch", "BRANCH").strip()
    )
    full_company_name = (
        f"{company_name} ({gs.current_jurisdiction} - {gs.current_company_number})"
    )
    logger.info(f"{i()}🏢📊 Extracted company name: {full_company_name}")

    return full_company_name


def extract_attributes(soup: Union[BeautifulSoup, Tag]) -> Dict[str, str]:
    """
    Extracts the attributes from the company page.

    Parameters:
    ----------
    soup : BeautifulSoup or Tag
        The BeautifulSoup object representing the HTML document.

    Returns:
    -------
    dict
        A dictionary containing the extracted attributes.
    """
    attributes_element = soup.find("dl", class_="attributes")
    if attributes_element:
        attributes = extract.attributes(attributes_element)
        logger.info(f"{i()}📊 Extracted attributes: {attributes}")
        return attributes
    else:
        logger.warning(f"{i()}🛑 Attributes section not found.")
        return {}


def save_company_to_db(
    company_obj: Dict[str, Union[str, int, Dict[str, str]]]
) -> Company:
    """
    Saves the company data to the database.

    Parameters:
    ----------
    company_obj : dict
        The dictionary containing the company data to save.

    Returns:
    -------
    Company
        The saved company entity.
    """
    company = Company(**company_obj)
    company.catalog(data=company_obj)
    logger.info(
        f"{i()}🏢📊✅ COMPANY DATA SAVED to database: {company_obj.get('company_name')}"
    )
    return company


def company_data(
    soup: Union[BeautifulSoup, Tag], url: str
) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Extracts and saves company data from a given BeautifulSoup object representing a company's HTML page.

    Parameters:
    ----------
    soup : BeautifulSoup or Tag
        The BeautifulSoup object representing the HTML document.

    Returns:
    -------
    dict
        A dictionary containing the extracted company data, including the company name, attributes, and jurisdiction info.
    """
    section("SCRAPING COMPANY DATA", color="orange1", justification="right")
    company_obj = {}

    if not soup or not hasattr(soup, "find_all"):
        logger.warning(f"{i()}🛑 Invalid soup object passed.")
        return company_obj

    # Extract Company Name
    company_name = extract_company_name(soup)
    if not company_name:
        return company_obj
    company_obj["company_name"] = company_name

    # Extract jurisdiction
    jurisdiction_id = None
    try:
        jurisdiction_name = (
            soup.find("dl", class_="attributes")
            .find("dt", text="Jurisdiction")
            .find_next_sibling("dd")
            .text.strip()
        )

        if jurisdiction_name:
            jurisdiction_id = get_jurisdiction(jurisdiction_name).id
    except AttributeError:
        logger.warning(f"{i()}⚠️⚠️⚠️ Jurisdiction not found.")

    # Extract status and company type
    status_name = None
    company_type_name = None
    try:
        status_name = (
            soup.find("dl", class_="attributes")
            .find("dt", text="Status")
            .find_next_sibling("dd")
            .text.strip()
        )
    except AttributeError:
        logger.warning(f"{i()}⚠️⚠️⚠️ Status not found.")

    try:
        company_type_name = (
            soup.find("dl", class_="attributes")
            .find("dt", text="Company Type")
            .find_next_sibling("dd")
            .text.strip()
        )
    except AttributeError:
        logger.warning(f"{i()}⚠️⚠️⚠️ Company Type not found.")

    # Extract incorporation date and handle None correctly
    incorporation_date = None
    try:
        incorporation_date_span = (
            soup.find("dl", class_="attributes")
            .find("dt", text="Incorporation Date")
            .find_next_sibling("dd")
            .find("span", {"datetime": True})
        )
        if incorporation_date_span:
            incorporation_date_text = incorporation_date_span[
                "datetime"
            ]  # Extract the datetime attribute
            logger.info(f"{i()}  incorporation_date_text: {incorporation_date_text}")
            incorporation_date = parse(
                incorporation_date_text
            ).date()  # Parse date string into Python date object
    except (AttributeError, ValueError):
        logger.warning(f"{i()} ⚠️⚠️⚠️ Incorporation Date not found or invalid.")

    # Populate company data
    company_obj.update(
        {
            "company_number": gs.current_company_number,
            "status": status_name,
            "incorporation_date": incorporation_date,  # Make sure this is None if not found
            "company_type": company_type_name,
            "jurisdiction_id": jurisdiction_id,
        }
    )
    logger.info(f"{i()}🔍🔍🔍 Company data extracted: {company_obj}")
    # Save company data to the database
    company_entity = save_company_to_db(company_obj)

    # Now extract attributes
    attributes = extract_attributes(soup)
    logger.info(f"{i()}🔍🔍🔍 attributes: {attributes}")

    # Update company with extracted attributes
    company_update_fields = {
        "status": attributes.get("Status", ""),
        "incorporation_date": (
            parse(attributes.get("Incorporation Date", "")).date()
            if attributes.get("Incorporation Date")
            else None
        ),
        "company_type": attributes.get("Company Type", ""),
    }
    logger.info(f"{i()}🔍🔍🔍 company_update_fields: {company_update_fields}")
    # Update the company_entity object
    for field, value in company_update_fields.items():
        setattr(company_entity, field, value)

    logger.info(f"{i()}🔍🔍🔍 company_entity: {company_entity}")
    # Save the updated company_entity to the database
    company_entity.catalog(data=company_update_fields)
    logger.info(
        f"{i()}🏢📊 Company data updated with attributes: {company_update_fields}"
    )

    # Extract previous names
    company_obj["Previous Names"] = extract.company_akas(soup)

    company_obj["people"] = extract.people(soup)
    # Extract assertions
    assertions_element = soup.find("div", id="assertions")
    if assertions_element:
        company_obj["Assertions"] = extract.assertions(assertions_element)
    else:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩SCRAPPING ISSUE --- Assertions section not found.")

    # Extract links
    company_obj["Links"] = extract.links(soup, url)

    section("EXITING --- SCRAPING Company", color="green", justification="center")

    return company_obj
