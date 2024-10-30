import os
import json
import re
from datetime import datetime
# from urllib.parse import urljoin
from typing import List, Dict
from loguru import logger
from fuzzywuzzy import process, fuzz
from applogging import *
from settings import *
from utils import *
from useollama import *
# import gs

# Define the output directories for different types of entities
output_directories = {
    'person': "E:/_GIT/obsidian/BoA timeline/profiles/people/",
    'company': "E:/_GIT/obsidian/BoA timeline/profiles/corporations/",
    'address': "E:/_GIT/obsidian/BoA timeline/profiles/addresses/"
}

staging_directories = {
    'person': "E:/_GIT/obsidian/BoA timeline/profiles/people/staging/",
    'company': "E:/_GIT/obsidian/BoA timeline/profiles/corporations/staging/",
    'address': "E:/_GIT/obsidian/BoA timeline/profiles/addresses/staging/"
}

existing_notes_path = "file-folder-struc.txt"
cache_file_path = "cache.json"

# Initializer step to ensure staging folders exist
def ensure_staging_folders() -> None:
    """
    Ensures that staging directories for different types of entities exist.

    This function iterates over the values in the `staging_directories` dictionary
    and creates the corresponding directories if they do not already exist. It
    logs a message indicating that the staging directory has been ensured.

    Parameters:
    None

    Returns:
    None
    """
    for directory in staging_directories.values():
        os.makedirs(directory, exist_ok=True)
        logger.info(f"{i()}ENSURED ---- Staging directory exists at {directory}")

# Function to build or load the cache of existing notes and their aliases
def load_or_build_cache():
    """
    Loads the cache of existing notes and their aliases from a file or builds it if the file does not exist.

    This function checks if the cache file specified by `cache_file_path` exists. If it does, the function reads the contents of the file and returns the parsed JSON data. If the file does not exist, the function calls `build_existing_notes_cache` to build the cache and returns the result.

    Parameters:
    None

    Returns:
    dict: The cache of existing notes and their aliases.
    """
    if os.path.exists(cache_file_path):
        with open(cache_file_path, 'r', encoding='utf-8') as cache_file:
            return json.load(cache_file)
    else:
        return build_existing_notes_cache()

def build_existing_notes_cache():
    """
    Builds a cache of existing notes and their aliases.

    This function recursively walks through the directory "E:/_GIT/obsidian/BoA timeline/profiles/" and its subdirectories. For each .md file found, it reads the file content and extracts the file name and aliases using the `extract_aliases` function. The file name is converted to uppercase and the file path and aliases are stored in the `notes_cache` dictionary.

    The `notes_cache` dictionary is then serialized to a JSON file specified by `cache_file_path` with an indentation of 2.

    Returns:
        dict: A dictionary containing the cache of existing notes and their aliases.
    """
    notes_cache = {}
    for root, dirs, files in os.walk("E:/_GIT/obsidian/BoA timeline/profiles/"):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as note_file:
                    # logger.info(f"{i()}working with {file_path}")
                    note_content = note_file.read()
                    file_name = file.rsplit('.', 1)[0].upper()
                    aliases = extract_aliases(note_content)
                    notes_cache[file_name] = {
                        'path': file_path,
                        'aliases': aliases
                    }
    with open(cache_file_path, 'w', encoding='utf-8') as cache_file:
        json.dump(notes_cache, cache_file, indent=2)
    return notes_cache

def extract_aliases(
    note_content
):
    """
    Extracts aliases from the note content.

    This function searches for lines in the note content that start with "aka:" and extracts the aliases listed below it.

    Args:
        note_content (str): The content of the note.

    Returns:
        list: A list of aliases found in the note content, converted to uppercase.
    """
    aliases = []
    match = re.search(r'aka:\s*\n((\s*-\s*.*\n)+)', note_content, re.IGNORECASE)
    if match:
        alias_lines = match.group(1).strip().split('\n')
        aliases = [alias_line.strip()[1:].strip() for alias_line in alias_lines]
    return [alias.upper() for alias in aliases]

# Load the cache of existing notes
existing_notes_cache = load_or_build_cache()

# Function to find the closest match for a name in the cache
def find_closest_match(
    name,
    cache
):
    """
    Find the closest match for a name in the cache.

    Args:
        name (str): The name to find a match for.
        cache (dict): The cache of existing notes and their aliases.

    Returns:
        tuple: A tuple containing the closest match for the name and its score. Returns None if no match is found.
    """
    name = name.upper()
    all_names = list(cache.keys()) + [alias for data in cache.values() for alias in data['aliases']]
    match = process.extractOne(name, all_names, scorer=fuzz.token_sort_ratio)
    return match

