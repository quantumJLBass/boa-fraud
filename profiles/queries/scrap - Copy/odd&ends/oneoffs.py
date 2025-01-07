# # scraper.py
# # import json
# import os
# # import re
# # import copy
# from pathlib import Path
# # from bs4 import BeautifulSoup, Tag
# from loguru import logger
# from sqlalchemy.exc import IntegrityError
# # from sqlalchemy.orm import sessionmaker
# # from sqlalchemy import create_engine
# import probablepeople as pp
# # from selenium.webdriver.remote.webdriver import WebDriver
# import gs
# from .db.db_ef_classes import Person#, URLCatalog, Jurisdiction, Base, Address,
# from .settings import *
# from .services.applogging import *
# from .utils import *
# from .utils.useollama import *
# # from urllib.parse import urljoin, urlparse, parse_qs
# # from typing import List, Dict, Union, Tuple
# # from db.cache import load_cache, url_cached, catalog_cache, bulk_save_urls, get_base_url_id,get_uncached_urls
# from .utils.ziptest import *

# def insert_people():
#     """
#     Inserts people from the '../../people/' directory into the SQLite database.
#     """
#     section("📁👤 INSERTING PEOPLE 👤📁", "sea_green2", "center")

#     people_dir = Path(__file__).resolve().parent.parent.parent / 'people'

#     try:
#         for folder_name in os.listdir(people_dir):
#             if folder_name.lower() in ['people', 'staging', 'people.md']:
#                 continue

#             try:
#                 parsed_name, name_type = pp.tag(folder_name)
#             except pp.RepeatedLabelError:
#                 logger.error(f"{i()}💥🚩 ERROR PARSING NAME ----- {folder_name}: RepeatedLabelError")
#                 continue

#             # Add full_name and raw_data to the parsed_name dictionary
#             person_data = parsed_name.copy()
#             person_data['full_name'] = folder_name
#             person_data['raw_data'] = folder_name

#             try:
#                 person = Person(**person_data)
#                 gs.write.add(person)
#                 gs.write.commit()
#                 logger.info(f"{i()}✅👤 PERSON INSERTED ----- {folder_name}")
#             except IntegrityError:
#                 gs.write.rollback()
#                 logger.info(f"{i()}🔄👤 PERSON EXISTS ----- {folder_name}")
#             except Exception as e:
#                 gs.write.rollback()
#                 logger.error(f"{i()}💥🚩 ERROR INSERTING PERSON ----- {folder_name}: {str(e)}")

#     except OSError as e:
#         logger.error(f"{i()}💥🚩 ERROR ACCESSING DIRECTORY ----- {people_dir}: {str(e)}")
#     finally:
#         gs.write.close()
#         logger.info(f"{i()}🏁📁 FINISHED INSERTING PEOPLE")

# def insert_addresses():
#     """
#     Inserts addresses from the '../../addresses/' directory into the SQLite database.

#     This function reads the folder names in the specified directory, treats each folder name as an address,
#     and inserts it into the Address table in the database. It handles various address formats, including
#     those with and without secondary address lines (e.g., suite numbers).

#     The function follows these steps:
#     1. Constructs the path to the addresses directory.
#     2. Iterates through the folder names in the directory.
#     3. Parses each address into its components, handling various formats.
#     4. Attempts to insert each address into the database.
#     5. Logs the results of each insertion attempt.

#     Returns:
#         None

