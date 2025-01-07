import traceback

# from pathlib import Path
from typing import Optional, Dict, Union

# import gs
from services.applogging import logger, section
from settings.settings import i
from utils.useollama import normalize_address
from utils.ziptest import lookup_zipcode, parse_address

# from sqlalchemy.exc import IntegrityError


# from utils.utils import (extract_company_number_from_url,
#                          extract_jurisdiction_from_url, normalize_textblocks)
# from db.dbefclasses import  (CompanyAddress, PeopleAddress)
md_contents = """
---
tags:
- MOCs
entry-taxonomic-rank: family
---
```folder-overview
id: {ID}
folderPath: ""
title: "{{folderName}} overview"
showTitle: true
depth: 4
style: explorer
includeTypes:
- folder
- all
disableFileTag: true
sortBy: name
sortByAsc: true
showEmptyFolders: false
onlyIncludeSubfolders: false
storeFolderCondition: true
showFolderNotes: true
disableCollapseIcon: true
```
"""


def catalog_address_record(raw_address: str) -> Optional[Address]:
    """
    Catalog an address record, normalizing and validating the address before insertion.

    Args:
        raw_address (str): The address to catalog.

    Returns:
        Optional[Address]: The Address object if successfully cataloged, or None if there was an error.
    """
    from db.dbefclasses import Address

    section("CATALOG ADDRESS RECORD", color="orange1", justification="right")
    try:
        # Normalize the address
        normalized_address = normalize_address(raw_address)
        logger.info(
            f"{i()}🪧📬📨 from catalog_address_record NORMALIZED ADDRESS: {normalized_address}"
        )

        # Validate and standardize the address using lookup_zipcode
        standardized_address = lookup_zipcode(normalized_address)
        if not standardized_address:
            logger.error(
                f"{i()}🪧📬📨🛑❌ Unable to standardize address: {raw_address}"
            )
            return None
        logger.info(
            f"{i()}🪧📬📨 from catalog_address_record STANDARDIZED ADDRESS: {standardized_address}"
        )
        # Parse the standardized address
        street_address, secondary_address, city, state, zip_code = parse_address(
            standardized_address
        )
        if not all([street_address, city, state, zip_code]):
            logger.error(
                f"{i()}🪧📬📨🛑❌ Invalid or incomplete PARSED ADDRESS: {raw_address}"
            )
            return None

        logger.info(
            f"{i()}🪧📬📨 PARSED ADDRESS: {street_address}, {secondary_address}, {city}, {state}, {zip_code}"
        )

        # Prepare the address data for the record
        address_data = {
            "normalized_address": standardized_address,
            "raw_data": raw_address,
            "street": street_address,
            "street_2": secondary_address,
            "city": city,
            "state": state,
            "postal_code": zip_code,
            "country": "USA",
        }

        # Check if the address already exists using the mixin
        where_conditions = [
            f"(street = '{street_address}')",
            f"(city = '{city}')",
            f"(state = '{state}')",
            f"(postal_code = '{zip_code}')",
        ]
        existing_address = Address.fetch(where=where_conditions, limit=1)

        if existing_address:
            logger.info(
                f"{i()}🪧📬📨✅ ADDRESS ALREADY EXISTS in the database with ID: {existing_address.id}"
            )
            return existing_address  # Return the existing address object

        # Catalog the new address using the mixin
        new_address = Address.catalog(data=address_data)
        if new_address:
            logger.info(
                f"{i()}🪧📬📨✅✅ Successfully CATALOGED NEW ADDRESS with ID: {new_address.id}"
            )
            return new_address

    except Exception as e:
        logger.error(
            f"{i()}📛📛🪧📬📨 ERROR CATALOGING raw_address: {raw_address}. Error: {e}"
        )
        logger.error(traceback.format_exc())
        return None


def catalog_people_address(address: str, person_id: int) -> Optional[Address]:
    """
    Catalogs a person's address by inserting or updating the address and creating a PeopleAddress record.

    Args:
        address (str): The address string to be cataloged.
        person_id (int): The person ID associated with the address.

    Returns:
        Optional[Address]: The Address object if successfully cataloged, or None if there was an error.
    """
    from db.dbefclasses import PeopleAddress

    # Catalog the address and get the address object
    address_obj = catalog_address_record(address)
    if address_obj:
        address_id = address_obj.id
        standardized_address = address_obj.normalized_address
        # Use standardized_address as needed

        if address_id and person_id:
            # No need to check for existence; use conflict resolution directly
            address_data = {"address_id": address_id, "person_id": person_id}
            people_address = PeopleAddress(**address_data)
            people_address.catalog(data=address_data)
        return address_obj
    return None


def catalog_company_address(address: str, company_number: str) -> Optional[Address]:
    """
    Catalogs a company's address by inserting or updating the address and creating a CompanyAddress record.

    Args:
        address (str): The address string to be cataloged.
        company_number (str): The company number associated with the address.

    Returns:
        Optional[Address]: The Address object if successfully cataloged, or None if there was an error.
    """
    from db.dbefclasses import CompanyAddress

    # Catalog the address and get the address object
    address_obj = catalog_address_record(address)
    if address_obj:
        address_id = address_obj.id
        standardized_address = address_obj.normalized_address
        # Use standardized_address as needed

        if address_id and company_number:
            # No need to check for existence; use conflict resolution directly
            address_data = {"address_id": address_id, "company_number": company_number}
            company_address = CompanyAddress(**address_data)
            company_address.catalog(data=address_data)
        return address_obj
    return None