# Function to check if an entity exists and return the best match path
def entity_exists(
    name
):
    """
    Check if an entity exists in the `existing_notes_cache` dictionary.

    Args:
        name (str): The name of the entity to check.

    Returns:
        tuple: A tuple containing the key and path of the entity if it exists in the cache,
            otherwise (None, None).

    This function searches for the closest match for the given `name` in the `existing_notes_cache`
    dictionary. If a match is found and its similarity score is above the threshold of 80, the function
    checks if the matched name is equal to the key or if it is present in the aliases list of the
    corresponding data. If a match is found, the function returns the key and path of the entity.
    Otherwise, it returns (None, None).

    Example usage:
    ```
    entity_exists("John Doe")  # Returns ("JOHN DOE", "path/to/johndoe.md") if found, otherwise (None, None)
    ```
    """

    closest_match = find_closest_match(name, existing_notes_cache)
    if closest_match and closest_match[1] > 80:  # Threshold for match confidence
        matched_name = closest_match[0]
        for key, data in existing_notes_cache.items():
            if matched_name == key or matched_name in data['aliases']:
                return key, data['path']
    return None, None

# Function to extract and format the date
def format_date(
    date_str
):
    """
    Formats a given date string into the 'YYYY-MM-DD' format.

    Args:
        date_str (str): The date string to be formatted.

    Returns:
        str: The formatted date string in the 'YYYY-MM-DD' format. If the date string cannot be parsed,
        the original date string is returned.
    """

    logger.info(f"{i()}FORMATTING ---- Date: {date_str}")
    try:
        date_part = re.split(r"\s\(", date_str)[0]
        date_obj = datetime.strptime(date_part, '%d %B %Y')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return date_str

# Function to extract entry branches, collaborators, and parents
def extract_additional_entries(
    data: Dict[str, List[Dict[str, str]]]
) -> Tuple[List[str], List[str], List[str]]:
    """
    Extracts additional entries from the given data dictionary.

    Args:
        data (dict): A dictionary containing the data to extract entries from. It should have the following keys:
            - 'Officers' (list): A list of dictionaries representing officers. Each dictionary should have the key 'Name'.
            - 'Branch_relationship' (list): A list of dictionaries representing branch relationships. Each dictionary should have the keys 'Company', 'Jurisdiction', and 'Type'.

    Returns:
        tuple: A tuple containing three lists:
            - entry_branches (list): A list of formatted links representing branches.
            - entry_collaborators (list): A list of formatted links representing officers.
            - entry_home (list): A list of formatted links representing parents.
    """

    entry_branches = set()
    entry_collaborators = set()
    entry_home = set()

    # Extract from Officers
    officers = data.get('Officers', [])
    for officer in officers:
        last_first_mi = convert_name_to_last_first_mi(officer['Name'])
        name_key, _ = entity_exists(last_first_mi)
        entry_collaborators.add(create_link(name_key if name_key else last_first_mi, officer['Name']))

    # Extract from Branch_relationship
    branches = data.get('Branch_relationship', [])
    for branch in branches:
        branch_name = f"{branch['Company']} ({branch.get('Jurisdiction', '')})"
        name_key, _ = entity_exists(branch_name)
        if branch.get('Type') == 'Branch':
            entry_branches.add(create_link(name_key if name_key else branch_name))
        elif branch.get('Type') == 'Parent':
            entry_home.add(create_link(name_key if name_key else branch_name))

    return list(entry_branches), list(entry_collaborators), list(entry_home)

