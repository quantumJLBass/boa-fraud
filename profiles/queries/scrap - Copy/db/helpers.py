import re

# from services.applogging import logger
from settings import *
from utils import *

# from scraper import *
# from typing import List, Dict, Union, Tuple


# import json
# import os
# from typing import Dict, Any


# def build_conditions(where: list):
#     """
#     Builds SQLAlchemy conditions from a structured list.

#     Args:
#         where (list): A list of conditions with strings or lists of conditions.
#                     Use '&' or no prefix for 'AND', '|' for 'OR'.


#     Returns:
#         list: A list of SQLAlchemy conditions.
#     """
#     conditions = []
#     for condition in where:
#         if isinstance(condition, list):
#             sub_conditions = [text(c.lstrip('|&')) for c in condition]
#             conditions.append(or_(*sub_conditions) if '|' in condition[0] else and_(*sub_conditions))
#         else:
#             conditions.append(text(condition.lstrip('|&')))
#     return conditions
def extract_occurrence_number(link):
    """
    Extracts the occurrence number from the link if it matches the expected pattern.
    """
    match = re.search(r"https://opencorporates.com/officers/(\d+)", link)
    if match:
        return match.group(1)
    return None


def extract_event_dates(description):
    """
    Extract start and end dates from the event description.

    Args:
        description (str): The event description containing dates.

    Returns:
        Tuple[str, str]: The start and end dates extracted from the description.
    """
    dates = extract_dates(description)
    if len(dates) > 1:
        return sorted(dates)[:2]
    elif len(dates) == 1:
        return dates[0], ""
    else:
        return "", ""


def extract_dates(textstr):
    """
    Extracts all date strings from the given text.

    Args:
        text (str): The input text containing dates.

    Returns:
        list: A list of date strings found in the text.
    """
    date_pattern = r"\b(?:\d{4}[/-]\d{2}[/-]\d{2}|\d{2}[/-]\d{2}[/-]\d{4}|\d{2}[/-]\d{2}[/-]\d{2})\b"
    matches = re.findall(date_pattern, textstr)
    return matches
