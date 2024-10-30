import json
import traceback
import re
from typing import Tuple#, List, Dict, Union, Any
import ollama
from loguru import logger
from fuzzywuzzy import fuzz
# from rich.console import Console
# from rich import print as rprint
import usaddress
import probablepeople as pp
# from utils import
from services.applogging import *

# Global flags
display_debug = False
echo_output_terminal = False
use_llm = False  # Flag for using LLM

MODEL = 'mistral'
# logger.debug(f"🃏🧬🩻MODEL:{MODEL}")

# Load the address normalization data
with open('odd&ends/address-normalization-data.json',encoding='utf-8') as f:
    normalization_data = json.load(f)

# Helper functions
def get_directionals():
    """
    Retrieves the directionals from the normalization data.

    Returns:
        dict: A dictionary containing the directionals. If the 'directionals' key is not found in the normalization data, an empty dictionary is returned.
    """
    return normalization_data.get('directionals', {})

def get_address_parts():
    """
    Retrieves the address parts from the normalization data.

    Returns:
        dict: A dictionary containing the address parts. If the 'address_parts' key is not found in the normalization data, an empty dictionary is returned.
    """

    return normalization_data.get('address_parts', {})

def get_city_zip_data():
    """
    Retrieves the list of US state cities from the normalization data.

    Returns:
        list: A list of dictionaries containing the US state cities. If the 'us_state_cities' key is not found in the normalization data, an empty list is returned.
    """

    return normalization_data.get('us_state_cities', [])

def validate_city_zip(
    city: str,
   state: str,
   zip_code: str
) -> bool:
    """
    Validates the city, state, and zip code combination.

    Args:
        city (str): The name of the city.
        state (str): The state abbreviation.
        zip_code (str): The ZIP code, optionally with a hyphen and four-digit extension.

    Returns:
        bool: True if the city, state, and zip code combination is valid, False otherwise.

    This function retrieves the list of US state cities from the normalization data and searches for a match
    based on the provided city, state, and zip code. It uses the fuzzywuzzy library to compare the city names
    with high similarity threshold (90) to ensure a valid match. If a valid match is found, the function returns True.
    If no match is found, the function logs an error and returns False.
    """
    zip_code = zip_code.split('-')[0]  # Use the base ZIP code for matching
    zip_code = zip_code.zfill(5).replace(',', '').strip()  # Ensure the ZIP code is 5 digits
    city = city.replace(',', '').strip()  # Remove trailing commas and extra spaces
    state = state.replace(',', '').strip()  # Remove trailing commas and extra spaces
    city_zip_data = get_city_zip_data()
    for record in city_zip_data:
        if record['state'].upper() == state.upper() and str(record['zip_code']).zfill(5) == zip_code:
            if fuzz.ratio(record['city'].upper(), city.upper()) > 90:
                logger.debug(f"{i()}✅🏢🟰🏢Validated city: `{city}`, state: `{state}`, zip: `{zip_code}` against record: {record}")
                return True
    logger.error(f"{i()}‼️🚨🏢🙅‍♂️🏣🚨‼️🤔 City name validation failed for: `{city}`, state: `{state}`, zip: `{zip_code}`")
    return False

def similarity(
    a: str,
   b: str
) -> bool:
    """
    Checks if two strings are similar to each other.

    Uses fuzzywuzzy's fuzz.ratio function to compare the similarity of two strings.
    Returns True if the similarity is greater than 90, False otherwise.

    Args:
        a (str): The first string to compare.
        b (str): The second string to compare.

    Returns:
        bool: True if the similarity is greater than 90, False otherwise.
    """
    return fuzz.ratio(a, b) > 90

