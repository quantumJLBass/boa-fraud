from typing import Dict, List, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i

# def gazette_notices(
#     soup: Union[BeautifulSoup, Tag]
# ) -> List[Dict[str, str]]:
#     """
#     Extracts gazette notices information from a BeautifulSoup object representing a section of HTML with gazette notices data.

#     This function processes the given BeautifulSoup object to extract gazette notice information.
#     If the object is invalid, it returns an empty list.

#     Args:
#         soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with gazette notices data.

#     Returns:
#         list: A list of dictionaries containing the extracted gazette notice information, where each dictionary represents a gazette notice.

#     Example:
#         >>> from bs4 import BeautifulSoup
#         >>> html = '''
#         ... <div class="gazette-notice">
#         ...     <h3>Notice Title</h3>
#         ...     <p>Publication Date: 2023-01-01</p>
#         ...     <p>Notice Text</p>
#         ... </div>
#         ... '''
#         >>> soup = BeautifulSoup(html, 'html.parser')
#         >>> gazette_notices(soup)
#         [{'Title': 'Notice Title', 'Date': '2023-01-01', 'Text': 'Notice Text'}]
#     """
#     section("SCRAPING GAZETTE NOTICES")
#     if not soup or not hasattr(soup, 'find_all'):
#         logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩GAZETTE NOTICES -- Invalid soup object in gazette_notices.")
#         return []

#     logger.debug(f"{i()}⛏️🖨️ GAZETTE NOTICES -- Extracting data out of a string {len(soup.text) if soup else 0} long")
#     logger.debug(f"{i()}⛏️🖨️ GAZETTE NOTICES -- Extracting from {soup.prettify()}")

#     notices = []

#     for notice in soup.find_all('div', class_='gazette-notice'):
#         title = notice.find('h3').text.strip() if notice.find('h3') else ''
#         date = notice.find('p', string=lambda text: 'Publication Date' in text if text else False)
#         date = date.text.split(':')[-1].strip() if date else ''
#         text = notice.find('p', class_='notice-text').text.strip() if notice.find('p', class_='notice-text') else ''

#         notice_data = {
#             'company_number': gs.current_company_number,
#             'title': title,
#             'date': date,
#             'text': text
#         }
#         gazette_notice = GazetteNotice(**notice_data)
#         gazette_notice.catalog_record(data=notice_data)
#         notices.append(notice_data)
#         logger.debug(f"{i()}📰 GAZETTE NOTICES -- Saved gazette notice to database: {title} - {date}")

#     if not notices:
#         logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩GAZETTE NOTICES -- No gazette notices extracted.")

#     return notices


def gazette_notices(soup: Union[BeautifulSoup, Tag]) -> List[Dict[str, str]]:
    """
    Extracts gazette notice information from a BeautifulSoup object representing a table with gazette notice data.

    This function processes the given BeautifulSoup object to extract gazette notice information.
    If the object is invalid or there are insufficient columns in a row, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing a table with gazette notice data.

    Returns:
        list: A list of dictionaries containing the extracted gazette notice information, where each dictionary represents a gazette notice.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <tbody>
        ...   <tr>
        ...     <td>2023-01-01</td>
        ...     <td>Publication 1</td>
        ...     <td>Notice 1</td>
        ...     <td><a href="details_link">Details</a></td>
        ...   </tr>
        ...   <tr>
        ...     <td>2023-01-02</td>
        ...     <td>Publication 2</td>
        ...     <td>Notice 2</td>
        ...     <td><a href="details_link2">Details</a></td>
        ...   </tr>
        ... </tbody>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> extract_gazette_notices(soup)
        [{'company_number': '12345678', 'date': '2023-01-01', 'publication_id': '1', 'notice': 'Notice 1', 'link': 'https://url/details_link', 'classification_id': '1'},
        {'company_number': '12345678', 'date': '2023-01-02', 'publication_id': '2', 'notice': 'Notice 2', 'link': 'https://url/details_link2', 'classification_id': '2'}]
    """
    from db.dbefclasses import Classification, Company, GazetteNotice, Publication

    if not ensure_soup(soup, "GAZETTE NOTICES"):
        return []

    notices = []

    tbody = soup.find("tbody")
    if tbody:
        for row in tbody.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 4:
                pub_name = cells[1].text.strip()
                publication_company_record = None
                with gs.read() as readsession:
                    publication_company_record = (
                        readsession.query(Company).filter_by(name=pub_name).first()
                    )

                publication_data = {
                    "name": pub_name,
                    "company_number": (
                        publication_company_record.company_number
                        if publication_company_record
                        else None
                    ),
                }
                publication = Publication(**publication_data)
                publication.catalog(data=publication_data)

                class_name = cells[3].text.strip() if cells[3].text.strip() else None
                classification = Classification(
                    **{"classification": class_name}
                ).catalog(data={"classification": class_name})

                gazette_notice_data = {
                    "company_number": gs.current_company_number,
                    "date": cells[0].text.strip(),
                    "publication_id": publication.id if publication else None,
                    "notice": cells[2].text.strip(),
                    "link": (
                        urljoin(gs.current_url, details_link["href"])
                        if (details_link := cells[-1].find("a"))
                        else None
                    ),
                    "classification_id": classification.id if classification else None,
                }
                gazette_notice = GazetteNotice(**gazette_notice_data)
                gazette_notice.catalog(data=gazette_notice_data)
                notices.append(gazette_notice_data)

    if not notices:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩GAZETTE NOTICES -- No gazette notices extracted.")

    section(
        "EXITING --- SCRAPING GAZETTE NOTICES", color="green", justification="center"
    )

    return notices
