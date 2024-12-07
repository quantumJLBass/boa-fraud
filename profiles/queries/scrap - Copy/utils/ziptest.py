from __future__ import annotations

import random
import time
from typing import Tuple  # , List, Dict, Union,

import requests

import gs
from services.applogging import logger, section
from settings.settings import i

# from db.dbefclasses import Address #, URLCatalog, Jurisdiction, Base, Person

# OAuth2 credentials
CLIENT_ID = "aYx9TAVbzO6LPNz7lK5pAf7zpDb9eVft"
CLIENT_SECRET = "IUO7KmuH2CX4XKgy"
TOKEN_URL = "https://api.usps.com/oauth2/v3/token"
ZIPCODE_API_URL = "https://api.usps.com/addresses/v3/zipcode"


def get_access_token(client_id, client_secret) -> str:
    """
    Retrieves an access token from the USPS API using the provided client credentials.

    Args:
        client_id (str): The client ID for the USPS API.
        client_secret (str): The client secret for the USPS API.

    Returns:
        str: The access token for the USPS API.

    Raises:
        requests.exceptions.HTTPError: If the request to the USPS API fails.
    """
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "addresses",
    }

    response = requests.post(TOKEN_URL, data=data, timeout=10)
    response.raise_for_status()
    return response.json().get("access_token")


def parse_address(address):
    """
    Parses an address string into its constituent parts: street address,
    secondary address (if present), city, state, and zip code.

    Args:
        address (str): The address string to parse.

    Returns:
        Tuple[str, str, str, str, str]: The street address, secondary address, city, state, and zip code.
    """
    section("PARSING ADDRESS", color="orange1", justification="right")
    section(f"{address}", color="orange3", justification="center")
    # Handle if address is a tuple (take the first element as the address string)
    parsing_address = None
    if isinstance(address, tuple):
        logger.warning(
            f"{i()} ‼️🚨 address is a tuple, using first element: {address[0]} from {address}"
        )
        parsing_address = address[0]
    else:
        parsing_address = address

    parts = [part.strip() for part in parsing_address.split(",")]

    # Ensure there are at least three parts (city, state, and zip code)
    if len(parts) < 3:
        logger.warning(f"{i()} ‼️🚨 Invalid address format: {parsing_address}")
        return None, None, None, None, None

    try:
        city, state, zip_code = parts[-3], parts[-2], parts[-1]
        # Assume everything before the last three parts is the street information
        street_address = parts[0]
        # Optional secondary address
        secondary_address = parts[1] if len(parts) > 4 else None
        section(f"{street_address}, {secondary_address}, {city}, {state}, {zip_code}")
        section("EXITING --- PARSING ADDRESS", color="green", justification="center")
        return street_address, secondary_address, city, state, zip_code
    except IndexError as e:
        logger.error(f"{i()} ‼️🚨 Error parsing address: {parsing_address}. Error: {e}")
        section(
            "EXITING --- PARSING ADDRESS BADDLY",
            color="bright_red",
            justification="center",
        )
        return None, None, None, None, None


def lookup_zipcode(address: str) -> Tuple[str, Address]:
    """
    Look up a zip code for a given address.

    Args:
        address (str): The address to look up.

    Returns:
        Tuple[str, Address]: A tuple containing the formatted address and an
        Address object.

    Raises:
        requests.exceptions.HTTPError: If the request to the USPS API fails.
    """
    from db.dbefclasses import Address

    section("ZIPCODE LOOK UP", color="orange1", justification="right")
    token = get_access_token(CLIENT_ID, CLIENT_SECRET)

    street_address, secondary_address, city, state, zip_code = parse_address(address)

    # Request parameters
    params = {
        "streetAddress": street_address,
        "city": city,
        "state": state,
        "ZIPCode": zip_code,
    }

    if secondary_address:
        params["secondaryAddress"] = secondary_address

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Make the GET request to the USPS API
    response = requests.get(ZIPCODE_API_URL, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    data = response.json().get("address", {})

    # Build the standardized address string
    street = data.get("streetAddress", "")
    secondary = data.get("secondaryAddress", "")
    city = data.get("city", "")
    state = data.get("state", "")
    zip_code = data.get("ZIPCode", "")
    zip_plus4 = data.get("ZIPPlus4", "")

    # Format the address based on the presence of secondaryAddress
    if secondary:
        formatted_address = (
            f"{street}, {secondary}, {city}, {state}, {zip_code}-{zip_plus4}"
        )
    else:
        formatted_address = f"{street}, {city}, {state}, {zip_code}-{zip_plus4}"

    # Create the Address object
    address_obj = Address(
        normalized_address=formatted_address,
        street=street,
        street_2=secondary,
        city=city,
        state=state,
        postal_code=f"{zip_code}-{zip_plus4}",
        country="USA",
        raw_data=address,
    )
    rando = random.uniform(1, 5)
    logger.info(
        f"{i()} ✅ done with lookup_zipcode so just a breathe for {rando}time, we are done with {gs.current_url}"
    )
    gs.console.rule()
    time.sleep(rando)

    section("EXITING --- ZIPCODE LOOK UP", color="green", justification="center")

    return formatted_address, address_obj


# # List of addresses to process
# addresses = [
#     'PO BOX 767, GYPSUM, CO, 81637',
#     '1709 N 19TH ST, STE 3, BISMARCK, ND, 58501-2121',
#     '1500 14TH W ST, STE 100, WILLISTON, ND, 58801-4077',
#     '38 2ND E AVE, STE B, DICKINSON, ND, 58601',
#     '2105 ORGEON AVE, BUTTE, MT, 59701',
#     '26 W 6TH AVE, HELENA, MT 59624-1691',
#     '1001 S MAIN ST, STE 49, KALISPELL, MT, 59901',
#     '2200 W MAIN ST, STE 900, DURHAM, NC, 27705-4643',
#     '6623 OLD STATESVILLE RD, CHARLOTTE, NC, 28269-1749',
#     '2 S SALISBURY ST, RALEIGH, NC, 27601',
#     '2527 W KIT CARSON TRL, PHOENIX, AZ, 85086',
#     '2338 W ROYAL PALM RD, PHOENIX, AZ, 85021',
#     '1846 E INNOVATION PARK DR, STE 100, ORO VALLEY, AZ, 85755',
#     '2707 LEXINGTON RD, LOUISVILLE, KY, 40206',
#     '22 GARRISON AVE, FORT THOMAS, KY, 41075',
#     '300 S SPRING ST, STE 900, LITTLE ROCK, AR, 72201',
#     '2 N COLLEGE, FAYETTEVILLE, AR, 72701',
#     '109 EXECUTIVE DR, STE 3, MADISON, MS, 39110',
#     '117 FULTON ST, GREENWOOD, MS, 38930',
#     '5779 GETWELL RD, SOUTHAVEN, MS, 38672',
#     '3013 YAMATO RD, STE B12-BOX 105, BOCA RATON, FL, 33434',
#     '1093 ARBOR LN, JACKSONVILLE, FL, 32207',
#     '125 S STATE RD 7, WEST PALM BEACH, FL, 33414',
#     '3866 PROSPECT AVE, RIVIERA BEACH, FL, 33404',
# ]

# # Process each address and print the results
# for address in addresses:
#     try:
#         standardized_address = lookup_zipcode(address)
#         print(f"Original Address: {address}")
#         print(f"Standardized Address: {standardized_address}\n")
#     except Exception as e:
#         print(f"Failed to lookup address: {address}")
#         print(f"Error: {e}\n")
