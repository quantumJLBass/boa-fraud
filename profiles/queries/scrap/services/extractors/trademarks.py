from typing import Dict, List, Union

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def trademarks(soup: Union[BeautifulSoup, Tag]) -> List[Dict[str, str]]:
    """
    Extracts trademark information from a BeautifulSoup object representing a table with trademark data.

    This function processes the given BeautifulSoup object to extract trademark information.
    If the object is invalid or there are insufficient columns in a row, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing a table with trademark data.

    Returns:
        list: A list of dictionaries containing the extracted trademark information, where each dictionary represents a trademark.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <tbody>
        ...   <tr>
        ...     <td>Trademark 1</td>
        ...     <td>2023-01-01</td>
        ...     <td>Registered</td>
        ...   </tr>
        ...   <tr>
        ...     <td>Trademark 2</td>
        ...     <td>2023-01-02</td>
        ...     <td>Cancelled</td>
        ...   </tr>
        ... </tbody>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_trademarks(soup)
        [{'company_number': '12345678', 'trademark': 'Trademark 1', 'registration_date': '2023-01-01', 'status': 'Registered'},
        {'company_number': '12345678', 'trademark': 'Trademark 2', 'registration_date': '2023-01-02', 'status': 'Cancelled'}]
    """
    from db.dbefclasses import TrademarkRegistration

    if not ensure_soup(soup, "TRADEMARKS"):
        return []

    thesetrademarks = []

    tbody = soup.find("tbody")
    if tbody:
        for row in tbody.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 3:
                trademark_data = {
                    "company_number": gs.current_company_number,
                    "trademark": cells[0].text.strip(),
                    "registration_date": cells[1].text.strip(),
                    "status": cells[2].text.strip(),
                }
                trademark = TrademarkRegistration(**trademark_data)
                trademark.catalog(data=trademark_data)
                thesetrademarks.append(trademark_data)

    if not thesetrademarks:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩TRADEMARKS -- No trademarks extracted.")

    section("EXITING --- SCRAPING TRADEMARKS", color="green", justification="center")

    return thesetrademarks