#     Raises:
#         OSError: If there's an error accessing the directory.
#     """
#     md_contents = """
# ---
# tags:
# - MOCs
# entry-taxonomic-rank: family
# ---
# ```folder-overview
# id: {ID}
# folderPath: ""
# title: "{{folderName}} overview"
# showTitle: true
# depth: 4
# style: explorer
# includeTypes:
# - folder
# - all
# disableFileTag: true
# sortBy: name
# sortByAsc: true
# showEmptyFolders: false
# onlyIncludeSubfolders: false
# storeFolderCondition: true
# showFolderNotes: true
# disableCollapseIcon: true
# ```
#     """
#     # List of address strings
#     addresses = [
#         # '100 N HOWARD ST, STE R, SPOKANE, WA, 99201',
#         # '100 N HOWARD ST, STE W, SPOKANE, WA, 99201-0508',
#         # '600 KITSAP ST, STE 202, PORT ORCHARD, WA, 98366-5397',
#         # '3010 BETHEL SE RD, PORT ORCHARD, WA, 98366-2410',
#         # 'PO BOX 589, PORT ORCHARD, WA, 98366-0589',
#         # '1001 BISHOP ST, STE 1600, HONOLULU, HI, 96813-3698', #COUNTY: HONOLULU
#         # '725 KAPIOLANI BLVD, STE C110, HONOLULU, HI, 96813-6000', #COUNTY: HONOLULU
#         # '239 NW 13TH, STE 310, PORTLAND, OR, 97209',
#         # '985 E MAIN ST, HERMISTON, OR, 97838-2061',
#         # '503 S WESTGATE ST, STE B, ADDISON, IL, 60101-4531',
#         # '4199 GATEWAY BLVD, STE 2000, NEWBURGH, IN, 47630',
#         # '2501 SAN PEDRO NE DR, STE 102, ALBUQUERQUE, NM, 87110',
#         # '101 STATE HOUSE STA, AUGUSTA, ME, 04333',
#         # '1015 15TH NW ST, STE 1000, DC, 20005',
#         # '10770 LOWER COALING RD, COTTONDALE, AL, 35453-2837',
#         # '244 INVERNESS CTR, STE 200, BIRMINGHAM, AL, 35242',
#         # '1095 SUGAR VIEW DR, STE 500, SHERIDAN, WY, 82801',
#         # '1309 COFFEEN AVE, STE 2444, SHERIDAN, WY, 82801-5777',
#         # '724 FRONT ST, STE 340, EVANSTON, WY, 82930',
#         # '406 W LOUCKS ST, SHERIDAN, WY, 82801',
#         # '138 HAMMOND DR, STE B, ATLANTA, GA, 30328',
#         # '809 3RD AVE, WEST POINT, GA, 31833',
#         # '14363 WOLF CREEK CRT, SUMMERSET, SD, 57769',
#         # '25 1ST SW AVE, STE A, WATERTOWN, SD, 57201-3507',
#         # '148 B BRANDY MILL CIRCLE, HIGH RIDGE, MO, 63049',
#         # '120 S CENTRAL AVE, CLAYTON, MO, 63105',
#         # '600 W MAIN ST, JEFFERSON CITY, MO, 65102',
#         # '221-07 113TH DR, QUEENS VILLAGE, NY, 11429',
#         # '24 OFFICE PARK CT, STE A, COLUMBIA, SC, 29223-5967',
#         # '190 MAPLERIDGE DR, WATERBURY, CT, 06705',
#         # '6007 FINANCIAL PLZ, STE 206, SHREVEPORT, LA, 71129-2675',
#         # '320 SOMERULOS ST, BATON ROUGE, LA, 70802-6129',
#         # '8235 YMCA PLAZA DR, STE 400, BATON ROUGE, LA, 70810',
#         # '10540 BLANCHARD FURRH RD, MOORINGSPORT, LA, 71060-8585',
#         # '635 N BROAD ST, FREMONT, NE, 68102',
#         # '314 S 19TH ST, OMAHA, NE, 68102-1912',
#         # '6931 ANDERSON ST, PHILADELPHIA, PA, 19119',
#         # '2020 ARAPAHOE ST, STE LL, DENVER, CO, 80205',
#         # '355 UNION BLVD, STE 250, LAKEWOOD, CO, 80228',
#         # '5680 PECOS ST, DENVER, CO, 80221',
#         # '1305 KRAMERIA ST, UNIT H-118, DENVER, CO, 80220',
#         # '4100 E MISSISSIPPI AVE, STE 420, DENVER, CO, 80246',
#         # '7 VILLAGE DR, LITTLETON, CO, 80123',
#         # '0170 AUTUMN GLEN ST, GYPSUM, CO, 81637',
#         # 'PO BOX 767, GYPSUM, CO, 81637',
#         # '1709 N 19TH ST, STE 3, BISMARCK, ND, 58501-2121',
#         # '1500 14TH W ST, STE 100, WILLISTON, ND, 58801-4077',
#         # '38 2ND E AVE, STE B, DICKINSON, ND, 58601',
#         '2105 ORGEON AVE, BUTTE, MT, 59701',
#         '26 W 6TH AVE, HELENA, MT 59624-1691',
#         # '1001 S MAIN ST, STE 49, KALISPELL, MT, 59901',
#         # '2200 W MAIN ST, STE 900, DURHAM, NC, 27705-4643',
#         # '6623 OLD STATESVILLE RD, CHARLOTTE, NC, 28269-1749',
#         # '2 S SALISBURY ST, RALEIGH, NC, 27601',
#         # '2527 W KIT CARSON TRL, PHOENIX, AZ, 85086',
#         # '2338 W ROYAL PALM RD, PHOENIX, AZ, 85021',
#         # '1846 E INNOVATION PARK DR, STE 100, ORO VALLEY, AZ, 85755',
#         # '2707 LEXINGTON RD, LOUISVILLE, KY, 40206',
#         # '22 GARRISON AVE, FORT THOMAS, KY, 41075',
#         # '300 S SPRING ST, STE 900, LITTLE ROCK, AR, 72201',
#         # '2 N COLLEGE, FAYETTEVILLE, AR, 72701',
#         # '109 EXECUTIVE DR, STE 3, MADISON, MS, 39110',
#         # '117 FULTON ST, GREENWOOD, MS, 38930',
#         # '5779 GETWELL RD, SOUTHAVEN, MS, 38672',
#         # '3013 YAMATO RD, STE B12-BOX 105, BOCA RATON, FL, 33434',
#         # '1093 ARBOR LN, JACKSONVILLE, FL, 32207',
#         # '125 S STATE RD 7, WEST PALM BEACH, FL, 33414',
#         # '3866 PROSPECT AVE, RIVIERA BEACH, FL, 33404',
#         # '810 NW 57 ST, FT LAUDERDALE, FL, 33309',
#         # '601 ABBOTT RD, EAST LANSING, MI, 48823',
#         # '16250 NORTHLAND DR, STE 220, SOUTHFIELD, MI, 48075',
#         # '24655 SOUTHFIELD RD, STE 100, SOUTHFIELD, MI, 48075',
#         # '30600 TELEGRAPH ROAD BINGHAM FARMS MI 48025',
#         # '251 LITTLE FALLS DR, WILMINGTON, DE, 19808-1674',
#         # 'PO BOX 1677, 1813 N FRANKLIN ST, WILMINGTON, DE, 19802',
#         # '1209 ORANGE ST, WILMINGTON, DE, 19801',
#         # '3270 E INLAND EMPIRE BLVD, STE 100, ONTARIO, CA, 91764',
#         # '1651 E 4TH ST, STE 12, SANTA ANA, CA, 92701',
#         # '173 MEADOWCROFT WAY, SANTA ROSA, CA, 95403',
#         # '1820 W ORANGEWOOD AVE, STE 104, ORANGE, CA, 92868',
#         # '120 1/2 S EL CAMINO REAL, FL 2ND, SAN CLEMENTE, CA, 92672',
#         # '3775 SAGE CYN, ENCINITAS, CA, 92024',
#         # '4300 B ST, STE 206, ANCHORAGE, AK, 99503',
#         # '9360 GLACIER HWY, STE 202, JUNEAU, AK, 99801',
#         # '801 W 10TH ST, STE 300, JUNEAU, AK, 99801',
#         # '435 FORD RD, STE 600, SAINT LOUIS PARK, MN, 55426',
#         # '380 JACKSON STR, STE 700, SAINT PAUL, MN, 55101',
#         '6TH & MARQUETTE, 17TH FLR, NORWEST CTR, MINNEAPOLIS, MN, 55479',
#         '6TH & MARQUETTE, MS 1013, NORWEST CTR, MINNEAPOLIS, MN, 55479',
#         # '90 S 6TH ST, MINNEAPOLIS, MN, 55402-1109',
#         # '1333 NORTHLAND DR, STE 205, MENDOTA HEIGHTS, MN, 55120',
#         # '4516 EOFF ST, WHEELING, WV, 26003',
#         # '209 W WASHINGTON ST, CHARLESTON, WV, 25302',
#         # '4530 S EASTERN AVE, STE 10, LAS VEGAS, NV, 89119-6181',
#         # '2510 E SUNSET RD, # 5-512, LAS VEGAS, NV, 89120',
#         # '400 S 4TH ST, STE 650, LAS VEGAS, NV, 89101',
#         # '701 BRAZOS ST, STE 1050, AUSTIN, TX, 78701-3232',
#         # '2020 SOUTHWEST FWY, STE 300, HOUSTON, TX, 77098',
#         # '2525 E CEDAR DR, EAGLE MOUNTAIN, UT, 84005-4100',
#         # '15145 N 4400 W, GARLAND, UT, 84312',
#         # '198 N MAIN, STE 200, LOGAN, UT, 84321',
#         # '1493 E RIDGELINE DR, SOUTH OGDEN, UT, 84405-4947',
#         # '1005 N GROVE DR, ALPINE, UT, 84004',
#         # '3138 N 1250 W, PLEASANT VIEW, UT, 84414-1665',
#         # '3138 N 1250 W, PLEASANT VIEW, UT, 84414-1665',
#         # '701 S MAIN ST, STE 400, LOGAN, UT, 84321',
#         # '3877 W SLALOM WAY, COLLINSTON, UT, 84306',
#         # '399 N MAIN ST, STE 300, LOGAN, UT, 84321',
#         # '376 E 400 S, STE 300, SALT LAKE CITY, UT, 84111-2906',
#         # '3448 W SPRING CIR, MOUNTAIN GREEN, UT, 84050-6740',
#         # '40 W CACHE VALLEY BLVD, STE 9A, LOGAN, UT, 84341',
#         # '965 S 100 W, STE 203, LOGAN, UT, 84321',
#         # '3907 MOCCASIN RD, COEUR D ALENE, ID, 83815',
#         # '784 S CLEARWATER LOOP, STE R, POST FALLS, ID, 83854',
#         # '715 N PLEASANT VIEW RD, POST FALLS, ID, 83854-5223',
#         # '300 W MAIN ST, 150, BOISE, ID, 83702'
#     ]
#     # Construct the path to the addresses directory
#     addresses_dir = Path(__file__).resolve().parent.parent.parent / 'addresses-test'
#     for address in addresses:
#         try:
#             good_address, address_obj = lookup_zipcode(address)
#             time.sleep(60)
#             folder_path = Path(addresses_dir) / good_address  # Create a path object for the folder
#             subfolder = folder_path / 'files'
#             subfolder.mkdir(parents=True, exist_ok=True)  # Create the directory

