from services.applogging import logger
from services.notes import render_link
from settings.settings import i
from utils.utils import convert_name_to_last_first_mi


def render_officers(entries):
    """
    Formats a list of entries into a table for display in a note.

    This function takes a list of entries and formats them into a table for easy display in a note. Each entry is represented as a row in the table, with the following columns:
        - Name: The name of the entry, formatted as a link if a corresponding entity exists in the database.
        - Role: The role of the entry.
        - Status: The status of the entry ('active' or 'inactive').
        - Link: The link associated with the entry.

    Parameters:
    ----------
    entries (list): A list of dictionaries containing information about each entry. Each dictionary should have the following keys:
        - 'Name' (str): The name of the entry.
        - 'Role' (str): The role of the entry.
        - 'Status' (str): The status of the entry ('active' or 'inactive').
        - 'Link' (str): The link associated with the entry.
        - 'Type' (str): The type of the entry ('person' or 'corporation').
    entry_type (str, optional): The type of entry being formatted. Defaults to 'officer'.

    Returns:
    -------
    str: A string representing the entries in a table format. Each row of the table contains the following columns:
        - Name: The name of the entry, formatted as a link if a corresponding entity exists in the database.
        - Role: The role of the entry.
        - Status: The status of the entry ('active' or 'inactive').
        - Link: The link associated with the entry.

    Raises:
    ------
    None

    Notes:
    - If the input entries list is empty, an empty string is returned.
    - The function iterates over each entry in the entries list and creates a row in the table with the following information:
        - The name of the entry, formatted as a link if a corresponding entity exists in the database.
        - The role of the entry.
        - The status of the entry.
        - The link associated with the entry.
    - The function logs debug messages before and after the table formatting process.
    Example:
        >>> format_table([
        ...     {'Name': 'John Doe', 'Role': 'Officer', 'Status': 'Active', 'Link': 'https://example.com/johndoe'},
        ...     {'Name': 'Jane Smith', 'Role': 'Officer', 'Status': 'Inactive', 'Link': 'https://example.com/janesmith'}
        ... ])
        '| Name | Role | Status | Type | Link |\n|------|----|-----|--------|------|\n| [John Doe](https://example.com/johndoe) | Officer | Active | [Link](https://example.com/johndoe) |\n| [Jane Smith](https://example.com/janesmith) | Officer | Inactive | [Link](https://example.com/janesmith) |\n'
    """
    logger.info(f"{i()}CREATING NOTE ---- format officer table started")
    if not entries:
        return ""

    # n = max(len(e['Name']) for e in entries) + 4
    # r = max(len(e['Role']) for e in entries)
    # s = max(len(e['Status']) for e in entries)

    table = f"| {'Name':<20} | {'Role':<15} | {'Status':<10} | {'Type':<11} | Link |\n|--{'':-<20}|--{'':-<15}|--{'':-<10}|--{'':-<11}|------|\n"
    for entry in entries:
        name_link = convert_name_to_last_first_mi(entry["Name"])
        name_key, _ = (
            None,
            None,
        )  # must replace with a resolver... entity_exists(name_link)
        link = render_link(name_key if name_key else name_link, entry["Name"], True)
        table += f"| {link:<20} | {entry.get('Role', '-'):<15} | {entry.get('Status', '-'):<10} | {entry['Type']:<11} | [Link]({entry.get('Link', '#')}) |\n"
    logger.info(f"{i()}CREATING NOTE ---- format officer table finished")
    return table
