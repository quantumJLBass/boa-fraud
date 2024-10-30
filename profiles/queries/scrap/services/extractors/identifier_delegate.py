from typing import Dict, List, Union

from bs4 import BeautifulSoup, Tag

import gs
from services.applogging import logger, section
from services.extractors.utils import ensure_soup
from settings.settings import i


def identifier_delegate(soup: Union[BeautifulSoup, Tag]) -> List[Dict[str, str]]:
    """
    Extracts identifiers information from a BeautifulSoup object representing a section of HTML with identifiers data.

    This function processes the given BeautifulSoup object to extract identifier information.
    If the object is invalid, it returns an empty list.

    Args:
        soup (BeautifulSoup): A BeautifulSoup object representing the section of HTML with identifiers data.

    Returns:
        list: A list of dictionaries containing the extracted identifier information, where each dictionary represents an identifier.

    Example:
        >>> from bs4 import BeautifulSoup
        >>> html = '''
        ... <div id="data-table-identifier_delegate">
        ...     <table>
        ...         <tbody>
        ...             <tr>
        ...                 <td>LEI</td>
        ...                 <td><a href="https://search.gleif.org/#/record/529900NGGVF94UK6PG95">529900NGGVF94UK6PG95</a></td>
        ...                 <td></td>
        ...                 <td></td>
        ...                 <td><a href="/statements/1849233704">details</a></td>
        ...             </tr>
        ...         </tbody>
        ...     </table>
        ... </div>
        ... '''
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> identifier_delegate(soup)
        [{'company_number': '12345678', 'identifier_system': 'LEI', 'identifier': '529900NGGVF94UK6PG95', 'categories': '', 'external_link': 'https://search.gleif.org/#/record/529900NGGVF94UK6PG95', 'statement_link': '/statements/1849233704'}]
    """
    from db.dbefclasses import IdentifierDelegate

    if not ensure_soup(soup, "IDENTIFIERS"):
        return []

    identifiers = []

    identifier_table = soup.find("div", id="data-table-identifier_delegate")
    if identifier_table:
        tbody = identifier_table.find("tbody")
        if tbody:
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 5:
                    identifier_data = {
                        "company_number": gs.current_company_number,
                        "identifier_system": cells[0].text.strip(),
                        "identifier": cells[1].text.strip(),
                        "categories": cells[2].text.strip(),
                        "external_link": cells[1].find('a')['href'] if cells[1].find('a') else None,
                        "statement_link": cells[4].find('a')['href'] if cells[4].find('a') else None,
                    }
                    identifier = IdentifierDelegate(**identifier_data)
                    identifier.catalog(data=identifier_data)
                    identifiers.append(identifier_data)

    if not identifiers:
        logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩IDENTIFIERS -- No identifiers extracted.")

    section("EXITING --- SCRAPING IDENTIFIERS", color="green", justification="center")

    return identifiers


# def extract_identifiers(
#     soup: Union[BeautifulSoup, Tag]
# ) -> List[Dict[str, str]]:
#     """
#     Extracts identifier information from a BeautifulSoup object representing a table with identifier data.

#     This function processes the given BeautifulSoup object to extract identifier information.
#     If the object is invalid or there are insufficient columns in a row, it returns an empty list.

#     Args:
#         soup (BeautifulSoup): A BeautifulSoup object representing a table with identifier data.

#     Returns:
#         list: A list of dictionaries containing the extracted identifier information, where each dictionary represents an identifier.

#     Example:
#         >>> from bs4 import BeautifulSoup
#         >>> html = '''
#         ... <tbody>
#         ...   <tr>
#         ...     <td>Identifier System 1</td>
#         ...     <td>12345</td>
#         ...     <td>Category 1</td>
#         ...   </tr>
#         ...   <tr>
#         ...     <td>Identifier System 2</td>
#         ...     <td>67890</td>
#         ...     <td>Category 2</td>
#         ...   </tr>
#         ... </tbody>
#         ... '''
#         >>> soup = BeautifulSoup(html, 'html.parser')
#         >>> extract_identifiers(soup)
#         [{'company_number': '12345678', 'identifier_system': 'Identifier System 1', 'identifier': '12345', 'categories': 'Category 1'},
#          {'company_number': '12345678', 'identifier_system': 'Identifier System 2', 'identifier': '67890', 'categories': 'Category 2'}]
#     """
#     section("SCRAPING IDENTIFIERS")
#     if not soup or not hasattr(soup, 'find'):
#         logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩IDENTIFIERS -- Invalid soup object in extract_identifiers.")
#         return []

#     logger.debug(f"{i()}⛏️🖨️ IDENTIFIERS -- Extracting data out of a string {len(soup.text) if soup else 0} long")
#     logger.debug(f"{i()}⛏️🖨️ IDENTIFIERS -- Extracting from {soup.prettify()}")

#     identifiers = []

#     tbody = soup.find('tbody')
#     if tbody:
#         for row in tbody.find_all('tr'):
#             cells = row.find_all('td')
#             if len(cells) >= 3:
#                 identifier_data = {
#                     'company_number': gs.current_company_number,
#                     'identifier_system': cells[0].text.strip(),
#                     'identifier': cells[1].text.strip(),
#                     'categories': cells[2].text.strip()
#                 }
#                 identifier = IdentifierDelegate(**identifier_data)
#                 identifier.catalog_record(data=identifier_data)
#                 identifiers.append(identifier_data)

#     if not identifiers:
#         logger.debug(f"{i()}⛏️🖨️ 🛑🚨🚩IDENTIFIERS -- No identifiers extracted.")

#     return identifiers
