# utils.py
import json

# import random
import re

# import time
import traceback
from typing import Dict, List, Tuple, Union  # , Any

import dateparser
import probablepeople as pp

# import psutil
import requests

from services.applogging import logger  # , section
from services.webdriver import get_random_user_agent
from settings.settings import MIN_CONTENT_SIZE, SKIP_HTTP_CODES, i

# import gs


# from utils.useollama import *
# URLCatalog, RoleType, , Base, Address, Person,
# Company, Link, Attribute, Assertion, Filing,
# Event, Officer, PersonOfficer, CompanyOfficer,
# PeopleAddress, CompanyAddress, RelatedRelationship,
# SubsidiaryRelationship, IdentifierDelegate, TotalShare,
# Publication, Classification, GazetteNotice,
# TrademarkRegistration, LEIData, LEIEntityDetail,
# LEIAddress, IndustryCode, CompanyIndustryCode,

display_debug = True


def check_content_length(url: str) -> tuple[bool, int]:
    """
    Performs a GET request with stream=True and checks the content length by streaming.

    Args:
        url (str): The URL to fetch the headers for.

    Returns:
        bool: True if the content length is greater than the minimum size, False otherwise.
        int: The HTTP status code.
    """
    user_agent = get_random_user_agent()
    headers = {"User-Agent": user_agent}

    try:
        response = requests.get(
            url, headers=headers, allow_redirects=True, stream=True, timeout=5
        )
        status_code = response.status_code
        pattern = next((p for p in MIN_CONTENT_SIZE if p in url), None)
        min_size = MIN_CONTENT_SIZE.get(pattern, 1600)  # Default min size is 1600 bytes

        # Log all information from the response
        logger.info(f"⚠️📄🌎🚧 HEADERS FOR URL {url}")
        logger.info(f"⚠️📄🌎🚧Status Code: {status_code}")
        logger.info("⚠️📄🌎🚧Response Headers:")
        for header, value in response.headers.items():
            logger.info(f"⚠️📄🌎🚧{header}: {value}")
        logger.info(f"⚠️📄🌎🚧URL: {response.url}")
        logger.info(f"⚠️📄🌎🚧cookies: {response.cookies}")
        for name, value in response.cookies.items():
            logger.info(f"⚠️📄🌎🚧cookie:: {name}: {value}")
        logger.info(f"⚠️📄🌎🚧Encoding: {response.encoding}")
        logger.info(f"⚠️📄🌎🚧History: {response.history}")
        logger.info(f"⚠️📄🌎🚧Elapsed Time: {response.elapsed}")
        logger.info("⚠️📄🌎🚧Request Headers:")
        for header, value in response.request.headers.items():
            logger.info(f"⚠️📄🌎🚧{header}: {value}")
        logger.info(f"⚠️📄🌎🚧Request URL: {response.request.url}")
        logger.info(f"⚠️📄🌎🚧Request hooks: {response.request.hooks}")
        logger.info(f"⚠️📄🌎🚧Request method: {response.request.method}")
        logger.info(f"⚠️📄🌎🚧Request body: {response.request.body}")

        # Reading raw content
        raw_content = b""
        for chunk in response.iter_content(chunk_size=1024):
            raw_content += chunk
        raw_content_length = len(raw_content)

        # Actual content length
        # content_length = len(response.content)

        # Log content lengths
        logger.info(f"⚠️📄🌎🚧Request raw content_length: {raw_content_length}")
        # logger.info(f"⚠️📄🌎🚧Request content content_length: {content_length}")

        # Log first 100 bytes of the raw content for verification
        logger.info(f"⚠️📄🌎🚧raw content: {raw_content}")

        # Detailed raw response log
        logger.info(
            f"⚠️📄🌎🚧Raw Response: HTTP version: {response.raw.version}, Status: {response.raw.status}, Reason: {response.raw.reason}, Headers: {response.raw.headers}"
        )

        # Detailed cookies log
        for cookie in response.cookies:
            logger.info(
                f"⚠️📄🌎🚧Cookie: {cookie.name} = {cookie.value}, Domain: {cookie.domain}, Path: {cookie.path}, Expires: {cookie.expires}"
            )

        if status_code in SKIP_HTTP_CODES:
            logger.info(
                f"⏭️🌎🚧 CONTENT CHECK ----- Skipping URL {url} due to HTTP status code: {status_code}"
            )
            return False, status_code

        if raw_content_length < min_size:
            logger.info(
                f"⏭️🌎🚧 CONTENT CHECK ----- Skipping URL {url} due to content length: {raw_content_length} bytes (min size: {min_size} bytes)"
            )
            return False, status_code

        logger.info(
            f"⏭️🌎✅ CONTENT CHECK ----- {url} has sufficient content length: {raw_content_length} bytes (min size: {min_size} bytes)"
        )
        return True, status_code
    except requests.RequestException as e:
        logger.error(
            f"💀💥🌎🚧 CONTENT CHECK ----- Error fetching headers for {url}: {e}"
        )
        logger.error(f"{i()}{traceback.format_exc()}")
        return False, -1


def normalize_textblocks(text: str) -> str:
    """
    Normalizes a given text by removing newlines, tabs, and non-breaking spaces, replacing multiple spaces with a single space,
    removing specific strings, and stripping leading/trailing spaces.

    Parameters:
        text (str): The text to be normalized.

    Returns:
        str: The normalized text.


    """
    logger.debug(f"{i()}✍️〽️NORMALIZE TEXT ----- Text before normalization: {text}")
    # Remove newlines, tabs, and non-breaking spaces
    text = re.sub(r"[\n\r\t\u00a0]+", " ", text)

    # Replace multiple spaces with a single space
    text = re.sub(r"\s+", " ", text)

    # Remove specific strings
    text = (
        text.replace(" (US)", "")
        .replace("United States", "")
        .replace(" UNITED STATES", "")
    )
    #
    # Strip leading/trailing spaces
    text = text.strip()
    logger.debug(f"{i()}✅✍️〽️ NORMALIZE TEXT ----- Text after normalization: {text}")

    return text