# Function to create note content
def create_note_content(
    entity_type,
    data,
    root_url
):
    """
    Generate the content of a note based on the given entity type, data, and root URL.

    Args:
        entity_type (str): The type of the entity (e.g., 'company', 'person').
        data (dict): The data for the entity.
        root_url (str): The root URL of the entity.

    Returns:
        str: The content of the note, including front matter and sections.

    Raises:
        AssertionError: If the entity type is not 'company' or 'person'.

    Note:
        - The front matter includes the page title, URL/URI, date, and tags.
        - The attributes of the entity are dynamically added to the front matter.
        - The sections include general data, directors/officers, events, filings, assertions, branch relationships, and links.
        - The sections are filtered out if they are empty.
        - The source section includes a link to the root URL.
    """

    logger.info(f"{i()}CREATING NOTE ---- root_url: {root_url}")
    attributes = data.get('Attributes', {})
    events = data.get('Events', [])
    filings = data.get('Filings', [])
    assertions = data.get('Assertions', {})
    officers = data.get('Officers', [])
    branches = data.get('Branch_relationship', [])
    links = data.get('Links', [])

    entry_branches, entry_collaborators, entry_home = extract_additional_entries(data)

    frontmatter = {
        "page-title": f"Company Overview - {data['Company Name']}" if entity_type == 'company' else f"{data['Name']}",
        "url/uri": [root_url],
        "date": format_date(attributes.get("Incorporation Date", "")),
        "tags": ["Company-Details/General-Information"] if entity_type == 'company' else ["Person-Details"]
    }

    # Dynamically add all attributes to front matter
    for key, value in attributes.items():
        frontmatter_key = key.lower().replace(' ', '-')
        if frontmatter_key == 'parent' and isinstance(value, dict):
            parent_name = value.get('company_name', 'N/A')
            parent_url = value.get('url', 'N/A')

            # Find the parent relationship to extract jurisdiction and company_id
            parent_relationship = next((branch for branch in branches if branch['Type'] == 'Parent'), None)
            if parent_relationship:
                parent_jurisdiction = parent_relationship.get('Jurisdiction', 'N/A')
                parent_company_id = parent_relationship.get('Company ID', 'N/A')
                formatted_parent_name = f"[[{parent_name} ({parent_jurisdiction} - {parent_company_id})]]"
            else:
                formatted_parent_name = f"[[{parent_name}]]"

            frontmatter["parent-name"] = formatted_parent_name
            frontmatter["parent-url"] = parent_url
        elif 'address' in frontmatter_key:
            frontmatter[frontmatter_key] = f"[[{value}]]"
        else:
            frontmatter[frontmatter_key] = format_date(value) if "date" in frontmatter_key else value


    if entry_home:
        frontmatter["entry-home"] = entry_home
    if entry_branches:
        frontmatter["entry-branches"] = entry_branches
    if entry_collaborators:
        frontmatter["entry-collaborators"] = entry_collaborators

    frontmatter_str = "---\n"
    for key, value in frontmatter.items():
        if isinstance(value, list):
            value = "\n  - ".join(value)
            frontmatter_str += f"{key}:\n  - {value}\n"
        else:
            frontmatter_str += f"{key}: {value}\n"
    frontmatter_str += "---\n\n"

    note_content = frontmatter_str

    # Add sections to note content
    if attributes:
        note_content += "## General Information\n"
        note_content += format_general_data(attributes)
        note_content += "\n"

    if events:
        note_content += "## Events\n"
        note_content += format_events(events)
        note_content += "\n"

    if filings:
        note_content += "## Filings\n"
        note_content += format_filings(filings)
        note_content += "\n"

    if assertions:
        note_content += "## Assertions\n"
        note_content += format_assertions(assertions)
        note_content += "\n"

    if officers:
        note_content += "## Directors / Officers\n"
        note_content += format_table(officers, 'officer')
        note_content += "\n"

    if branches:
        note_content += "## Branch Relationships\n"
        note_content += format_branch_relationships(branches)
        note_content += "\n"

    if links:
        note_content += "## Links\n"
        note_content += format_links(links)
        note_content += "\n"

    note_content += f"## Source\n[Original URL]({root_url})\n"

    return note_content

def format_general_data(
    attributes
):
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
        if isinstance(value, dict) and 'company_name' in value and 'url' in value:
            company_name = value.get('company_name', '')
            company_url = value.get('url', '')
            value = f"[[{company_name}]] ([link]({company_url}))"
        elif isinstance(value, list):
            value = ', '.join(value)
        if "Address" in key:
            value = f"[[{value}]]"
        if "Agent Name" in key:
            name_link = convert_name_to_last_first_mi(value)
            name_key, _ = entity_exists(name_link)
            value = create_link(name_key if name_key else name_link, value, True)
        table += f"| {key:<18} | {value:<43} |\n"
    logger.info(f"{i()}CREATING NOTE ---- format_general_data finished")
    return table

def create_link(
    entity_key,
    display_name=None,
    tabled=False
):
    """
    Creates a Markdown link with the given `file_name` and optional `display_name`.

    Args:
        file_name (str): The name of the file to link to.
        display_name (Optional[str]): The name to display for the link. If not provided, the `file_name` will be used.
        tabled (bool, optional): Whether to use the `|` separator for the link with a delimiter between the `file_name` and `display_name` because the link is in a table. Defaults to False.

    Returns:
        str: The Markdown link with the `file_name` and `display_name`. If `display_name` is not provided or is the same as `file_name`, the link will only contain the `file_name`.

    Example:
        >>> create_link('example.md', 'Example File', True)
        '[[example.md\|Example File]]'

        >>> create_link('example.md', 'Example File')
        '[[example.md|Example File]]'

        >>> create_link('example.md')
        '[[example.md]]'
    """
    separator = "|"
    if tabled:
        separator = "\|"
    if display_name and display_name != entity_key:
        return f"[[{entity_key}{separator}{display_name}]]"
    else:
        return f"[[{entity_key}]]"

