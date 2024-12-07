from services.applogging import *
from services.notes import render_link
from settings.settings import i
from utils.useollama import *
from utils.utils import *


def render_attributes(attributes):
    """
    Formats the given attributes into a table with the format "| Attribute | Value |".

    This function processes the given attributes dictionary to extract the information and format it into a table.
    The attributes dictionary should have the following structure:

    {
        'attribute1': 'value1',
        'attribute2': 'value2',
        'Parent': {'company_name': 'company_name_value', 'url': 'url_value'},
        ...
    }

    If the attributes dictionary is empty or None, an empty string is returned.

    Parameters:
    ----------
    attributes (dict): A dictionary containing attributes data. It should have string keys and values that are either
                    strings or dictionaries. The dictionaries should have keys 'company_name' and 'url'.

    Returns:
    -------
    str: The formatted attributes table as a string. The table has the format:
        | Attribute           | Value                                      |
        |---------------------|--------------------------------------------|
        | attribute1          | value1                                     |
        | attribute2          | value2                                     |
        | Parent              | [[company_name_value]] ([link](url_value)) |

    Example:
    --------
    >>> attributes = {
    ...     'Company Number': '0000155703',
    ...     'Status': 'Active',
    ...     'Parent': {'company_name': 'HALLIDAY, WATKINS & MANN, P.C.', 'url': '/companies/us_ut/1341274-0144'},
    ...     'Registered Address': '376 E 400 S, STE 300, SALT LAKE CITY, UT 84111-2906, United States',
    ...     'Agent Name': 'Jason Henderson',
    ...     'Agent Address': '38 SECOND AVE EAST, SUITE B, DICKINSON, ND 58601'
    ... }
    >>> print(format_general_data(attributes))
    | Attribute           | Value                                      |
    |---------------------|--------------------------------------------|
    | Company Number      | 0000155703                                 |
    | Status              | Active                                     |
    | Parent              | [[HALLIDAY, WATKINS & MANN, P.C.]] ([link](/companies/us_ut/1341274-0144)) |
    | Registered Address  | [[376 E 400 S, STE 300, SALT LAKE CITY, UT 84111-2906]] |
    | Agent Name          | [[Jason Henderson]] ([link to agent])      |
    | Agent Address       | [[38 SECOND AVE EAST, SUITE B, DICKINSON, ND 58601]] ([link to agent address]) |
    """
    logger.info(f"{i()}CREATING NOTE ---- format_general_data started")
    table = f"| {'Attribute':<18} | {'Value':<43} |\n|{'':-<20}|{'':-<45}|\n"
    for key, value in attributes.items():
        if isinstance(value, dict) and "company_name" in value and "url" in value:
            company_name = value.get("company_name", "")
            company_url = value.get("url", "")
            value = f"[[{company_name}]] ([link]({company_url}))"
        elif isinstance(value, list):
            value = ", ".join(value)
        if "Address" in key:
            value = f"[[{value}]]"
        if "Agent Name" in key:
            name_link = convert_name_to_last_first_mi(value)
            name_key, _ = (
                None,
                None,
            )  # we will want to make a resolver for the names. entity_exists(name_link)
            value = render_link(name_key if name_key else name_link, value, True)
        table += f"| {key:<18} | {value:<43} |\n"
    logger.info(f"{i()}CREATING NOTE ---- format_general_data finished")
    return table
