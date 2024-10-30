import re
# from services.applogging import logger
from settings import *
from utils import *
# from scraper import *
# from typing import List, Dict, Union, Tuple


# import json
# import os
# from typing import Dict, Any


# def build_conditions(where: list):
#     """
#     Builds SQLAlchemy conditions from a structured list.

#     Args:
#         where (list): A list of conditions with strings or lists of conditions.
#                     Use '&' or no prefix for 'AND', '|' for 'OR'.

#     Returns:
#         list: A list of SQLAlchemy conditions.
#     """
#     conditions = []
#     for condition in where:
#         if isinstance(condition, list):
#             sub_conditions = [text(c.lstrip('|&')) for c in condition]
#             conditions.append(or_(*sub_conditions) if '|' in condition[0] else and_(*sub_conditions))
#         else:
#             conditions.append(text(condition.lstrip('|&')))
#     return conditions

# def fetch_records(
#     model,
#     columns: list,
#     limit: int = 1000,
#     sort_by: str = None,
#     group_by: str = None,
#     random_sample: bool = False,
#     where: list = None
# ) -> list:
#     """
#     Fetches records from a specified model/table with optional sorting, grouping, random sampling, and filtering.

#     Args:
#         model (Base): SQLAlchemy model class representing the table.
#         columns (list): List of columns to select.
#         limit (int): The maximum number of records to retrieve. Defaults to 1000.
#         sort_by (str, optional): The field by which to sort the results. Defaults to None.
#         group_by (str, optional): The field by which to group the results. Defaults to None.
#         random_sample (bool, optional): Whether to randomly sample the results. Defaults to False.
#         where (list, optional): A list of SQLAlchemy filter conditions or lists of conditions.

#     Returns:
#         list: A list of tuples containing the requested records.
#     """
#     logger.info("🔍 Starting to fetch records.")
#     try:
#         # Initial query setup
#         query = globals.session.query(*[getattr(model, col) for col in columns])

#         # Apply conditions if provided
#         if where:
#             conditions = build_conditions(where)
#             query = query.filter(and_(*conditions))
#             logger.debug(f"Applied conditions: {conditions}")

#         # Apply grouping if specified
#         if group_by:
#             logger.debug(f"Grouping by: {group_by}")
#             query = query.group_by(getattr(model, group_by))

#         # Apply sorting if specified
#         if sort_by:
#             logger.debug(f"Sorting by: {sort_by}")
#             query = query.order_by(getattr(model, sort_by))

#         records = []
#         if random_sample:
#             # Correctly include the same conditions in the count query
#             count_query = globals.session.query(func.count(model.id)).filter(and_(*conditions))
#             count = count_query.scalar()
#             logger.debug(f"Count of records matching conditions: {count}")

#             if count > 0:
#                 logger.debug(f"Fetching up to {limit} random records.")
#                 for _ in range(min(limit, count)):
#                     random_offset = random.randint(0, count - 1)
#                     logger.debug(f"Random offset: {random_offset}")

#                     # Log the SQL query with the offset
#                     record_query = query.offset(random_offset).limit(1)
#                     logger.debug(f"Executing query: {record_query}")
#                     record = record_query.all()

#                     logger.debug(f"Retrieved record: {record}")
#                     records.extend(record)
#             else:
#                 logger.info("No records match the random sampling criteria.")
#         else:
#             records = query.limit(limit).all()
#             logger.debug(f"Retrieved {len(records)} records without random sampling.")

#         logger.info(f"🌎📡 Retrieved {len(records)} records.")
#         return [(getattr(record, col) for col in columns) for record in records]
#     except Exception as e:
#         logger.error(f"💥🚩 Error retrieving records: {e}")
#         logger.error(f"{traceback.format_exc()}")
#         return []
#     finally:
#         logger.info("🔒 Closing session with the database.")
#         globals.session.close()

def extract_occurrence_number(link):
    """
    Extracts the occurrence number from the link if it matches the expected pattern.
    """
    match = re.search(r'https://opencorporates.com/officers/(\d+)', link)
    if match:
        return match.group(1)
    return None

def extract_event_dates(description):
    """
    Extract start and end dates from the event description.

    Args:
        description (str): The event description containing dates.

    Returns:
        Tuple[str, str]: The start and end dates extracted from the description.
    """
    dates = extract_dates(description)
    if len(dates) > 1:
        return sorted(dates)[:2]
    elif len(dates) == 1:
        return dates[0], ""
    else:
        return "", ""

def extract_dates(textstr):
    """
    Extracts all date strings from the given text.

    Args:
        text (str): The input text containing dates.

    Returns:
        list: A list of date strings found in the text.
    """
    date_pattern = r'\b(?:\d{4}[/-]\d{2}[/-]\d{2}|\d{2}[/-]\d{2}[/-]\d{4}|\d{2}[/-]\d{2}[/-]\d{2})\b'
    matches = re.findall(date_pattern, textstr)
    return matches

# def record_exists(cursor, table: str, conditions: Dict[str, str]) -> bool:
#     """
#     Check if a record exists in the table based on the given conditions.

#     Args:
#         cursor (sqlite3.Cursor): The cursor to execute the query.
#         table (str): The table name.
#         conditions (Dict[str, str]): A dictionary of conditions for the WHERE clause.

#     Returns:
#         bool: True if the record exists, False otherwise.
#     """
#     query = f"SELECT 1 FROM {table} WHERE " + " AND ".join([f"{k} = ?" for k in conditions.keys()])
#     cursor.execute(query, tuple(conditions.values()))
#     return cursor.fetchone() is not None
