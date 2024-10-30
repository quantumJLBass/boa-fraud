from typing import Any, Dict, Union

from bs4 import BeautifulSoup, Tag

from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def share_parcel(soup: Union[BeautifulSoup, Tag]) -> Dict[str, Any]:
    """
    Extracts share parcel data from the HTML page.

    Parameters:
    ----------
    soup : BeautifulSoup or Tag
        The BeautifulSoup object representing the HTML document.
    relationship_type : str
        Type of relationship (object or subject) to extract.

    Returns:
    -------
    dict
        A dictionary containing the extracted share parcel data.
    """

    if not ensure_soup(soup, "SHARE PARCEL"):
        return []
    relationship_type = "some type"
    logger.info(f"{i()} Extracting share parcel ({relationship_type})")
    share_parcel_data = {}

    share_parcel_table = soup.find("table", class_="share_parcel")
    if share_parcel_table:
        rows = share_parcel_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) > 1:
                parcel = {
                    "Parcel ID": cells[0].get_text(strip=True),
                    "Company": cells[1].get_text(strip=True),
                    "Shares": cells[2].get_text(strip=True),
                }
                share_parcel_data[parcel["Parcel ID"]] = parcel

        logger.info(
            f"{i()} Extracted {relationship_type} share parcels: {share_parcel_data}"
        )
    else:
        logger.warning(f"{i()} Share parcel table not found.")

    section("EXITING --- SCRAPING SHARE PARCEL", color="green", justification="center")

    return share_parcel_data
