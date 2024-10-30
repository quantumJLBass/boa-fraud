from typing import List, Union, Any#, Tuple, Dict
import re
import traceback
#from loguru import logger
from bs4 import BeautifulSoup, Tag
# from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, text, and_, or_ #create_engine,
# import sqlite3
# import json
# import os
import gs
from services.applogging import logger
from settings.settings import *
from utils.utils import *
# from services.scraper import *
from dbefclasses import URLCatalog#, Base  # ORM models

def catalog_cache(
    url: str,
    html_content: Union[str, BeautifulSoup, Tag],
    company_number: str = None,
    jurisdiction: str = None
) -> None:
    """
    Catalog cache data into the database and update the cache record if it exists, or create a new record if it doesn't.

    Args:
        url (str): The URL for which the HTML content is being cataloged.
        html_content (str or BeautifulSoup): The HTML content to be stored. If BeautifulSoup object, convert to string.
        company_number (str, optional): The company number associated with the URL.
        jurisdiction (str, optional): The jurisdiction associated with the URL.

    Returns:
        None
    """
    try:
        if isinstance(html_content, (BeautifulSoup, Tag)):
            html_content = str(html_content)
        elif not isinstance(html_content, str):
            logger.info(f"💥💥💥CATALOG HTML ----- Cataloging cache data for URL: {url}")
            logger.info(f"💥💥💥CATALOG HTML ----- html_content: {type(html_content)}")
            raise ValueError("html_content must be a string or BeautifulSoup object")

        with gs.read() as readsession:
            existing_record = readsession.query(URLCatalog).filter_by(url=url).first()
            if existing_record:
                logger.info(f"🔧🗃️ UPDATING HTML ----- Updating cache data for URL: {url}")
                existing_record.html_content = html_content
            else:
                logger.info(f"🔧🗃️ CATALOG HTML ----- Cataloging cache data for URL: {url}")
                new_record = URLCatalog(
                    url=url,
                    html_content=html_content,
                    company_number=company_number,
                    jurisdiction=jurisdiction,
                    completed=False
                )
                with gs.write() as sub_session:
                    sub_session.add(new_record)
                    sub_session.commit()
                    logger.info(f"🔧🗃️ HTML data saved for URL: {url}")
    except Exception as e:
        with gs.write() as writesession:
            writesession.rollback()
        logger.error(f"💥🚩Error cataloging cache data: {e}")
        logger.error(f"{traceback.format_exc()}")

def update_url_status(
    url: str,
    completed: bool = False
) -> None:
    """
    Update the status of a URL in the URLCatalog table.

    Args:
        url (str): The URL to update.
        completed (bool, optional): The new completion status. Defaults to False.

    Returns:
        None
    """
    try:
        logger.info(f"🔧🗃️ UPDATING URL STATUS ------ URL: {url}, Completed: {completed}")
        with gs.read() as readsession:
            record = readsession.query(URLCatalog).filter_by(url=url).first()
            if record:
                record.completed = completed
                with gs.write() as sub_session:
                    sub_session.commit()
                    logger.info(f"🔧🗃️ UPDATING URL STATUS ------ URL status updated: {url}")
            else:
                logger.warning(f"💥🚩URL not found for update: {url}")
    except Exception as e:
        with gs.write() as writesession:
            writesession.rollback()
            logger.error(f"💥🚩Error updating URL status: {e}")
            logger.error(f"{traceback.format_exc()}")

def check_url_exists(
    url: str
) -> bool:
    """
    Check if a URL exists in the URLCatalog table.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL exists, False otherwise.
    """
    exists = False
    try:
        with gs.read() as readsession:
            exists = readsession.query(URLCatalog).filter_by(url=url).count() > 0
    except Exception as e:
        logger.error(f"💥🚩Error checking URL existence: {e}")
        logger.error(f"{traceback.format_exc()}")
    return exists