def load_json_data() -> (
    Tuple[Dict[str, str], Dict[str, str], List[Dict[str, Union[str, int]]]]
):
    """
    Load the JSON data from the 'address-normalization-data.json' file and return the address parts, directionals, and US state cities.

    Returns:
        Tuple[Dict[str, str], Dict[str, str], List[Dict[str, Union[str, int]]]]: A tuple containing the address parts, directionals, and US state cities.
    """
    with open("odd&ends/address-normalization-data.json", encoding="utf-8") as fc:
        data = json.load(fc)

    this_address_parts = data["address_parts"]
    this_directionals = data["directionals"]
    this_us_state_cities = data["us_state_cities"]

    return this_address_parts, this_directionals, this_us_state_cities


address_parts, directionals, us_state_cities = load_json_data()


def convert_name_to_last_first_mi(name: str) -> str:
    """
    Convert a name in the format "First Middle Last" or "Last, First Middle" to "Last, First MI, Suffix".

    This function takes a name in various formats such as "First Middle Last", "Last, First Middle", and
    converts it to the format "Last, First MI, Suffix". The middle initial is extracted from the middle
    name if not provided, and generational suffixes are included if present.

    Parameters:
    ----------
    name : str
        The name to be converted. It can be in the format "First Middle Last", "Last, First Middle",
        or other variations handled by probablepeople.

    Returns:
    -------
    str
        The converted name in the format "Last, First MI, Suffix".

    Example:
        >>> convert_name_to_last_first_mi("John Smith Doe")
        'Doe, John S'
        >>> convert_name_to_last_first_mi("Doe, John Smith")
        'Doe, John S'
        >>> convert_name_to_last_first_mi("John Q. Public Jr.")
        'Public, John Q, Jr.'
        >>> convert_name_to_last_first_mi("Dr. Emily R. Stone")
        'Stone, Emily R'
    """
    logger.debug(f"{i()}♻️ ✍️ Converting name: {name}")
    try:
        parsed_name, name_type = pp.tag(name)
        if name_type == "Person":
            parts = {
                "PrefixMarital": parsed_name.get("PrefixMarital", "").strip(),
                "PrefixOther": parsed_name.get("PrefixOther", "").strip(),
                "GivenName": parsed_name.get("GivenName", "").strip(),
                "FirstInitial": parsed_name.get("FirstInitial", "").strip(),
                "MiddleName": parsed_name.get("MiddleName", "").strip(),
                "MiddleInitial": parsed_name.get("MiddleInitial", "").strip(),
                "Surname": parsed_name.get("Surname", "").strip(),
                "LastInitial": parsed_name.get("LastInitial", "").strip(),
                "SuffixGenerational": parsed_name.get("SuffixGenerational", "").strip(),
                "SuffixOther": parsed_name.get("SuffixOther", "").strip(),
                "Nickname": parsed_name.get("Nickname", "").strip(),
            }

            # If MiddleName is present but not MiddleInitial, derive MiddleInitial from MiddleName
            if parts["MiddleName"] and not parts["MiddleInitial"]:
                parts["MiddleInitial"] = parts["MiddleName"][0]

            # Construct new name with or without SuffixGenerational
            new_name = f"{parts['Surname']}, {parts['GivenName']} {parts['MiddleInitial']}".strip()
            if parts["SuffixGenerational"]:
                new_name = f"{new_name}, {parts['SuffixGenerational']}"

            logger.debug(f"{i()}✅ ✍️ Converted name: {new_name}")
            return new_name
        else:
            logger.debug(f"{i()}✅ ✍️ {name} read as a type of {name_type}")
            return name
    except pp.RepeatedLabelError as e:
        logger.error(f"{i()}🔹🚨🚩🌍📫〽️✍️🛑Error parsing name: {e}")
        logger.error(f"{i()}🔹🚨🚩🌍📫〽️✍️🛑Original String: {e.original_string}")
        logger.error(f"{i()}🔹🚨🚩🌍📫〽️✍️🛑Parsed String: {e.parsed_string}")
        logger.error(traceback.format_exc())
        return name


def normalize_date(date_string) -> Union[str, None]:
    """
    Normalizes various date formats to YYYY-MM-DD.

    Args:
        date_string (str): The date string to normalize.

    Returns:
        str: The normalized date in YYYY-MM-DD format, or None if parsing fails.
    """
    try:
        # Parse the date string
        parsed_date = dateparser.parse(
            date_string,
            settings={"PREFER_DAY_OF_MONTH": "first", "PREFER_DATES_FROM": "past"},
        )

        # If parsing is successful, return the formatted date
        if parsed_date:
            return parsed_date.strftime("%Y-%m-%d")
        else:
            return None
    except Exception as e:
        logger.error(f"{i()}🛑🧺🚨 Error normalizing date '{date_string}': {str(e)}")
        logger.error(f"{traceback.format_exc()}")
        return None


def determine_address_type(dt_text: str) -> str:
    """
    Determines the address type based on the dt_text.

    Args:
        dt_text (str): The text of the dt element.

    Returns:
        str: The determined address type code.
    """
    from db.dbefclasses import AddressType

    dt_text_lower = dt_text.lower()
    address_types = AddressType.fetch(columns=["code", "name"])
    for code, name in address_types:
        if name.lower() in dt_text_lower:
            return code
    return "company"  # Default to company address if type is unclear
