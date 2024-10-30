from services.applogging import logger
from settings.settings import i
from utils.useollama import *


def render_assertions(assertions):
    """
    Formats the given assertions into a table with the format: "| Title | Description |".

    This function processes the given assertions dictionary to extract the information and format it into a table.
    The assertions dictionary should have the following structure:

    {
        'Company Addresses': [
            {
                'Title': 'Address Title',
                'Description': 'Address Description'
            },
            ...
        ],
        'Telephone Numbers': [
            {
                'Title': 'Phone Title',
                'Description': 'Phone Description'
            },
            ...
        ]
    }

    If the assertions dictionary is empty or None, an empty string is returned.

    Args:
        assertions (dict): A dictionary containing assertions data. It should have the keys 'Company Addresses' and/or 'Telephone Numbers',
            each of which should be a list of dictionaries. Each dictionary in the list should have the keys 'Title' and 'Description'.

    Returns:
        str: The formatted assertions table as a string. The table has the format:
            | Title | Description |
            |-------|-------------|
            | Address Title | Address Description |
            | Phone Title | Phone Description |
            ...
    """
    logger.info(f"{i()}✍️📑CREATING NOTE ---- format assertions table started")
    if not assertions:
        logger.info(f"{i()}❌✍️📑CREATING NOTE ---- Empty assertions")
        return ""
    assertion_list = f"| {'Title':<19} | {'Description':<55} |\n|{'':-<21}|{'':-<57}|\n"
    if "Company Addresses" in assertions:
        for address in assertions["Company Addresses"]:
            normalized_address = "[[" + normalize_address(address["Description"]) + "]]"
            assertion_list += f"| {address['Title']:<19} | {normalized_address:<55} |\n"
    if "Telephone Numbers" in assertions:
        for phone in assertions["Telephone Numbers"]:
            assertion_list += f"| {phone['Title']:<19} | {phone['Description']:<55} |\n"
    logger.info(f"{i()}✅✍️📑CREATING NOTE ---- format assertions table finished")
    return assertion_list