def format_table(
    entries,
    entry_type='officer'
):
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
        name_link = convert_name_to_last_first_mi(entry['Name'])
        name_key, _ = entity_exists(name_link)
        link = create_link(name_key if name_key else name_link, entry['Name'], True)
        table += f"| {link:<20} | {entry.get('Role', '-'):<15} | {entry.get('Status', '-'):<10} | {entry['Type']:<11} | [Link]({entry.get('Link', '#')}) |\n"
    logger.info(f"{i()}CREATING NOTE ---- format officer table finished")
    return table

# Define the functions
def extract_dates(
    text
):
    """
    Extracts all date strings from the given text.

    Args:
        text (str): The input text containing dates.

    Returns:
        list: A list of date strings found in the text.
    """
    date_pattern = r'\b(?:\d{4}[/-]\d{2}[/-]\d{2}|\d{2}[/-]\d{2}[/-]\d{4}|\d{2}[/-]\d{2}[/-]\d{2})\b'
    matches = re.findall(date_pattern, text)
    return matches

def format_events(
    events
) -> str:
    """
    Formats a list of events into a Markdown table for display in a note.

    Args:
        events (List[Dict[str, str]]): A list of dictionaries representing events. Each dictionary should have the following keys:
            - Description (str): The description of the event.
            - Link (str, optional): The link to the event (default is '#').

    Returns:
        str: A Markdown table representing the events. The table has the following format:
            ## Events for
            | Start Date | End Date | Event | Link |
            |------------|----------|-------|------|
            | start_date1 | end_date1 | event_description1 | [Link](event_link1) |
            | start_date2 | end_date2 | event_description2 | [Link](event_link2) |
            ...

    Example:
        >>> format_events([
        ...     {'Description': 'Between 2010-01-11 and 2018-09-19: Addition of officer [[HEITZ, KELLY N|KELLY NICHOLAS HEITZ]], agent', 'Link': 'https://opencorporates.com/events/346987079'},
        ...     {'Description': '2010-01-11: Incorporated', 'Link': 'https://opencorporates.com/events/346987091'}
        ... ])
        '## Events for\n| Start Date | End Date | Event | Link |\n|------------|----------|-------|------|\n| 2010-01-11 | 2018-09-19 | Addition of officer [[HEITZ, KELLY N|KELLY NICHOLAS HEITZ]], agent | [Link](https://opencorporates.com/events/346987079) |\n| 2010-01-11 |  | Incorporated | [Link](https://opencorporates.com/events/346987091) |\n'
    """

    logger.info(f"{i()}✍️📆CREATING NOTE ---- format event table started")
    if not events:
        logger.info(f"{i()}❌✍️📆CREATING NOTE ---- Empty Events")
        return ""
    # l = max(len(e['Description']) for e in events)
    event_list = f"\n| {'Start Date':<10} | {'End Date':<10} | {'Event':<55} | Link |\n|{'':-<12}|{'':-<12}|{'':-<55}|------|\n"

    for event in events:
        description = event.get('Description', '')
        link = event.get('Link', '#')
        Date = event.get('Date', '#')
        dates = extract_dates(Date)

        if len(dates) > 1:
            start_date, end_date = sorted(dates)[:2]
        elif len(dates) == 1:
            start_date, end_date = dates[0], ""
        else:
            start_date, end_date = "", ""

        event_list += f"| {start_date:<10} | {end_date:<10} | {description:<55} | [Link]({link}) |\n"

    logger.info(f"{i()}✅✍️📆CREATING NOTE ---- format event table finished")
    return event_list

