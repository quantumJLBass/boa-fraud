import json
import re
from typing import List, Union

from bs4 import BeautifulSoup, Tag

import gs
from db.dbefclasses import PersonAKA
from services.applogging import logger
from services.extractors.utils import ensure_soup
from settings.settings import i


def person_aka(soup: Union[BeautifulSoup, Tag]) -> List[str]:
    """
    Extracts and saves the previous names (AKAs) of the person from the HTML document.

    Parameters:
    ----------
    soup : BeautifulSoup or Tag
        The BeautifulSoup object representing the HTML document.

    Returns:
    -------
    list
        A list of previous names (AKAs) if found, otherwise an empty list.
    """
    akas = []

    if not ensure_soup(soup, "PEOPLE AKAS"):
        return []

    return akas
