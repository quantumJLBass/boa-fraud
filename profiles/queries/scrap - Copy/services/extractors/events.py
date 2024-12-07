from typing import Dict, List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services import extractors as extract
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def events(soup: Union[BeautifulSoup, Tag]) -> List[Dict[str, str]]:
    """
    Extracts events information from a BeautifulSoup object representing a section of HTML with events data.

    This function processes the given BeautifulSoup object to extract event information.
    If the object is invalid or there is a mismatch between the number of <dt> and <dd> tags, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with events data.

    Returns:
        list: A list of dictionaries containing the extracted event information, where each dictionary represents an event.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <dl>
        ...   <dt>2023-01-01</dt>
        ...   <dd><a href="https://example.com/event">Event description</a></dd>
        ... </dl>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> events(soup)
        [{'Date': '2023-01-01', 'Description': 'Event description', 'Link': 'https://example.com/event'}]
    """
    from db.dbefclasses import Event

    if not ensure_soup(soup, "COMPANY EVENTS"):
        return []

    theseevents = []

    people = extract.people(soup)
    event_list = soup.find("dl", class_="oc-events-timeline")
    if event_list:
        dt_elements = event_list.find_all("dt")
        dd_elements = event_list.find_all("dd")

        for dt, dd in zip(dt_elements, dd_elements):
            date = dt.text.strip().replace("On ", "")
            description = dd.text.strip()
            link = dd.find("a")["href"] if dd.find("a") else None

            event_data = {
                "company_number": gs.current_company_number,
                "start_date": date,  # Assuming the date is the start date
                "description": description,
                "link": urljoin(gs.current_url, link) if link else None,
            }

            # Create an Event object and save it to the database
            event = Event(**event_data)
            event.catalog(data=event_data)
            theseevents.append(event)

            logger.debug(
                f"{i()}🗃️ COMPANY EVENTS -- Saved event to database: {date} - {description}"
            )

    if not theseevents:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩COMPANY EVENTS -- No company events extracted.")

    section(
        "EXITING --- SCRAPING COMPANY EVENTS", color="green", justification="center"
    )

    return theseevents