def format_filings(
    filings
):
    """
    Generates a formatted table for filings including the date, description, and an optional link.

    This function takes a list of filing dictionaries as input and generates a formatted table with the following columns:
    - Date: The date of the filing.
    - Description: The description of the filing.

    If the input list is empty or None, an empty string is returned.

    Parameters:
    ----------
    filings (list): A list of dictionaries containing filing information. Each dictionary should have the following keys:
        - Date (str): The date of the filing.
        - Description (str): The description of the filing.
        - Link (str, optional): The link to the filing (default is '#').

    Returns:
    -------
    str: A formatted table representing the filings. The table has the following format:
        | Date | Description | Link |
        |------|-------------|------|
        | filing_date1 | filing_description1 | [Link](filing_link1) |
        | filing_date2 | filing_description2 | [Link](filing_link2) |
        ...

    Example:
        >>> filings = [
        ...     {'Date': '2022-01-01', 'Description': 'Annual Report', 'Link': 'https://example.com/filing1'},
        ...     {'Date': '2022-02-01', 'Description': 'Quarterly Report', 'Link': 'https://example.com/filing2'},
        ... ]
        >>> format_filings(filings)
        '| Date | Description | Link |\n|------|-------------|------|\n| 2022-01-01 | Annual Report | [Link](https://example.com/filing1) |\n| 2022-02-01 | Quarterly Report | [Link](https://example.com/filing2) |\n'
    """
    logger.info(f"{i()}✍️📑CREATING NOTE ---- format filings table started")
    if not filings:
        logger.info(f"{i()}❌✍️📑CREATING NOTE ---- Empty filings")
        return ""
    filing_list = f"| {'Date':<11} | {'Description':<30} | Link |\n|{'':-<13}|{'':-<32}|-------|\n"
    for filing in filings:
        filing_list += f"| {filing['Date']:<11} | {filing['Description']:<30} | [Link]({filing.get('Link', '#')}) |\n"
    logger.info(f"{i()}✅✍️📑CREATING NOTE ---- format filings table finished")
    return filing_list

def format_assertions(
    assertions
):
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
    if 'Company Addresses' in assertions:
        for address in assertions['Company Addresses']:
            normalized_address = '[[' + normalize_address(address['Description']) + ']]'
            assertion_list += f"| {address['Title']:<19} | {normalized_address:<55} |\n"
    if 'Telephone Numbers' in assertions:
        for phone in assertions['Telephone Numbers']:
            assertion_list += f"| {phone['Title']:<19} | {phone['Description']:<55} |\n"
    logger.info(f"{i()}✅✍️📑CREATING NOTE ---- format assertions table finished")
    return assertion_list

def format_branch_relationships(
    branches: List[Dict[str, str]]
) -> str:
    """
    Formats the given list of branch relationships into a table.

    Args:
        branches (list[dict]): A list of dictionaries representing branch relationships. Each dictionary should have the following keys:
            - 'Company' (str): The name of the company.
            - 'Company ID' (str): The ID of the company.
            - 'Jurisdiction' (str, optional): The jurisdiction of the branch. Defaults to 'N/A' if not provided.
            - 'Status' (str, optional): The status of the branch. Defaults to 'N/A' if not provided.
            - 'Type' (str, optional): The type of the branch. Defaults to 'N/A' if not provided.
            - 'Link' (str, optional): The link associated with the branch. Defaults to 'N/A' if not provided.
            - 'Start Date' (str, optional): The start date of the branch. Defaults to 'N/A' if not provided.
            - 'End Date' (str, optional): The end date of the branch. Defaults to 'N/A' if not provided.
            - 'statement_link' (str, optional): The link to the relationship statement. Defaults to 'N/A' if not provided.

    Returns:
        str: A string representing the formatted table with the branch relationships.

    Example:
        >>> branches = [
        ...     {'Company': 'Company A','Company ID': 'Company A ID', 'Jurisdiction': 'Jurisdiction 1', 'Status': 'Active', 'Type': 'Branch', 'Link': 'https://example.com/1', 'Start Date': '01 Jan 2000', 'End Date': '', 'statement_link': 'https://example.com/statement/1'},
        ...     {'Company': 'Company B','Company ID': 'Company B ID',  'Jurisdiction': 'Jurisdiction 2', 'Status': 'Inactive', 'Type': 'Branch', 'Link': 'https://example.com/2', 'Start Date': '01 Jan 2000', 'End Date': '01 Jan 2020', 'statement_link': 'https://example.com/statement/2'},
        ... ]
        >>> format_branch_relationships(branches)
        '| Company                         | Jurisdiction         | Jurisdiction         | Status   | Type       | Link                              | Start Date   | End Date     | Statement Link                     |\n|----------------------------------|----------------------|----------------------|----------|------------|-----------------------------------|--------------|--------------|-----------------------------------|\n| [[Company A]]                    | Company A ID         | Jurisdiction 1       | Active   | Branch     | [Link](https://example.com/1)     | 01 Jan 2000  | N/A          | [Statement](https://example.com/1) |\n| [[Company B]]                    | Company B ID         | Jurisdiction B       | Inactive | Branch     | [Link](https://example.com/2)     | 01 Jan 2000  | 01 Jan 2020  | [Statement](https://example.com/2) |\n'
    """

    logger.info(f"{i()}✍️👔CREATING NOTE ---- format branch table started")
    if not branches:
        logger.info(f"{i()}❌✍️👔CREATING NOTE ---- Empty branch")
        return ""

    header = f"| {'Company':<30}| {'Company ID':<20}  | {'Jurisdiction':<20} | {'Status':<8} | {'Type':<10} | {'Link':<35} | {'Start Date':<12} | {'End Date':<12} | {'Statement Link':<35} |\n"
    separator = f"|{'':-<32}|{'':-<22}|{'':-<22}|{'':-<10}|{'':-<12}|{'':-<37}|{'':-<14}|{'':-<14}|{'':-<37}|\n"

    branch_list = header + separator

    for branch in branches:
        company = branch.get('Company', 'N/A') or 'N/A'
        company_id = branch.get('Company ID', 'N/A') or 'N/A'
        jurisdiction = branch.get('Jurisdiction', 'N/A') or 'N/A'
        status = branch.get('Status', 'N/A') or 'N/A'
        branch_type = branch.get('Type', 'N/A') or 'N/A'
        link = branch.get('Link', 'N/A') or 'N/A'
        start_date = branch.get('Start Date', 'N/A') or 'N/A'
        end_date = branch.get('End Date', 'N/A') or 'N/A'
        statement_link = branch.get('statement_link', 'N/A') or 'N/A'

        link_formatted = f"[Link]({link})" if link != 'N/A' else 'N/A'
        statement_link_formatted = f"[Statement]({statement_link})" if statement_link != 'N/A' else 'N/A'

        branch_list += "| {company:<30} | {company_id:<20} | {jurisdiction:<20} | {status:<8} | {branch_type:<10} | {link_formatted:<35} | {start_date:<12} | {end_date:<12} | {statement_link_formatted:<35} |\n".format(
            company=f"[[{company}]]", company_id=company_id, jurisdiction=jurisdiction, status=status, branch_type=branch_type, link_formatted=link_formatted, start_date=start_date, end_date=end_date, statement_link_formatted=statement_link_formatted)


    logger.info(f"{i()}✅✍️👔CREATING NOTE ---- format branch table finished")
    return branch_list

