# from services.applogging import *
# from settings.settings import *
# from utils.utils import *
# from services.scraper import *
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy import create_engine, func, text, and_, or_
# import sqlite3
# import json
# import os
# import re
# from typing import Dict, Any
# import traceback

# def load_jurisdictions(json_path):

#     try:
#         with open(json_path, 'r', encoding='utf-8') as f:
#             data = json.load(f)['us_state_cities']

#         for j in data:
#             try:
#                 # Find parent_jurisdiction based on state abbreviation
#                 parent_jurisdiction = gs.read.query(Jurisdiction).filter(Jurisdiction.state_abv == j['state'].lower()).first()
#                 parent_jurisdiction_id = parent_jurisdiction.id if parent_jurisdiction else None

#                 # Handle empty strings or missing values for longitude and latitude
#                 longitude = float(j['longitude']) if j['longitude'] else None
#                 latitude = float(j['latitude']) if j['latitude'] else None

#                 # Format zip_code to be 5 digits
#                 zip_code = str(j['zip_code']).zfill(5)

#                 # Lookup full state name from the Jurisdiction table based on state abbreviation
#                 state_jurisdiction = gs.read.query(Jurisdiction).filter(Jurisdiction.state_abv == j['state'].lower(), Jurisdiction.parent_jurisdiction == None).first()
#                 state_full_name = state_jurisdiction.name if state_jurisdiction else j['state']
#                 city = j['city'] if j['city'] else None
#                 county = j['county'] if j['county'] else None


#                 jurisdiction_data = Jurisdiction(
#                     code=zip_code,
#                     name=j['city'],
#                     country='United States',
#                     full_name=state_full_name,
#                     state_abv=j['state'].lower(),
#                     county=county,
#                     city=city,
#                     longitude=longitude,
#                     latitude=latitude,
#                     zip_code=zip_code,
#                     area_code=j.get('area_code', None),
#                     parent_jurisdiction=parent_jurisdiction_id
#                 )

#                 # Check if the record already exists
#                 existing = gs.read.query(Jurisdiction).filter(Jurisdiction.code == zip_code).first()
#                 if existing is None:
#                     gs.write.add(jurisdiction_data)
#                     print(f"Inserted: {city or ''}, {county or ''}, {state_full_name or ''} {zip_code or ''}")
#                 else:
#                     print(f"Duplicate code found: {zip_code}")

#             except ValueError as ve:
#                 print(f"ValueError: {ve} for data: {j}")
#                 gs.write.rollback()
#             except SQLAlchemyError as e:
#                 print(f"SQLAlchemyError: {e} for data: {j}")
#                 gs.write.rollback()
#             except Exception as e:
#                 print(f"Unexpected error: {e} for data: {j}")
#                 gs.write.rollback()

#         gs.write.commit()

#     except Exception as e:
#         print(f"Error loading data: {e}")
#         logger.error(f"{traceback.format_exc()}")
#         gs.write.rollback()

#     finally:
#         gs.write.close()

# def load_jurisdictionsA(json_path):
#     engine = create_engine(f'sqlite:///{DB_FILE}')
#     metadata = MetaData()
#     jurisdictions = Table('jurisdiction', metadata, autoload_with=engine)

#     with open(json_path, 'r', encoding='utf-8') as f:
#         data = json.load(f)['results']['jurisdictions']

#     with engine.connect() as conn:
#         for j in data:
#             jurisdiction_data = {
#                 'code': j['jurisdiction']['code'],
#                 'name': j['jurisdiction']['name'],
#                 'country': j['jurisdiction']['country'],
#                 'full_name': j['jurisdiction']['full_name']
#             }
#             print(f"Processing: {jurisdiction_data}")  # Debug statement
#             # Check if the record already exists
#             query = jurisdictions.select().where(jurisdictions.c.code == j['jurisdiction']['code'])
#             result = conn.execute(query).fetchone()
#             if result is None:
#                 conn.execute(jurisdictions.insert().values(jurisdiction_data))
#                 print(f"Inserted: {j['jurisdiction']['code']}")
#             else:
#                 print(f"Duplicate code found: {j['jurisdiction']['code']}")
#         conn.commit()  # Ensure all changes are committed

# def initialize_db(fix: bool = False):
#     """
#     Initialize the SQLite database and create the necessary tables using SQLAlchemy ORM models.
#     """
#     logger.info("Initializing the database and creating tables.")
#     try:
#         print('needs to fix state')
#         # load_jurisdictions('E:/_GIT/obsidian/BoA timeline/profiles/queries/scrap/db/sample data/jurisdictions.json')
#         # This creates all tables based on the ORM models defined in db_ef_classes.py
#         # Base.metadata.create_all(engine)
#         # load_jurisdictionsA('E:/_GIT/obsidian/BoA timeline/profiles/queries/scrap/db/sample data/jurisdictions.json')
#         # load_jurisdictions("E:\\_GIT\\obsidian\\BoA timeline\\profiles\\queries\\scrap\\address-normalization-data.json")
#         # logger.info("Database tables created successfully.")
#     except Exception as e:
#         logger.error(f"Error initializing database: {e}")
#         logger.error(f"{traceback.format_exc()}")
