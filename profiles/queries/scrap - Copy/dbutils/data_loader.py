# import os
# import json
# from loguru import logger
# from applogging import *
# from settings import *
# from utils import *

# # from db.init_db import *
# # from db.companies import *
# # from db.attributes import *
# # from db.officers import *
# # from db.events import *
# # from db.filings import *
# # from db.assertions import *
# # from db.branch_relationships import *
# # from db.links import *
# # from db.init_db import initialize_db
# # from db.companies import catalog_company
# # from db.attributes import catalog_attribute
# # from db.officers import catalog_officer
# # from db.events import catalog_event
# # from db.filings import catalog_filing
# # from db.assertions import catalog_assertion
# # from db.branch_relationships import catalog_branch_relationship
# # from db.links import catalog_link



# from scraper import *
# from typing import List, Dict, Union, Tuple
# import gs
# from loguru import logger
# from bs4 import BeautifulSoup
# from selenium.webdriver.remote.webdriver import WebDriver
# import sqlite3
# import json
# import os
# import re
# from typing import Dict, Any

# # def load_data_from_json(file_path):
# #     """
# #     Load company data from a JSON file and catalog the data into the database.
# #     """
# #     with open(file_path, 'r', encoding='utf-8') as json_file:
# #         data = json.load(json_file)

# #     # Loop over each company in the data
# #     for company_url, company_data in data.items():
# #         if 'Attributes' in company_data:
# #             company_number = company_data['Attributes']['Company Number']
# #             catalog_company(company_number, company_data)

# #             # Insert attributes
# #             attributes = company_data.get('Attributes', {})
# #             for key, value in attributes.items():
# #                 catalog_attribute(company_number, key, value)

# #             # Insert officers
# #             officers = company_data.get('Officers', [])
# #             for officer in officers:
# #                 catalog_officer(company_number, officer)

# #             # Insert events
# #             events = company_data.get('Events', [])
# #             for event in events:
# #                 catalog_event(company_number, event)

# #             # Insert links
# #             links = company_data.get('Links', [])
# #             for link in links:
# #                 catalog_link(company_number, link)

# #             # Insert filings
# #             filings = company_data.get('Filings', [])
# #             for filing in filings:
# #                 catalog_filing(company_number, filing)

# #             # Insert assertions
# #             assertions = company_data.get('Assertions', {})
# #             for assertion_type, assertion_list in assertions.items():
# #                 for assertion in assertion_list:
# #                     catalog_assertion(company_number, assertion)

# #             # Insert branch relationships
# #             branches = company_data.get('Branch Relationships', [])
# #             for branch in branches:
# #                 catalog_branch_relationship(company_number, branch)
# #         else:
# #             logger.warning(f"{i()}⚠️ No 'Attributes' key found for company URL: {company_url}")