def format_links(
    links
):
    """
    Formats a list of links into a Markdown table for display in a note.

    Args:
        links (List[str]): A list of links to be formatted.

    Returns:
        str: A Markdown table representing the links.

    Example:
        >>> format_links(["https://example.com", "https://github.com"])
        '| Link | URL |\n|------|------|\n| [Link](https://example.com) | Link |\n| [Link](https://github.com) | Link |\n'

    Note:
        This function logs the start and end of the link table formatting process using the `logger` module.
    """

    logger.info(f"{i()}✍️🔗CREATING NOTE ---- format link table started")
    if not links:
        logger.info(f"{i()}❌✍️🔗CREATING NOTE ---- Empty link")
        return ""
    link_list = f"| Link   | {'url':<30} \n|{'':-<8}|{'':-<32}|\n"
    for link in links:
        link_list += f"| [Link]({link}) |{link:<30}|\n"
    logger.info(f"{i()}✅✍️🔗CREATING NOTE ---- format link table finished")
    return link_list

def add_aka(
    note_content,
    new_aka
):
    """
    Adds a new alias (aka) to the note content if the 'aka:' section exists, otherwise creates a new 'aka:' section.

    This function checks if the 'aka:' section exists in the `note_content` string. If it does, it extracts the existing aliases from the section and adds the `new_aka` to the set of aliases. If the 'aka:' section does not exist, it appends a new 'aka:' section to the `note_content` string with the `new_aka` as the only alias.

    Parameters:
    ----------
    note_content (str): The content of the note.
    new_aka (str): The new alias to be added.

    Returns:
    -------
    str: The updated note content with the new alias added.

    Example:
        >>> note_content = "This is a note.\naka:\n- Alias1\n- Alias2"
        >>> new_aka = "Alias3"
        >>> add_aka(note_content, new_aka)
        "This is a note.\naka:\n- Alias1\n- Alias2\n- Alias3"

        >>> note_content = "This is a note."
        >>> new_aka = "Alias3"
        >>> add_aka(note_content, new_aka)
        "This is a note.\naka:\n- Alias3"

    Note:
        The function uses regular expressions to search for the 'aka:' section in the `note_content` string. It assumes that the 'aka:' section follows the format "aka:\n- Alias1\n- Alias2\n...". If the format is different, the function may not work as expected.
    """
    logger.info(f"{i()}ADDING aka ---- {new_aka}")
    if 'aka:' in note_content:
        akas_section = re.search(r'(?<=aka:\s*\n)((\s*-\s*.*\n)+)', note_content, re.IGNORECASE)
        if akas_section:
            akas = set(akas_section.group(1).strip().split('\n'))
            akas.add(f"- {new_aka}")
            new_akas_section = "\n".join(akas) + "\n"
            note_content = note_content.replace(akas_section.group(0), new_akas_section)
    else:
        note_content += f'aka:\n- {new_aka}\n'
    logger.info(f"{i()}ADDING aka COMPLETED ---- {new_aka}")
    return note_content

