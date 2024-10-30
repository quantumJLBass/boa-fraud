from typing import Dict, List, Union

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def industry_codes(soup: Union[BeautifulSoup, Tag]) -> List[Dict[str, str]]:
    """
    Extracts industry codes information from a BeautifulSoup object representing a section of HTML with industry codes data.

    This function processes the given BeautifulSoup object to extract industry code information.
    If the object is invalid, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with industry codes data.

    Returns:
        list: A list of dictionaries containing the extracted industry code information, where each dictionary represents an industry code.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <div class="industry-codes">
        ...     <p>NAICS: 541330 - Engineering Services</p>
        ...     <p>SIC: 8711 - Engineering Services</p>
        ... </div>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> industry_codes(soup)
        [{'Type': 'NAICS', 'Code': '541330', 'Description': 'Engineering Services'},
        {'Type': 'SIC', 'Code': '8711', 'Description': 'Engineering Services'}]
    """
    from db.dbefclasses import CompanyIndustryCode, IndustryCode

    if not ensure_soup(soup, "INDUSTRY CODES"):
        return []

    codes = []

    industry_codes_element = soup.find("div", class_="industry-codes")
    if industry_codes_element:
        for p in industry_codes_element.find_all("p"):
            code_type, code_info = p.text.split(":", 1)
            code, description = code_info.strip().split(" - ", 1)

            code_data = {
                "type": code_type.strip(),
                "code": code.strip(),
                "description": description.strip(),
            }

            industry_code = IndustryCode(**code_data)
            industry_code.catalog(data=code_data)

            company_industry_code = CompanyIndustryCode(
                company_number=gs.current_company_number, industry_code=industry_code
            )
            company_industry_code.catalog(
                data={
                    "company_number": gs.current_company_number,
                    "industry_code_id": industry_code.id,
                }
            )

            codes.append(code_data)
            logger.debug(
                f"{i()}🏭 INDUSTRY CODES -- Saved industry code to database: {code_type} - {code}"
            )

    if not codes:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩INDUSTRY CODES -- No industry codes extracted.")

    section(
        "EXITING --- SCRAPING INDUSTRY CODES", color="green", justification="center"
    )

    return codes


# def extract_industry_codes(
#     soup: Union[BeautifulSoup, Tag]
# ) -> List[Dict[str, str]]:
#     """
#     Extracts industry codes from the provided BeautifulSoup object.

#     :param soup: A BeautifulSoup object containing the HTML content to extract industry codes from.
#     :type soup: Union[BeautifulSoup, Tag]
#     :return: A list of dictionaries containing industry code information.
#     :rtype: List[Dict[str, str]]
#     """
#     section("SCRAPING INDUSTRY CODES")
#     if not soup or not hasattr(soup, 'find'):
#         logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩INDUSTRY CODES -- Invalid soup object in extract_industry_codes.")
#         return []

#     logger.debug(f"{i()}⛏️🖨️ INDUSTRY CODES -- Extracting data out of a string {len(soup.text) if soup else 0} long")
#     logger.debug(f"{i()}⛏️🖨️ INDUSTRY CODES -- Extracting from {soup.prettify()}")

#     industry_codes = []


#     tbody = soup.find('tbody')
#     if tbody:
#         for row in tbody.find_all('tr'):
#             cells = row.find_all('td')
#             if len(cells) >= 3:
#                 industry_code_data = {
#                     'code': cells[0].text.strip(),
#                     'description': cells[1].text.strip(),
#                     'code_scheme': cells[2].text.strip()
#                 }
#                 industry_code = IndustryCode(**industry_code_data)
#                 industry_code.catalog_record(data=industry_code_data)

#                 cic = {
#                     'company_number': gs.current_company_number,
#                     'industry_code_id': industry_code.id
#                 }
#                 company_industry_code = CompanyIndustryCode(**cic)
#                 company_industry_code.catalog_record(data=cic)

#                 industry_codes.append(industry_code)

#     if not industry_codes:
#         logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩INDUSTRY CODES -- No industry codes extracted.")

#     return industry_codes