#             # Create the markdown file inside the folder
#             markdown_file_path = folder_path / f"{good_address}.md"
#             with markdown_file_path.open('w', encoding='utf-8') as file:
#                 file.write(md_contents)

#             try:
#                 with gs.write() as session:
#                     # Attempt to insert the address into the database
#                     session.add(address_obj)
#                     session.commit()
#                     logger.info(f"{i()}✅🏠 ADDRESS INSERTED ----- {folder_path}")
#             except IntegrityError:
#                 with gs.write() as session:
#                     session.rollback()
#                 logger.info(f"{i()}🔄🏠 ADDRESS EXISTS ----- {folder_path}")
#                 logger.error(f"{traceback.format_exc()}")
#             except Exception as e:
#                 with gs.write() as session:
#                     session.rollback()
#                 logger.error(f"{i()}💥🚩 ERROR INSERTING ADDRESS ----- {folder_path}: {str(e)}")
#                 logger.error(f"{traceback.format_exc()}")

#         except Exception as e:
#             logger.error(f"💥🚩Error processing {address}: {e}")
#             logger.error(f"{traceback.format_exc()}")
#         finally:
#             logger.info(f"{i()}🏁📁 FINISHED INSERTING ADDRESSES")

#     section("📁🏠 INSERTING ADDRESSES 🏠📁", "sea_green2", "center")