def add_url(note_content, new_url):
    """
    Adds a new URL to the given note content.

    This function checks if the 'url/uri:' section exists in the `note_content` string. If it does, it searches for the 'url/uri:' section using regular expressions. If the section is found, it extracts the existing URLs, adds the new URL to the set, and replaces the old URLs section with the updated set. If the 'url/uri:' section does not exist, it appends the new URL to the end of the `note_content` string.

    Args:
        note_content (str): The content of the note.
        new_url (str): The URL to be added.

    Returns:
        str: The updated note content with the new URL added.

    Example:
        >>> note_content = "This is a note.\nurl/uri:\n- https://example.com\n- https://example.org"
        >>> new_url = "https://example.net"
        >>> add_url(note_content, new_url)
        "This is a note.\nurl/uri:\n- https://example.com\n- https://example.org\n- https://example.net"

        >>> note_content = "This is a note."
        >>> new_url = "https://example.net"
        >>> add_url(note_content, new_url)
        "This is a note.\nurl/uri:\n- https://example.net"
    """
    logger.info(f"{i()}ADDING URL/URI ---- {new_url}")
    if 'url/uri:' in note_content:
        urls_section = re.search(r'url/uri:\s*\n((?:\s*-\s*.*\n)+)', note_content, re.IGNORECASE)
        # urls_section = re.search(r'(?<=url/uri:\s*\n)((\s*-\s*.*\n)+)', note_content, re.IGNORECASE)
        if urls_section:
            urls = set(urls_section.group(1).strip().split('\n'))
            urls.add(f"- {new_url}")
            new_urls_section = "\n".join(urls) + "\n"
            note_content = note_content.replace(urls_section.group(0), new_urls_section)
    else:
        note_content += f'url/uri:\n- {new_url}\n'
    logger.info(f"{i()}ADDING URL/URI COMPLETED ---- {new_url}")
    return note_content

def note_the_data(
    data,
    root_url
):
    """
    Creates a note based on the given data and root URL.

    This function determines the entity type and name based on the data. It then creates the note content using the `create_note_content` function. The function gets the correct output and staging directory based on the entity type. It ensures that the staging directory exists and creates a folder for the entity inside the staging directory. The function determines the path to the note file inside the entity folder. If the note file does not exist, it writes the note content to the file and updates the cache with the new note. If the note file already exists, it logs a message indicating that the note already exists.

    Args:
        data (dict): A dictionary containing the data used to create the note.
        root_url (str): The root URL of the data.

    Returns:
        None: If the entity type cannot be determined.

    Example:
        >>> data = {
        ...     'Company Name': 'Acme Inc.',
        ...     'Address': '123 Main St',
        ...     'Phone Number': '555-1234',
        ...     'Website': 'https://www.acmeinc.com'
        ... }
        >>> root_url = 'https://example.com'
        >>> note_the_data(data, root_url)
        CREATING NOTE ---- note_the_data started
        CREATING NOTE ---- note_the_data finished Note created for Acme Inc. at E:/_GIT/obsidian/BoA timeline/profiles/other/staging/Acme Inc./Acme Inc..md
        Note created for Acme Inc. at E:/_GIT/obsidian/BoA timeline/profiles/other/staging/Acme Inc./Acme Inc..md

    """
    section("Creating Note")
    logger.info(f"{i()}✍️📑CREATING NOTE ---- note_the_data started")

    # Determine the entity type and name
    if 'Company Name' in data:
        logger.warning(f"{i()}✍️📑CREATING NOTE ---- found 'Company Name' in data")
        entity_name = data['Company Name']
        entity_type = 'company'
    elif 'Name' in data:
        logger.warning(f"{i()}✍️📑CREATING NOTE ---- found 'Name' in data") # todo: this doesn't even make sense
        entity_name = data['Name']
        entity_type = 'person'
    elif 'Address' in data:
        logger.warning(f"{i()}✍️📑CREATING NOTE ---- found 'Address' in data") # todo: this doesn't even make sense as it's a part of the data of the company
        entity_name = data['Address']
        entity_type = 'address'
    else:
        logger.warning(f"{i()}❌❌❌❌CREATING NOTE ---- Entity type cannot be determined for the given data.")
        entity_name = 'Unknown Entity'
        entity_type = 'unknown'

    note_content = create_note_content(entity_type, data, root_url)
    logger.debug(f"{i()}✍️📑CREATING NOTE ---- Note content created for {entity_name}.")

    # Get the correct output and staging directory based on the entity type
    staging_directory = staging_directories.get(entity_type, "E:/_GIT/obsidian/BoA timeline/profiles/other/staging/")
    logger.debug(f"{i()}✍️📑CREATING NOTE ---- Staging directory set to {staging_directory}.")

    # Ensure the staging directory exists
    os.makedirs(staging_directory, exist_ok=True)
    logger.debug(f"{i()}✍️📑CREATING NOTE ---- Ensured staging directory exists at {staging_directory}.")

    # Create a folder for the entity inside the staging directory
    entity_folder = os.path.join(staging_directory, entity_name)
    os.makedirs(entity_folder, exist_ok=True)
    logger.debug(f"{i()}✍️📑CREATING NOTE ---- Entity folder created at {entity_folder}.")

    # Path to the note file inside the entity folder
    note_path = os.path.join(entity_folder, f"{entity_name}.md")

    if os.path.exists(note_path):
        # Update existing note
        with open(note_path, 'r', encoding='utf-8', errors='ignore') as note_file:
            existing_note_content = note_file.read()

        # Add AKAs and URLs
        updated_note_content = add_aka(existing_note_content, entity_name)
        updated_note_content = add_url(updated_note_content, root_url)

        # Save the updated note
        with open(note_path, 'w', encoding='utf-8') as note_file:
            note_file.write(updated_note_content)
        logger.info(f"{i()}✍️📑CREATING NOTE ---- Note updated for {entity_name} at {note_path}")
        print(f"{i()}✍️📑CREATING NOTE ---- Note updated for {entity_name} at {note_path}")
    else:
        # Create new note
        with open(note_path, 'w', encoding='utf-8') as note_file:
            note_file.write(note_content)
        logger.info(f"{i()}✍️📑CREATING NOTE ---- Note created for {entity_name} at {note_path}")
        print(f"{i()}✍️📑CREATING NOTE ---- Note created for {entity_name} at {note_path}")

    # Update cache with the new note
    update_cache(entity_name, note_path)
    logger.debug(f"{i()}✍️📑CREATING NOTE ---- Cache updated with note for {entity_name}.")

    logger.info(f"{i()}✅✍️📑CREATING NOTE ---- note_the_data finished")

