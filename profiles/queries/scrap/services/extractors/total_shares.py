from typing import Dict, Union

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def total_shares(soup: Union[BeautifulSoup, Tag]) -> Dict[str, str]:
    """
    Extracts total shares information from a BeautifulSoup object representing a section of HTML with total shares data.

    This function processes the given BeautifulSoup object to extract total shares information.
    If the object is invalid or the information is not found, it returns an empty dictionary.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with total shares data.

    Returns:
        dict: A dictionary containing the extracted total shares information.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <div id="data-table-total_shares">
        ...     <tbody>
        ...         <tr>
        ...             <td>1,000,000</td>
        ...             <td>Common Shares</td>
        ...         </tr>
        ...     </tbody>
        ... </div>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> total_shares(soup)
        {'Number': '1,000,000', 'Share Class': 'Common Shares'}
    """
    from db.dbefclasses import TotalShare

    if not ensure_soup(soup, "TOTAL SHARES"):
        return []

    total_shares_data = {}

    # Check for the new HTML structure
    table_wrapper = soup.find("div", id="data-table-total_shares")
    if table_wrapper:
        tbody = table_wrapper.find("tbody")
        if tbody:
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    total_shares_data["Number"] = cells[0].text.strip()
                    if cells[1].find("a"):
                        total_shares_data["Share Class"] = cells[1].find("a")["href"]
                    else:
                        total_shares_data["Share Class"] = cells[1].text.strip()

                    total_shares_record = TotalShare(
                        company_number=gs.current_company_number,
                        total_shares=total_shares_data.get("Number", ""),
                        share_value=total_shares_data.get("Share Class", ""),
                    )
                    total_shares_record.catalog(data=total_shares_data)
                    logger.debug(
                        f"{i()}📊 TOTAL SHARES -- Saved total shares to database: {total_shares_data}"
                    )
    else:
        logger.debug(
            f"{i()}⛏️🖨️ 🛑🚨🚩TOTAL SHARES -- No total shares information found."
        )

    section("EXITING --- SCRAPING TOTAL SHARES", color="green", justification="center")

    return total_shares_data