def url_cached(
    url: str
) -> bool:
    """
    Check if a URL exists in the URLCatalog table and if its HTML content has been cached.

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL exists and html_content is not None, False otherwise.
    """
    is_cached = False
    try:
        with gs.read() as readsession:
            is_cached = readsession.query(URLCatalog).filter(
                URLCatalog.url == url,
                URLCatalog.html_content is not None
            ).count() > 0
    except Exception as e:
        logger.error(f"💥🚩Error checking URL cache status: {e}")
        logger.error(f"{traceback.format_exc()}")
    return is_cached

def load_cache(
    url: str
) -> BeautifulSoup:
    """
    Load cached HTML content for a given URL from the database.

    This function retrieves the cached HTML content for the specified URL from the URLCatalog table,
    parses it with BeautifulSoup, and returns the main content div.

    Args:
        url (str): The URL for which the HTML content is to be loaded.

    Returns:
        BeautifulSoup: A BeautifulSoup object containing the parsed HTML main content div if found,
                    otherwise None if the content is not found or an error occurs.
    """
    try:
        with gs.read() as readsession:
            existing_record = readsession.query(URLCatalog).filter_by(url=url).first()
            if existing_record and existing_record.html_content:
                logger.info(f"🔧🗃️ LOADING HTML ----- Loading cache data for URL: {url}")
                return BeautifulSoup(existing_record.html_content, 'html.parser')
            else:
                logger.error(f"💥🚩Error: No cached HTML found for URL: {url}")
                return None
    except Exception as e:
        logger.error(f"💥🚩Error loading cache html: {e}")
        logger.error(f"{traceback.format_exc()}")
        return None

def build_conditions(
    where: list
) -> List[Any]:
    """
    Builds SQLAlchemy conditions from a structured list.

    Args:
        where (list): A list of conditions with strings or lists of conditions.
                    Use '&' or no prefix for 'AND', '|' for 'OR'.

    Returns:
        list: A list of SQLAlchemy conditions.
    """
    conditions = []
    for condition in where:
        if isinstance(condition, list):
            sub_conditions = []
            for sub_condition in condition:
                if sub_condition.startswith('|'):
                    sub_conditions.append(text(sub_condition[1:]))
                else:
                    sub_conditions.append(text(sub_condition.lstrip('&')))
            conditions.append(and_(*sub_conditions))
        else:
            if condition.startswith('|'):
                conditions.append(or_(text(condition[1:])))
            else:
                conditions.append(and_(text(condition.lstrip('&'))))
    return conditions

def get_uncached_urls(
    limit: int = 1000,
    sort_by: str = None,
    group_by: str = None,
    random_sample: bool = False,
    where: list = None
) -> list:
    """
    Retrieves a list of URLs with null html_content from the URLCatalog table,
    optionally sorted, grouped, randomly sampled, and/or filtered by specified conditions.

    Args:
        limit (int): The maximum number of URLs to retrieve. Defaults to 1000.
        sort_by (str, optional): The field by which to sort the results. Defaults to None.
        group_by (str, optional): The field by which to group the results. Defaults to None.
        random_sample (bool, optional): Whether to randomly sample the results. Defaults to False.
        where (list, optional): A list of SQLAlchemy filter conditions or lists of conditions.
                                The default is 'AND', '&' for 'AND', '|' for 'OR'.

    Returns:
        list: A list of URLs with null html_content.
    """
    try:
        with gs.read() as readsession:
            query = readsession.query(
                URLCatalog.url, URLCatalog.company_number, URLCatalog.jurisdiction
            ).filter(URLCatalog.html_content is None)
            if where:
                conditions = build_conditions(where)
                query = query.filter(and_(*conditions))
            if group_by:
                query = query.group_by(getattr(URLCatalog, group_by))
            if sort_by:
                query = query.order_by(getattr(URLCatalog, sort_by))
            records = []
            if random_sample:
                count_query = readsession.query(func.count(URLCatalog.id)).filter(
                    URLCatalog.html_content is None
                )
                if where:
                    count_query = count_query.filter(and_(*conditions))
                count = count_query.scalar()
                if count > 0:
                    for _ in range(min(limit, count)):
                        random_offset = random.randint(0, count - 1)
                        record_query = query.offset(random_offset).limit(1)
                        record = record_query.all()
                        records.extend(record)
            else:
                records = query.limit(limit).all()
            return [(record.url, record.company_number, record.jurisdiction) for record in records]
    except Exception as e:
        logger.error(f"💥🚩 Error retrieving URLs with null html_content: {e}")
        logger.error(f"{traceback.format_exc()}")
        return []