def update_cache(
    name,
    note_path
):
    """
    Updates the cache with the given name and note path.

    Args:
        name (str): The name of the entity.
        note_path (str): The path to the note file.

    Returns:
        None

    This function reads the content of the note file specified by `note_path`, extracts the aliases using the `extract_aliases` function, and updates the `existing_notes_cache` dictionary with the entity name, note path, and aliases. It then writes the updated cache to the file specified by `cache_file_path` in JSON format with an indentation of 2.

    Note:
        - The `existing_notes_cache` dictionary is assumed to be defined and initialized before calling this function.
        - The `cache_file_path` is assumed to be defined and initialized before calling this function.
        - The `extract_aliases` function is assumed to be defined and imported before calling this function.

    Example usage:
    ```
    update_cache("John Doe", "path/to/johndoe.md")
    ```
    """

    logger.info(f"{i()}✍️📑CREATING NOTE ---- building cache")
    with open(note_path, 'r', encoding='utf-8') as note_file:
        note_content = note_file.read()
    aliases = extract_aliases(note_content)
    existing_notes_cache[name.upper()] = {
        'path': note_path,
        'aliases': aliases
    }
    with open(cache_file_path, 'w', encoding='utf-8') as cache_file:
        json.dump(existing_notes_cache, cache_file, indent=2)
    logger.info(f"{i()}✅✍️📑CREATING NOTE ---- finished building cache")

def create_address_structure(
    address,
    staging_directory
):
    """
    Creates a folder structure for a given address within a staging directory.

    This function takes an address and a staging directory as input and creates a folder structure for the address within the staging directory. If the folder does not exist, it is created along with a note file named after the address.

    Parameters:
    -----------
    address: str
        The address for which to create the folder structure.
    staging_directory: str
        The directory in which to create the folder structure.

    Returns:
    --------
    None

    Example usage:
    ```
    create_address_structure("123 Main St", "/path/to/staging_directory")
    ```

    This will create a folder named "123 Main St" within the "/path/to/staging_directory" directory, if it does not already exist. It will also create a note file named "123 Main St.md" within the folder.
    """
    logger.info(f"{i()}✍️📑CREATING NOTE ---- create_address_structure started")
    address_folder = os.path.join(staging_directory, address)
    if not os.path.exists(address_folder):
        os.makedirs(address_folder)
        folder_note_path = os.path.join(address_folder, f"{address}.md")
        with open(folder_note_path, 'w', encoding='utf-8') as folder_note:
            folder_note.write(f"# {address}\n")
    logger.info(f"{i()}✅✍️📑CREATING NOTE ---- create_address_structure finished")


