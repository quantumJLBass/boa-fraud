from typing import Dict, Union

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def lei_data(soup: Union[BeautifulSoup, Tag]) -> Dict[str, Union[str, Dict[str, str]]]:
    """
    Extracts Legal Entity Identifier (LEI) data from a BeautifulSoup object representing a section of HTML with LEI data.

    This function processes the given BeautifulSoup object to extract LEI information.
    If the object is invalid or the information is not found, it returns an empty dictionary.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with LEI data.

    Returns:
        dict: A dictionary containing the extracted LEI information.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <div class="lei-data">
        ...     <p>LEI: 549300HGDDX6FKTG8X76</p>
        ...     <p>Legal Name: Example Company Ltd</p>
        ...     <p>Legal Address: 123 Main St, City, Country</p>
        ... </div>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> lei_data(soup)
        {'LEI': '549300HGDDX6FKTG8X76', 'Legal Name': 'Example Company Ltd', 'Legal Address': '123 Main St, City, Country'}
    """
    from db.dbefclasses import LEIAddress, LEIData, LEIEntityDetail

    if not ensure_soup(soup, "LEI DATA"):
        return []

    leiData = {}

    lei_element = soup.find("div", class_="lei-data")
    if lei_element:
        lei = lei_element.find(
            "p", string=lambda text: "LEI:" in text if text else False
        )
        legal_name = lei_element.find(
            "p", string=lambda text: "Legal Name:" in text if text else False
        )
        legal_address = lei_element.find(
            "p", string=lambda text: "Legal Address:" in text if text else False
        )

        if lei:
            leiData["LEI"] = lei.text.split(":")[-1].strip()
        if legal_name:
            leiData["Legal Name"] = legal_name.text.split(":")[-1].strip()
        if legal_address:
            leiData["Legal Address"] = legal_address.text.split(":")[-1].strip()

        if leiData:
            lei_record = LEIData(
                company_number=gs.current_company_number, lei=leiData.get("LEI", "")
            )
            lei_record.catalog(data=leiData)

            lei_address = LEIAddress(
                company_number=gs.current_company_number,
                address=leiData.get("Legal Address", ""),
            )
            lei_address.catalog(data={"address": leiData.get("Legal Address", "")})

            lei_entity_detail = LEIEntityDetail(
                company_number=gs.current_company_number,
                legal_name=leiData.get("Legal Name", ""),
            )
            lei_entity_detail.catalog(
                data={"legal_name": leiData.get("Legal Name", "")}
            )

            logger.debug(f"{i()}🆔 LEI DATA -- Saved LEI data to database: {leiData}")
    else:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩LEI DATA -- No LEI data found.")

    section("EXITING --- SCRAPING LEI DATA", color="green", justification="center")

    return leiData