#     # try:
#     #     # Iterate through the folder names in the directory
#     #     for folder_name in os.listdir(addresses_dir):
#     #         # Parse the address
#     #         parts = folder_name.split(', ')

#     #         # Initialize variables
#     #         street = street_2 = city = state = postal_code = ''

#     #         # Parse based on the number of parts
#     #         if len(parts) >= 4:
#     #             *street_parts, city, state, postal_code = parts
#     #             if len(street_parts) > 1:
#     #                 street = street_parts[0]
#     #                 street_2 = ', '.join(street_parts[1:])
#     #             else:
#     #                 street = street_parts[0]
#     #         elif len(parts) == 3:
#     #             street, city, state_zip = parts
#     #             state, postal_code = state_zip.split(' ', 1)

#     #         # Create an Address object
#     #         address = Address(
#     #             normalized_address=folder_name,
#     #             street=street,
#     #             street_2=street_2,
#     #             city=city,
#     #             state=state,
#     #             postal_code=postal_code,
#     #             country='USA',  # Assuming all addresses are in the USA
#     #             raw_data=folder_name
#     #         )

#     #         try:
#     #             # Attempt to insert the address into the database
#     #             globals.write.add(address)
#     #             globals.write.commit()
#     #             logger.info(f"{i()}✅🏠 ADDRESS INSERTED ----- {folder_name}")
#     #         except IntegrityError:
#     #             globals.write.rollback()
#     #             logger.info(f"{i()}🔄🏠 ADDRESS EXISTS ----- {folder_name}")
#     #         except Exception as e:
#     #             globals.write.rollback()
#     #             logger.error(f"{i()}💥🚩 ERROR INSERTING ADDRESS ----- {folder_name}: {str(e)}")

#     # except OSError as e:
#     #     logger.error(f"{i()}💥🚩 ERROR ACCESSING DIRECTORY ----- {addresses_dir}: {str(e)}")
#     # finally:
#     #     globals.write.close()
#     #     logger.info(f"{i()}🏁📁 FINISHED INSERTING ADDRESSES")
