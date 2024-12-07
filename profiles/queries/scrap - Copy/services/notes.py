import os

# import json
import re
from datetime import datetime

from loguru import logger

from services.applogging import *

# from fuzzywuzzy import process, fuzz
from services.notes import *
from settings.settings import *
from utils.useollama import *
from utils.utils import *
from utils.ziptest import *

# from urllib.parse import urljoin


# import gs

# Define the output directories for different types of entities
output_directories = {
    "person": "E:/_GIT/obsidian/BoA timeline/profiles/people/",
    "company": "E:/_GIT/obsidian/BoA timeline/profiles/corporations/",
    "address": "E:/_GIT/obsidian/BoA timeline/profiles/addresses/",
}

staging_directories = {
    "person": "E:/_GIT/obsidian/BoA timeline/profiles/people/staging/",
    "company": "E:/_GIT/obsidian/BoA timeline/profiles/corporations/staging/",
    "address": "E:/_GIT/obsidian/BoA timeline/profiles/addresses/staging/",
}

existing_notes_path = "file-folder-struc.txt"
cache_file_path = "cache.json"

# Initializer step to ensure staging folders exist


def extract_aliases(note_content):
    """
    Extracts aliases from the note content.

    This function searches for lines in the note content that start with "aka:" and extracts the aliases listed below it.

    Args:
        note_content (str): The content of the note.

    Returns:
        list: A list of aliases found in the note content, converted to uppercase.
    """
    aliases = []
    match = re.search(r"aka:\s*\n((\s*-\s*.*\n)+)", note_content, re.IGNORECASE)
    if match:
        alias_lines = match.group(1).strip().split("\n")
        aliases = [alias_line.strip()[1:].strip() for alias_line in alias_lines]
    return [alias.upper() for alias in aliases]


# def find_closest_match(
#     name,
#     cache
# ):
#     """
#     Find the closest match for a name in the cache.

#     Args:
#         name (str): The name to find a match for.
#         cache (dict): The cache of existing notes and their aliases.

#     Returns:
#         tuple: A tuple containing the closest match for the name and its score. Returns None if no match is found.
#     """
#     name = name.upper()
#     all_names = list(cache.keys()) + [alias for data in cache.values() for alias in data['aliases']]
#     match = process.extractOne(name, all_names, scorer=fuzz.token_sort_ratio)
#     return match