def load_file_content(
    file_path: str
) -> str:
    """
    Loads the content of a file.

    Args:
        file_path (str): The path to the file to load.

    Returns:
        str: The content of the file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Load templates and examples
PROMPT_TEMPLATE = load_file_content('prompts/PROMPT_TEMPLATE.txt')
VALIDATION_PROMPT_TEMPLATE = load_file_content('prompts/VALIDATION_PROMPT_TEMPLATE.txt')
CORRECTNESS_PROMPT_TEMPLATE = load_file_content('prompts/CORRECTNESS_PROMPT_TEMPLATE.txt')
EXAMPLES1 = load_file_content('prompts/EXAMPLES1.txt')
EXAMPLES2 = load_file_content('prompts/EXAMPLES2.txt')
EXAMPLES3 = load_file_content('prompts/EXAMPLES3.txt')

def enforce_english_symbols(
    text: str
) -> str:
    """
    Removes non-English symbols from a string.

    This function uses regular expressions to remove any characters outside the range
    of ASCII characters (0x00 to 0x7F) from a given text string.

    Args:
        text (str): The text string from which to remove non-English symbols.

    Returns:
        str: The text string with non-English symbols removed.
    """
    return re.sub(r'[^\x00-\x7F]+', '', text)

def apply_directionals_and_parts(
    parsed_address: dict
) -> dict:
    """
    Applies directionals and address parts to a parsed address.

    This function applies directionals and address parts to a parsed address dictionary.
    It iterates over specific labels in the parsed address and applies cleaning, joining,
    and directional transformations to them. It also applies address parts to specific keys
    in the parsed address.

    Args:
        parsed_address (dict): The parsed address dictionary.

    Returns:
        dict: The parsed address dictionary with directionals and address parts applied.
    """
    directionals = get_directionals()
    address_parts = get_address_parts()
    # Clean and join parts for specific labels
    for label in ['Recipient', 'PlaceName', 'StreetName']:
        if label in parsed_address:
            logger.debug(f"{i()}⁉️❓❓Address parts: {label}")
            parsed_address[label] = clean_and_join_parts(parsed_address, label)
            logger.debug(f"{i()}🌍📫〽️✍️ Cleaned and joined parts for label `{label}`: {parsed_address[label]}")

    for key in ['StreetNamePreDirectional', 'StreetNamePostDirectional']:
        if key in parsed_address and parsed_address[key].upper() in directionals:
            logger.debug(f"{i()}⁉️❓❓Directional: {directionals[parsed_address[key].upper()]}")
            parsed_address[key] = directionals[parsed_address[key].upper()]
            logger.debug(f"{i()}🌍📫〽️✍️ Applied directional for `{key}`: {parsed_address[key]}")

    for key in ['StreetNamePreType', 'StreetNamePostType', 'StreetNamePreModifier', 'StreetNamePostModifier', 'OccupancyType']:
        if key in parsed_address and parsed_address[key].upper() in address_parts:
            logger.debug(f"{i()}⁉️❓❓Address parts: {address_parts[parsed_address[key].upper()]}")
            parsed_address[key] = address_parts[parsed_address[key].upper()]
            logger.debug(f"{i()}🌍📫〽️✍️ Applied address part for `{key}`: {parsed_address[key]}")

    return parsed_address

def clean_and_join_parts(
    parsed_address: dict,
   label: str
) -> str:
    """
    Cleans and joins parts of a parsed address.

    This function takes a parsed address dictionary and a label as inputs. It
    cleans and joins the parts corresponding to the label. If there are multiple
    parts, they are joined into a single string with spaces between them. If there
    is only one part, it is returned as is. If there are no parts, an empty string is
    returned.

    Args:
        parsed_address (dict): The parsed address dictionary.
        label (str): The label corresponding to the parts to be cleaned and joined.

    Returns:
        str: The cleaned and joined parts of the parsed address.
    """
    logger.debug(f"{i()}🌍📫〽️✍️ about to clean and or join parts for {label}")
    parts = [value.replace(',', '').strip() for key, value in parsed_address.items() if key == label]
    logger.debug(f"{i()}🌍📫〽️✍️ parts ready to be cleaned and or joinned: {parts}")
    if len(parts) > 1:
        joined_value = ' '.join(parts)
        logger.debug(f"{i()}🌍📫〽️✍️ Joined multiple parts for `{label}`: {joined_value}")
        return joined_value
    elif len(parts) == 1:
        logger.debug(f"{i()}🌍📫〽️✍️ Single part for `{label}`: {parts[0]}")
        return parts[0]
    return ''

def extract_zip_from_address_component(
    parsed_address: dict,
   component: str
) -> dict:
    """
    Extracts a zip code from the given address component and updates the parsed address.

    Args:
        parsed_address (dict): The parsed address dictionary.
        component (str): The component from which to extract the zip code.

    Returns:
        dict: The updated parsed address dictionary.
    """
    component_value = parsed_address.get(component, '')
    zip_match = re.search(r'\b\d{5}(?:-\d{4})?\b', component_value)
    if zip_match:
        logger.debug(f"{i()}🌍📫〽️✍️ found a zipcode in `{component_value}`")
        zip_code = zip_match.group()
        component_value = component_value.replace(zip_code, '').replace(',', '').strip()
        parsed_address[component] = component_value
        parsed_address['ZipCode'] = zip_code
        logger.debug(f"{i()}🌍📫〽️✍️ Extracted zip code `{zip_code}` from `{component}`")
    return parsed_address

def construct_reformatted_address(
    parsed_address
) -> str:
    """
    Constructs a reformatted address from a parsed address dictionary.

    This function constructs a reformatted address from a parsed address dictionary.
    It takes a parsed address dictionary as input and constructs a full address string
    by joining the appropriate parts together. The resulting address is then cleaned up
    by removing extraneous spaces and commas.

    Args:
        parsed_address (dict): The parsed address dictionary.

    Returns:
        str: The reformatted address string.
    """
    # Construct each part according to the template

    street_address = " ".join([
        parsed_address.get('AddressNumberPrefix', ''),
        parsed_address.get('AddressNumber', ''),
        parsed_address.get('AddressNumberSuffix', ''),
        parsed_address.get('StreetNamePreDirectional', ''),
        parsed_address.get('StreetNamePreModifier', ''),
        parsed_address.get('StreetNamePreType', ''),
        parsed_address.get('StreetName', ''),
        parsed_address.get('StreetNamePostDirectional', ''),
        parsed_address.get('StreetNamePostModifier', ''),
        parsed_address.get('StreetNamePostType', '')
    ]).strip()

    occupancy = " ".join([
        parsed_address.get('OccupancyType', ''),
        parsed_address.get('OccupancyIdentifier', '')
    ]).strip()

    box = " ".join([
        parsed_address.get('USPSBoxType', ''),
        parsed_address.get('USPSBoxID', ''),
        parsed_address.get('USPSBoxGroupType', ''),
        parsed_address.get('USPSBoxGroupID', '')
    ]).strip()

    city = parsed_address.get('PlaceName', '').strip()
    state = parsed_address.get('StateName', '').strip()
    zip_code = parsed_address.get('ZipCode', '').strip()
    recipient = parsed_address.get('Recipient', '').strip()

    # Construct the full address
    full_address = f"{box}, {street_address}, {occupancy}, {city}, {state}, {zip_code}".strip(", ").upper()
    
    # Clean up extraneous spaces and commas
    full_address = re.sub(r'\s{2,}', ' ', full_address)  # Replace multiple spaces with a single space
    full_address = re.sub(r',\s*,', ',', full_address).replace(' ,', ',')
    
    if recipient:
        full_address = f"{full_address}\n{recipient.upper()}"

    logger.debug(f"{i()}🌍📫〽️✍️ Constructed reformatted address: `{full_address}`")
    return full_address

def correct_city(
    city: str
) -> str:
    """
    Corrects the city name by removing any invalid characters and trimming any leading/trailing whitespace.

    Args:
        city (str): The city name to be corrected.

    Returns:
        str: The corrected city name.

    Raises:
        None
    """
    if not re.match("^[A-Z ]+$", city):
        logger.error(f"{i()}‼️🚨 Invalid characters in city name: `{city}`")
        city = re.sub(r'[^A-Z ]', '', city).strip()  # Attempt to clean the city name
        logger.debug(f"{i()}✍️ Corrected City Name: `{city}`")
    return city

def correct_state(
    state: str
) -> str:
    """
    Corrects the state name by removing any invalid characters and trimming any leading/trailing whitespace.

    Args:
        state (str): The state name to be corrected.

    Returns:
        str: The corrected state name.

    Raises:
        None
    """
    if not re.match("^[A-Z]{2}$", state):
        logger.error(f"{i()}‼️🚨 Invalid characters in state name: `{state}`")
        state = re.sub(r'[^A-Z]', '', state).strip()[:2]  # Attempt to clean the state name
        logger.debug(f"{i()}✍️ Corrected State Name: `{state}`")
    return state

def validate_and_correct_city_zip(
    city: str,
    state: str,
    zip_code: str
) -> Tuple[str, str, bool]:
    """
    Validates and corrects the city, state, and zip code by comparing them against a list of validated city/state/zip code combinations.

    Args:
        city (str): The city name to be validated and possibly corrected.
        state (str): The state name to be validated and possibly corrected.
        zip_code (str): The zip code to be validated and possibly corrected.

    Returns:
        Tuple[str, str, bool]: A tuple containing the corrected city name (str), corrected state name (str), and a boolean indicating whether the city/state/zip code was validated (bool).
    """
    zip_code = zip_code.split('-')[0].zfill(5).replace(',', '').strip()  # Use the base ZIP code for matching
    city = city.replace(',', '').strip()  # Remove trailing commas and extra spaces
    state = state.replace(',', '').strip()  # Remove trailing commas and extra spaces
    city_zip_data = get_city_zip_data()

    for record in city_zip_data:
        record_city = record['city'].upper()
        record_state = record['state'].upper()
        record_zip = str(record['zip_code']).zfill(5)

        if record_zip == zip_code:
            if record_state == state.upper():
                if fuzz.ratio(record_city, city.upper()) > 90:
                    logger.debug(f"{i()}✅🏢🟰🏢Validated city: `{city}`, state: `{state}`, zip: `{zip_code}` against record: {record}")
                    return city, state, True
                elif not city or fuzz.ratio(record_city, city.upper()) > 60:
                    logger.debug(f"{i()}🔄🏢🟰🏢Corrected city: `{record_city}` for zip: `{zip_code}` and state: `{state}`")
                    return record_city, state, True
            elif record_city == city.upper():
                logger.debug(f"{i()}🔄🏢🟰🏢Corrected state: `{record_state}` for city: `{city}` and zip: `{zip_code}`")
                return city, record_state, True

    logger.error(f"{i()}‼️🚨🏢🙅‍♂️🏣🚨‼️🤔 City/state validation failed for: `{city}`, state: `{state}`, zip: `{zip_code}`")
    return city, state, False

def validate_and_retry(
    reformatted,
    original_address,
    retries =3
) -> str:
    """
    Validates a reformatted address against an original address and retries if necessary.

    This function takes a reformatted address and an original address as input. It then generates a prompt
    to validate the reformatted address and sends it to the Ollama API. If the similarity between the
    initial and validated address is not sufficient, it generates a prompt to check the correctness of
    the validated address. If the correctness is not sufficient, it attempts to correct the validated
    address and retries the validation process. If the address is not corrected after the specified number
    of retries, it returns the original address.

    Args:
        reformatted (str): The reformatted address to be validated.
        original_address (str): The original address to compare against the reformatted address.
        retries (int, optional): The number of times to retry the validation process. Defaults to 3.

    Returns:
        str: The validated address if it is similar and correct, otherwise the original address.
    """
    for _ in range(retries):
        validation_prompt = VALIDATION_PROMPT_TEMPLATE.format(
            original_address=original_address,
            reformatted_address=reformatted,
            EXAMPLES=EXAMPLES2
        )
        logger.debug(f"{i()}🌍📫〽️✍️reformatted: {reformatted}")

        validation_response = ollama.generate(model=MODEL, prompt=validation_prompt)
        validated_address = validation_response['response'].strip()
        validated_address = enforce_english_symbols(validated_address)
        logger.debug(f"{i()}🌍📫〽️✍️Validated Address: `{validated_address}`")

        # Check similarity between initial and validated address
        if similarity(reformatted, validated_address):
            return validated_address

        # Check correctness of the validated address
        correctness_prompt = CORRECTNESS_PROMPT_TEMPLATE.format(
            original_address=original_address,
            reformatted_address=validated_address,
            EXAMPLES=EXAMPLES3
        )
        logger.debug(f"{i()}🌍📫〽️✍️validated_address: `{validated_address}`")
        correctness_response = ollama.generate(model=MODEL, prompt=correctness_prompt)
        correctness_data = correctness_response['response'].strip().split('\n')
        logger.debug(f"{i()}🌍📫〽️✍️Correctness Data: `{correctness_data}`")

        if any("Correctness: Correct" in line for line in correctness_data):
            return validated_address

        # If not correct, retry with corrected address
        corrected_lines = [line for line in correctness_data if "Corrected Address" in line]
        if corrected_lines:
            corrected_address = "\n".join(line.split(": ")[1] for line in corrected_lines if ": " in line).strip()
            logger.debug(f"{i()}🌍📫〽️✍️Corrected Address: `{corrected_address}`")
            reformatted = corrected_address
        else:
            logger.error(f"{i()}‼️🛑🚨🚩‼️🤔Corrected Address not found in Correctness Data: `{correctness_data}`")
            break
    return original_address

def normalize_address(
    address: str
) -> str:
    """
    Normalizes the given address by cleaning it, parsing it, and validating it.

    Parameters:
    ----------
    address : str
        The address to be normalized.

    Returns:
    -------
    str
        The normalized address.

    Raises:
    ------
    Exception
        If an error occurs during the normalization process.
    """
    try:
        # Initial cleaning of the address
        address = re.sub(r'[\n\r\t\u00a0]+', ' ', address)
        # Replace multiple spaces with a single space
        address = re.sub(r'\s+', ' ', address)
        address = address.upper().replace('\n\n', ', ').replace('\n', ', ').replace(' UNITED STATES', '').replace(' USA', '').strip().strip(',').strip().replace(',,', ',').replace('.', '').strip()# + ', USA'
        logger.debug(f"{i()}🌍📫〽️✍️ Cleaned Address: `{address}`")

        # Initial parsing of the address
        try:
            parsed_address, address_type = usaddress.tag(address.upper())
            parsed_address = apply_directionals_and_parts(parsed_address)
            parsed_address = extract_zip_from_address_component(parsed_address, 'PlaceName')
            parsed_address = extract_zip_from_address_component(parsed_address, 'StateName')
            logger.debug(f"{i()}🌍📫〽️✍️Address Type: [green]{address_type}")
            logger.debug(f"{i()}🌍📫〽️✍️Parsed Address: [green]{parsed_address}")

            # Ensure StateName is present if missing
            if 'StateName' not in parsed_address or not parsed_address['StateName']:
                if 'ZipCode' in parsed_address and parsed_address['ZipCode']:
                    zip_code = parsed_address['ZipCode']
                    state = next((record['state'] for record in get_city_zip_data() if str(record['zip_code']).zfill(5) == zip_code.zfill(5)), '')
                    parsed_address['StateName'] = state.upper() if state else ''
                    logger.debug(f"{i()}🌍📫〽️✍️Inferred StateName: `{parsed_address['StateName']}` from ZipCode: `{zip_code}`")

        except usaddress.RepeatedLabelError as e:
            logger.error(f"{i()}🚨🚩🌍📫〽️✍️🛑Error in normalize_address (USAddress): {e}")
            logger.error(f"{i()}🚨🚩🌍📫〽️✍️🛑Original String: {e.original_string}")
            logger.error(f"{i()}🚨🚩🌍📫〽️✍️🛑Parsed String: {e.parsed_string}")
            logger.error(traceback.format_exc())
            return address  # Return the original address if an error occurs

        # recipient = ''
        parsed_pp, pp_type = '', ''
        if 'Recipient' in parsed_address:
            try:
                parsed_pp, pp_type = pp.tag(parsed_address['Recipient'].upper())
                logger.debug(f"{i()}🔹🌍📫〽️✍️Parsed Person Data: {parsed_pp}")
                logger.debug(f"{i()}🔹🌍📫〽️✍️Person Type: {pp_type}")
                # recipient = parsed_address['Recipient']
            except pp.RepeatedLabelError as e:
                logger.error(f"{i()}🔹🚨🚩🌍📫〽️✍️🛑Error in normalize_address (ProbablePeople): {e}")
                logger.error(f"{i()}🔹🚨🚩🌍📫〽️✍️🛑Original String: {e.original_string}")
                logger.error(f"{i()}🔹🚨🚩🌍📫〽️✍️🛑Parsed String: {e.parsed_string}")
                logger.error(traceback.format_exc())

        # Clean and join the parts for Recipient, PlaceName, StreetName, StateName, ZipCode
        for label in ['Recipient', 'PlaceName', 'StreetName', 'StateName', 'ZipCode']:
            if label in parsed_address:
                parsed_address[label] = clean_and_join_parts(parsed_address, label)
        logger.debug(f"{i()}🌍📫〽️✍️ Cleaned and joined parts for address: {parsed_address}")


        logger.debug(f"{i()} Parsed Address (after cleaning and joining): {parsed_address}")

        # # Ensure commas are correctly placed
        # parsed_address = apply_directionals_and_parts(parsed_address)

        # # Remove any empty labels to avoid issues in prompt generation
        # parsed_address = {k: v for k, v in parsed_address.items() if v}
        # logger.debug(f"{i()} Parsed Address (after cleaning and joining): {parsed_address}")

        # # Construct the reformatted address
        # reformatted_address = construct_reformatted_address(parsed_address)
        # logger.debug(f"{i()} Reformatted Address: `{reformatted_address}`")

        # # Validate city name and zip code
        # city = parsed_address.get('PlaceName', '')
        # state = parsed_address.get('StateName', '')
        # zip_code = parsed_address.get('ZipCode', '')

        # if city and state and zip_code:
        #     if not validate_city_zip(city, state, zip_code):
        #         logger.error(f"{i()}🛑❌🚨🚩Invalid city name or zip code detected: `{city}`, `{state}`, `{zip_code}`")
        #         return address  # Return the original address if validation fails
        # else:
        #     logger.error(f"{i()}🛑⛔🚫🚨🚩Failed to parse city:`{city}`, state:`{state}`, or zip code:`{zip_code}` from: `{reformatted_address}`")
        #     return address  # Return the original address if parsing fails

        # # Regex validation
        # if not re.match("^[A-Z ]+$", city):
        #     logger.error(f"{i()}‼️🚨 Invalid characters in city name: `{city}`")
        #     return address  # Return the original address if city name is invalid

        # if not re.match("^[A-Z]+$", state):
        #     logger.error(f"{i()}‼️🚨 Invalid characters in state name: `{state}`")
        #     return address  # Return the original address if state name is invalid

        # If validation fails, call LLM for assistance
        # Step 4: Correct city and state
        city = correct_city(parsed_address.get('PlaceName', ''))
        state = correct_state(parsed_address.get('StateName', ''))
        zip_code = parsed_address.get('ZipCode', '').strip()

        # Step 5: Validate city, state, and zip code
        city, state, valid = validate_and_correct_city_zip(city, state, zip_code)
        if not valid:
            logger.error(f"{i()}🛑❌🚨🚩 Invalid city/state or zip code detected: `{city}`, `{state}`, `{zip_code}`")
            return address  # Return the original address if validation fails

        parsed_address['PlaceName'] = city
        parsed_address['StateName'] = state
        logger.debug(f"{i()}🌍📫〽️✍️ Corrected Address: City: `{city}`, State: `{state}`, Zip: `{zip_code}`")

        # Step 6: Construct the reformatted address
        reformatted_address = construct_reformatted_address(parsed_address)

        # Step 7: Final validation
        if use_llm:
            validated_address = validate_and_retry(reformatted_address, address)
        else:
            validated_address = reformatted_address

        validated_address = validated_address.replace(',,', ',').replace(', ,', ',').replace(', ,', ',')
        validated_address = re.sub(r'\s{2,}', ' ', validated_address)  # Replace multiple spaces with a single space
        logger.debug(f"{i()}✍️🌍📫〽️✍️Final Reformatted Address: `{validated_address}`")

        if echo_output_terminal:
            print(validated_address)

        return validated_address
    except Exception as e:
        logger.error(f"{i()}‼️🛑🚨🚩‼️🤔Exception in normalize_address: {e}")
        logger.error(traceback.format_exc())
        return address  # Return the original address if an error occurs