def get_incomplete_urls(
    limit: int = 1000
) -> list:
    """
    Retrieves a list of URLs from the URLCatalog table where completed is marked as False.

    Args:
        limit (int): The maximum number of URLs to retrieve. Defaults to 1000.

    Returns:
        list: A list of URLs where completed is False.
    """
    try:
        with gs.read() as readsession:
            urls = readsession.query(URLCatalog.url).filter(
                URLCatalog.completed is False
            ).limit(limit).all()
            logger.info(f"🌎📡Retrieved {len(urls)} URLs with completed marked as False.")
            return [url[0] for url in urls]
    except Exception as e:
        logger.error(f"💥🚩Error retrieving URLs with completed marked as False: {e}")
        logger.error(f"{traceback.format_exc()}")
        return []

def bulk_save_urls(
    urls: List[str],
    company_number: str,
    jurisdiction: str,
    parent_id: int = None
) -> None:
    """
    Save a list of URLs with their associated company number and jurisdiction to the URLCatalog.

    Args:
        urls (List[str]): List of URLs to save.
        company_number (str): The associated company number.
        jurisdiction (str): The associated jurisdiction.
        parent_id (int, optional): The ID of the parent URL if applicable. Defaults to None.

    Returns:
        None
    """
    try:
        logger.info(f"🔧🗃️ BULK SAVING URLS ------ Saving {len(urls)} URLs.")
        new_url_records = []
        with gs.read() as readsession:
            for url in urls:
            # Check if the URL already exists
                if not readsession.query(URLCatalog).filter_by(url=url).first():
                    new_url_records.append(URLCatalog(
                        url=url,
                        company_number=company_number,
                        jurisdiction=jurisdiction,
                        completed=False,
                        parent_id=parent_id
                    ))

        # Bulk save new records if there are any
        if new_url_records:
            with gs.write() as writesession:
                writesession.bulk_save_objects(new_url_records)
                writesession.commit()
                logger.info(f"🔧🗃️ BULK SAVING URLS ------ Successfully saved {len(new_url_records)} URLs.")
        else:
            logger.info("🔧🗃️ BULK SAVING URLS ------ No new URLs to save.")
    except Exception as e:
        with gs.write() as writesession:
            writesession.rollback()
            logger.error(f"💥🚩Error bulk saving URLs: {e}")
            logger.error(f"{traceback.format_exc()}")

def get_base_url_id(
    company_number: str,
    jurisdiction: str = None
) -> int:
    """
    Retrieve the ID of the base URL for a given company number and optional jurisdiction.

    Args:
        company_number (str): The company number to filter by.
        jurisdiction (str, optional): The jurisdiction to filter by. Defaults to None.

    Returns:
        int: The ID of the base URL if found, otherwise None.
    """
    try:
        # Pattern to match base URLs with exactly 5 slashes
        base_url_pattern = r'^https:\/\/opencorporates\.com\/companies\/[^\/]+\/[^\/]+$'
        with gs.read() as readsession:
            # Build initial query
            query = readsession.query(URLCatalog).filter(
                URLCatalog.company_number == company_number
            )

            # Optionally filter by jurisdiction if provided
            if jurisdiction:
                query = query.filter(URLCatalog.jurisdiction == jurisdiction)

            # Fetch all matching records and filter by URL pattern in Python
            base_url_records = query.all()
            for record in base_url_records:
                if re.match(base_url_pattern, record.url):
                    return record.id

        return None
    except Exception as e:
        logger.error(f"Error fetching base URL ID: {e}")
        logger.error(f"{traceback.format_exc()}")
        return None