def format_date(date_str):
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
        date_obj = datetime.strptime(date_part, "%d %B %Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        return date_str


def create_note_content(entity_type, data, root_url):
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
    attributes = data.get("Attributes", {})
    events = data.get("Events", [])
    filings = data.get("Filings", [])
    assertions = data.get("Assertions", {})
    officers = data.get("Officers", [])
    branches = data.get("Branch_relationship", [])
    links = data.get("Links", [])

    entry_branches, entry_collaborators, entry_home = None, None, None

    frontmatter = {
        "page-title": (
            f"Company Overview - {data['Company Name']}"
            if entity_type == "company"
            else f"{data['Name']}"
        ),
        "url/uri": [root_url],
        "date": format_date(attributes.get("Incorporation Date", "")),
        "tags": (
            ["Company-Details/General-Information"]
            if entity_type == "company"
            else ["Person-Details"]
        ),
    }

    # Dynamically add all attributes to front matter
    for key, value in attributes.items():
        frontmatter_key = key.lower().replace(" ", "-")
        if frontmatter_key == "parent" and isinstance(value, dict):
            parent_name = value.get("company_name", "N/A")
            parent_url = value.get("url", "N/A")

            # Find the parent relationship to extract jurisdiction and company_id
            parent_relationship = next(
                (branch for branch in branches if branch["Type"] == "Parent"), None
            )
            if parent_relationship:
                parent_jurisdiction = parent_relationship.get("Jurisdiction", "N/A")
                parent_company_id = parent_relationship.get("Company ID", "N/A")
                formatted_parent_name = (
                    f"[[{parent_name} ({parent_jurisdiction} - {parent_company_id})]]"
                )
            else:
                formatted_parent_name = f"[[{parent_name}]]"

            frontmatter["parent-name"] = formatted_parent_name
            frontmatter["parent-url"] = parent_url
        elif "address" in frontmatter_key:
            frontmatter[frontmatter_key] = f"[[{value}]]"
        else:
            frontmatter[frontmatter_key] = (
                format_date(value) if "date" in frontmatter_key else value
            )

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
        note_content += render_attributes(attributes)
        note_content += "\n"

    if events:
        note_content += "## Events\n"
        note_content += render_events(events)
        note_content += "\n"

    if filings:
        note_content += "## Filings\n"
        note_content += render_filings(filings)
        note_content += "\n"

    if assertions:
        note_content += "## Assertions\n"
        note_content += render_assertions(assertions)
        note_content += "\n"

    if officers:
        note_content += "## Directors / Officers\n"
        note_content += render_officers(officers)
        note_content += "\n"

    if branches:
        note_content += "## Branch Relationships\n"
        note_content += render_relationships(branches)
        note_content += "\n"

    if links:
        note_content += "## Links\n"
        note_content += render_links(links)
        note_content += "\n"

    note_content += f"## Source\n[Original URL]({root_url})\n"

    return note_content


# Define the functions
def extract_dates(text):
    """
    Extracts all date strings from the given text.

    Args:
        text (str): The input text containing dates.

    Returns:
        list: A list of date strings found in the text.
    """
    date_pattern = r"\b(?:\d{4}[/-]\d{2}[/-]\d{2}|\d{2}[/-]\d{2}[/-]\d{4}|\d{2}[/-]\d{2}[/-]\d{2})\b"
    matches = re.findall(date_pattern, text)
    return matches


def add_aka(note_content, new_aka):
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



    Note:
        The function uses regular expressions to search for the 'aka:' section in the `note_content` string. It assumes that the 'aka:' section follows the format "aka:\n- Alias1\n- Alias2\n...". If the format is different, the function may not work as expected.
    """
    logger.info(f"{i()}ADDING aka ---- {new_aka}")
    if "aka:" in note_content:
        akas_section = re.search(
            r"(?<=aka:\s*\n)((\s*-\s*.*\n)+)", note_content, re.IGNORECASE
        )
        if akas_section:
            akas = set(akas_section.group(1).strip().split("\n"))
            akas.add(f"- {new_aka}")
            new_akas_section = "\n".join(akas) + "\n"
            note_content = note_content.replace(akas_section.group(0), new_akas_section)
    else:
        note_content += f"aka:\n- {new_aka}\n"
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
    if "url/uri:" in note_content:
        urls_section = re.search(
            r"url/uri:\s*\n((?:\s*-\s*.*\n)+)", note_content, re.IGNORECASE
        )
        # urls_section = re.search(r'(?<=url/uri:\s*\n)((\s*-\s*.*\n)+)', note_content, re.IGNORECASE)
        if urls_section:
            urls = set(urls_section.group(1).strip().split("\n"))
            urls.add(f"- {new_url}")
            new_urls_section = "\n".join(urls) + "\n"
            note_content = note_content.replace(urls_section.group(0), new_urls_section)
    else:
        note_content += f"url/uri:\n- {new_url}\n"
    logger.info(f"{i()}ADDING URL/URI COMPLETED ---- {new_url}")
    return note_content


def note_the_data(data, root_url):
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
    if "Company Name" in data:
        logger.warning(f"{i()}✍️📑CREATING NOTE ---- found 'Company Name' in data")
        entity_name = data["Company Name"]
        entity_type = "company"
    elif "Name" in data:
        logger.warning(
            f"{i()}✍️📑CREATING NOTE ---- found 'Name' in data"
        )  # todo: this doesn't even make sense
        entity_name = data["Name"]
        entity_type = "person"
    elif "Address" in data:
        logger.warning(
            f"{i()}✍️📑CREATING NOTE ---- found 'Address' in data"
        )  # todo: this doesn't even make sense as it's a part of the data of the company
        entity_name = data["Address"]
        entity_type = "address"
    else:
        logger.warning(
            f"{i()}❌❌❌❌CREATING NOTE ---- Entity type cannot be determined for the given data."
        )
        entity_name = "Unknown Entity"
        entity_type = "unknown"

    note_content = create_note_content(entity_type, data, root_url)
    logger.debug(f"{i()}✍️📑CREATING NOTE ---- Note content created for {entity_name}.")

    # Get the correct output and staging directory based on the entity type
    staging_directory = staging_directories.get(
        entity_type, "E:/_GIT/obsidian/BoA timeline/profiles/other/staging/"
    )
    logger.debug(
        f"{i()}✍️📑CREATING NOTE ---- Staging directory set to {staging_directory}."
    )

    # Ensure the staging directory exists
    os.makedirs(staging_directory, exist_ok=True)
    logger.debug(
        f"{i()}✍️📑CREATING NOTE ---- Ensured staging directory exists at {staging_directory}."
    )

    # Create a folder for the entity inside the staging directory
    entity_folder = os.path.join(staging_directory, entity_name)
    os.makedirs(entity_folder, exist_ok=True)
    logger.debug(
        f"{i()}✍️📑CREATING NOTE ---- Entity folder created at {entity_folder}."
    )

    # Path to the note file inside the entity folder
    note_path = os.path.join(entity_folder, f"{entity_name}.md")

    if os.path.exists(note_path):
        # Update existing note
        with open(note_path, "r", encoding="utf-8", errors="ignore") as note_file:
            existing_note_content = note_file.read()

        # Add AKAs and URLs
        updated_note_content = add_aka(existing_note_content, entity_name)
        updated_note_content = add_url(updated_note_content, root_url)

        # Save the updated note
        with open(note_path, "w", encoding="utf-8") as note_file:
            note_file.write(updated_note_content)
        logger.info(
            f"{i()}✍️📑CREATING NOTE ---- Note updated for {entity_name} at {note_path}"
        )
        print(
            f"{i()}✍️📑CREATING NOTE ---- Note updated for {entity_name} at {note_path}"
        )
    else:
        # Create new note
        with open(note_path, "w", encoding="utf-8") as note_file:
            note_file.write(note_content)
        logger.info(
            f"{i()}✍️📑CREATING NOTE ---- Note created for {entity_name} at {note_path}"
        )
        print(
            f"{i()}✍️📑CREATING NOTE ---- Note created for {entity_name} at {note_path}"
        )

    # Update cache with the new note

    logger.debug(
        f"{i()}✍️📑CREATING NOTE ---- Cache updated with note for {entity_name}."
    )

    logger.info(f"{i()}✅✍️📑CREATING NOTE ---- note_the_data finished")


# def create_address_structure(
#     address,
#     staging_directory
# ):
#     """
#     Creates a folder structure for a given address within a staging directory.

#     This function takes an address and a staging directory as input and creates a folder structure for the address within the staging directory. If the folder does not exist, it is created along with a note file named after the address.

#     Parameters:
#     -----------
#     address: str
#         The address for which to create the folder structure.
#     staging_directory: str
#         The directory in which to create the folder structure.

#     Returns:
#     --------
#     None

#     Example usage:
#     ```
#     create_address_structure("123 Main St", "/path/to/staging_directory")
#     ```

#     This will create a folder named "123 Main St" within the "/path/to/staging_directory" directory, if it does not already exist. It will also create a note file named "123 Main St.md" within the folder.
#     """
#     logger.info(f"{i()}✍️📑CREATING NOTE ---- create_address_structure started")
#     address_folder = os.path.join(staging_directory, address)
#     if not os.path.exists(address_folder):
#         os.makedirs(address_folder)
#         folder_note_path = os.path.join(address_folder, f"{address}.md")
#         with open(folder_note_path, 'w', encoding='utf-8') as folder_note:
#             folder_note.write(f"# {address}\n")
#     logger.info(f"{i()}✅✍️📑CREATING NOTE ---- create_address_structure finished")
