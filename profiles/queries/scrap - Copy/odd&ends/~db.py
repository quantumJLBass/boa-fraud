from applogging import *
from settings import *
from utils import *
from scraper import *
from typing import List, Dict, Union, Tuple
import gs
from loguru import logger
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
import sqlite3
import json
import os
import re
from typing import Dict, Any

DB_FILE = 'cache.db'

def initialize_db():
    """
    Initialize the SQLite database and create the necessary tables.
    """
    logger.info(f"{i()}🔧📄 Initializing the database and creating tables.")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        logger.info(f"{i()}🛠️ Creating table 'companies'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                company_number TEXT PRIMARY KEY,
                company_name TEXT,
                status TEXT,
                incorporation_date TEXT,
                company_type TEXT,
                jurisdiction TEXT,
                registered_address TEXT,
                agent_name TEXT,
                agent_address TEXT,
                parent_company_name TEXT,
                parent_company_url TEXT
            )
        ''')
        logger.info(f"{i()}✅ 'companies' table created.")

        logger.info(f"{i()}🛠️ Creating table 'attributes'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attributes (
                id INTEGER PRIMARY KEY,
                company_number TEXT,
                name TEXT,
                value TEXT,
                FOREIGN KEY(company_number) REFERENCES companies(company_number)
            )
        ''')
        logger.info(f"{i()}✅ 'attributes' table created.")

        logger.info(f"{i()}🛠️ Creating table 'officers'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS officers (
                id INTEGER PRIMARY KEY,
                company_number TEXT,
                occurrence_number TEXT,
                name TEXT,
                role TEXT,
                status TEXT,
                link TEXT,
                address TEXT,
                start_date TEXT,
                end_date TEXT,
                type TEXT,
                FOREIGN KEY(company_number) REFERENCES companies(company_number)
            )
        ''')
        logger.info(f"{i()}✅ 'officers' table created.")

        logger.info(f"{i()}🛠️ Creating table 'events'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                company_number TEXT,
                start_date TEXT,
                end_date TEXT,
                description TEXT,
                link TEXT,
                FOREIGN KEY(company_number) REFERENCES companies(company_number)
            )
        ''')
        logger.info(f"{i()}✅ 'events' table created.")

        logger.info(f"{i()}🛠️ Creating table 'assertions'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assertions (
                id INTEGER PRIMARY KEY,
                company_number TEXT,
                title TEXT,
                description TEXT,
                link TEXT,
                FOREIGN KEY(company_number) REFERENCES companies(company_number)
            )
        ''')
        logger.info(f"{i()}✅ 'assertions' table created.")

        logger.info(f"{i()}🛠️ Creating table 'filings'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS filings (
                id INTEGER PRIMARY KEY,
                company_number TEXT,
                date TEXT,
                description TEXT,
                link TEXT,
                FOREIGN KEY(company_number) REFERENCES companies(company_number)
            )
        ''')
        logger.info(f"{i()}✅ 'filings' table created.")

        logger.info(f"{i()}🛠️ Creating table 'branch_relationships'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS branch_relationships (
                id INTEGER PRIMARY KEY,
                company_number TEXT,
                branch_company TEXT,
                branch_company_id TEXT,
                jurisdiction TEXT,
                status TEXT,
                type TEXT,
                link TEXT,
                start_date TEXT,
                end_date TEXT,
                statement_link TEXT,
                FOREIGN KEY(company_number) REFERENCES companies(company_number)
            )
        ''')
        logger.info(f"{i()}✅ 'branch_relationships' table created.")

        logger.info(f"{i()}🛠️ Creating table 'links'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY,
                company_number TEXT,
                link TEXT,
                FOREIGN KEY(company_number) REFERENCES companies(company_number)
            )
        ''')
        logger.info(f"{i()}✅ 'links' table created.")

        logger.info(f"{i()}🛠️ Creating table 'cache_index'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_index (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                completed BOOLEAN
            )
        ''')
        logger.info(f"{i()}✅ 'cache_index' table created.")

        logger.info(f"{i()}🛠️ Creating table 'sub_urls'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sub_urls (
                id INTEGER PRIMARY KEY,
                cached_url_id INTEGER,
                sub_url TEXT,
                completed BOOLEAN,
                FOREIGN KEY(cached_url_id) REFERENCES cache_index(id)
            )
        ''')
        logger.info(f"{i()}✅ 'sub_urls' table created.")

        logger.info(f"{i()}🛠️ Creating table 'officer_urls'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS officer_urls (
                id INTEGER PRIMARY KEY,
                cached_url_id INTEGER,
                officer_url TEXT,
                completed BOOLEAN,
                FOREIGN KEY(cached_url_id) REFERENCES cache_index(id)
            )
        ''')
        logger.info(f"{i()}✅ 'officer_urls' table created.")

        logger.info(f"{i()}🛠️ Creating table 'cache'.")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                id INTEGER PRIMARY KEY,
                url TEXT UNIQUE,
                html_content TEXT
            )
        ''')
        logger.info(f"{i()}✅ 'cache' table created.")

    logger.info(f"{i()}✅ Database initialized and tables created successfully.")

def record_exists(cursor, table: str, conditions: Dict[str, str]) -> bool:
    """
    Check if a record exists in the table based on the given conditions.

    Args:
        cursor (sqlite3.Cursor): The cursor to execute the query.
        table (str): The table name.
        conditions (Dict[str, str]): A dictionary of conditions for the WHERE clause.

    Returns:
        bool: True if the record exists, False otherwise.
    """
    query = f"SELECT 1 FROM {table} WHERE " + " AND ".join([f"{k} = ?" for k in conditions.keys()])
    cursor.execute(query, tuple(conditions.values()))
    return cursor.fetchone() is not None

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

def extract_dates(text):
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

def catalog_company(company_number, data):
    """
    Insert or update company data in the database.
    """
    logger.info(f"{i()}🔧🏢 Inserting or updating company data for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        conditions = {'company_number': company_number}
        if record_exists(cursor, 'companies', conditions):
            existing_record = cursor.fetchone()
            if existing_record:
                existing_data_size = sum(len(str(field)) for field in existing_record)
                new_data_size = sum(len(str(field)) for field in data.values())

                if new_data_size > existing_data_size:
                    cursor.execute('''
                        UPDATE companies SET company_name = ?, status = ?, incorporation_date = ?, company_type = ?, 
                        jurisdiction = ?, registered_address = ?, agent_name = ?, agent_address = ?, 
                        parent_company_name = ?, parent_company_url = ?
                        WHERE company_number = ?
                    ''', (
                        data.get('Company Name', 'Unknown'), data.get('Attributes', {}).get('Status', 'Unknown'), 
                        data.get('Attributes', {}).get('Incorporation Date', 'Unknown'), data.get('Attributes', {}).get('Company Type', 'Unknown'), 
                        data.get('Attributes', {}).get('Jurisdiction', 'Unknown'), data.get('Attributes', {}).get('Registered Address', 'Unknown'),
                        data.get('Attributes', {}).get('Inactive Directors / Officers', 'Unknown'), '', '', '', company_number
                    ))
                    logger.info(f"{i()}✅ Company data updated for company number: {company_number}")
        else:
            cursor.execute('''
                INSERT INTO companies (company_number, company_name, status, incorporation_date, company_type, jurisdiction, registered_address, agent_name, agent_address, parent_company_name, parent_company_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_number, data.get('Company Name', 'Unknown'), data.get('Attributes', {}).get('Status', 'Unknown'), 
                data.get('Attributes', {}).get('Incorporation Date', 'Unknown'), data.get('Attributes', {}).get('Company Type', 'Unknown'), 
                data.get('Attributes', {}).get('Jurisdiction', 'Unknown'), data.get('Attributes', {}).get('Registered Address', 'Unknown'),
                data.get('Attributes', {}).get('Inactive Directors / Officers', 'Unknown'), '', '', ''
            ))
            logger.info(f"{i()}✅ Company data inserted for company number: {company_number}")

        conn.commit()

def update_company(company_number, data):
    """
    Update company data in the database.
    """
    logger.info(f"{i()}🔧🏢 Updating company data for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE companies
            SET company_name = ?, status = ?, incorporation_date = ?, company_type = ?, jurisdiction = ?, 
                registered_address = ?, agent_name = ?, agent_address = ?, parent_company_name = ?, parent_company_url = ?
            WHERE company_number = ?
        ''', (
            data.get('Company Name', 'Unknown'), data.get('Attributes', {}).get('Status', 'Unknown'), 
            data.get('Attributes', {}).get('Incorporation Date', 'Unknown'), data.get('Attributes', {}).get('Company Type', 'Unknown'), 
            data.get('Attributes', {}).get('Jurisdiction', 'Unknown'), data.get('Attributes', {}).get('Registered Address', 'Unknown'),
            data.get('Attributes', {}).get('Inactive Directors / Officers', 'Unknown'), '', '', '', company_number
        ))
        conn.commit()
    logger.info(f"{i()}✅ Company data updated for company number: {company_number}")

def delete_company(company_number):
    """
    Delete company data from the database.
    """
    logger.info(f"{i()}🔧🏢 Deleting company data for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM companies WHERE company_number = ?', (company_number,))
        conn.commit()
    logger.info(f"{i()}✅ Company data deleted for company number: {company_number}")

def catalog_attribute(company_number, key, value):
    """
    Catalog a company's attribute in the database.
    """
    # Convert the value to a string if it's a dictionary
    if isinstance(value, dict):
        value = json.dumps(value)

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        conditions = {'company_number': company_number, 'name': key}
        cursor.execute('''
            SELECT value FROM attributes WHERE company_number = ? AND name = ?
        ''', (company_number, key))
        existing_value = cursor.fetchone()
        
        if existing_value:
            cursor.execute('''
                UPDATE attributes SET value = ? WHERE company_number = ? AND name = ?
            ''', (value, company_number, key))
            logger.info(f"{i()}✅ Attribute '{key}' updated for company number: {company_number}")
        else:
            cursor.execute('''
                INSERT INTO attributes (company_number, name, value)
                VALUES (?, ?, ?)
            ''', (company_number, key, value))
            logger.info(f"{i()}✅ Attribute '{key}' inserted for company number: {company_number}")

def update_attribute(company_number, key, value):
    """
    Update an attribute for a company in the database.
    """
    logger.info(f"{i()}🔧📄 Updating attribute '{key}' for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE attributes
            SET value = ?
            WHERE company_number = ? AND name = ?
        ''', (value, company_number, key))
        conn.commit()
    logger.info(f"{i()}✅ Attribute '{key}' updated for company number: {company_number}")

def delete_attribute(company_number, key):
    """
    Delete an attribute for a company from the database.
    """
    logger.info(f"{i()}🔧📄 Deleting attribute '{key}' for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM attributes WHERE company_number = ? AND name = ?', (company_number, key))
        conn.commit()
    logger.info(f"{i()}✅ Attribute '{key}' deleted for company number: {company_number}")

def catalog_officer(company_number, officer):
    """
    Insert or update an officer for a company in the database.
    """
    logger.info(f"{i()}🔧👔 Inserting or updating officer '{officer['Name']}' for company number: {company_number}")
    
    occurrence_number = officer.get('Occurrence Number')
    if not occurrence_number:
        occurrence_number = extract_occurrence_number(officer.get('Link', '#'))
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        conditions = {'company_number': company_number, 'name': officer['Name']}
        if record_exists(cursor, 'officers', conditions):
            existing_record = cursor.fetchone()
            if existing_record:
                existing_data_size = sum(len(str(field)) for field in existing_record)
                new_data_size = sum(len(str(field)) for field in officer.values())

                if new_data_size > existing_data_size:
                    cursor.execute('''
                        UPDATE officers SET role = ?, status = ?, link = ?, address = ?, start_date = ?, end_date = ?, type = ?, occurrence_number = ?
                        WHERE company_number = ? AND name = ?
                    ''', (
                        officer['Role'], officer.get('Status', 'Unknown'), officer.get('Link', '#'), officer.get('Address', 'Unknown'),
                        officer.get('Start_Date', 'Unknown'), officer.get('End_Date', 'Unknown'), officer.get('Type', 'Unknown'), occurrence_number,
                        company_number, officer['Name']
                    ))
                    logger.info(f"{i()}✅ Officer '{officer['Name']}' updated for company number: {company_number}")
        else:
            cursor.execute('''
                INSERT INTO officers (company_number, name, role, status, link, address, start_date, end_date, type, occurrence_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_number, officer.get('Name', 'Unknown'), officer.get('Role', 'Unknown'), officer.get('Status', 'Unknown'), officer.get('Link', '#'),
                officer.get('Address', 'Unknown'), officer.get('Start_Date', 'Unknown'), officer.get('End_Date', 'Unknown'), officer.get('Type', 'Unknown'),
                occurrence_number
            ))
            logger.info(f"{i()}✅ Officer '{officer.get('Name', 'Unknown')}' inserted for company number: {company_number}")

        conn.commit()

def update_officer(company_number, officer):
    """
    Update an officer for a company in the database.
    """
    logger.info(f"{i()}🔧👔 Updating officer '{officer['Name']}' for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE officers
            SET role = ?, status = ?, link = ?, address = ?, start_date = ?, end_date = ?, type = ?
            WHERE company_number = ? AND name = ?
        ''', (
            officer.get('Role', 'Unknown'), officer.get('Status', 'Unknown'), officer.get('Link', '#'), officer.get('Address', 'Unknown'),
            officer.get('Start Date', 'Unknown'), officer.get('End Date', 'Unknown'), officer.get('Type', 'Unknown'), company_number, officer['Name']
        ))
        conn.commit()
    logger.info(f"{i()}✅ Officer '{officer['Name']}' updated for company number: {company_number}")

def delete_officer(company_number, officer_name):
    """
    Delete an officer for a company from the database.
    """
    logger.info(f"{i()}🔧👔 Deleting officer '{officer_name}' for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM officers WHERE company_number = ? AND name = ?', (company_number, officer_name))
        conn.commit()
    logger.info(f"{i()}✅ Officer '{officer_name}' deleted for company number: {company_number}")

def catalog_event(company_number, event):
    """
    Insert or update an event for a company in the database.
    """
    logger.info(f"{i()}🔧📅 Inserting or updating event for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        start_date = event.get('start_date', '')
        end_date = event.get('end_date', '')

        # Only extract event dates if start_date and end_date are not present in the event object
        if not start_date and not end_date:
            start_date, end_date = extract_event_dates(event.get('Description', ''))

        conditions = {'company_number': company_number, 'description': event.get('Description', '')}
        if record_exists(cursor, 'events', conditions):
            existing_record = cursor.fetchone()
            if existing_record:
                if (len(start_date) > len(existing_record[2]) or len(end_date) > len(existing_record[3])):
                    cursor.execute('''
                        UPDATE events SET start_date = ?, end_date = ?, link = ?
                        WHERE company_number = ? AND description = ?
                    ''', (
                        start_date, end_date, event.get('Link', '#'), company_number, event.get('Description', '')
                    ))
                    logger.info(f"{i()}✅ Event updated for company number: {company_number}")
        else:
            cursor.execute('''
                INSERT INTO events (company_number, start_date, end_date, description, link)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                company_number, start_date, end_date, event.get('Description', 'Unknown'), event.get('Link', '#')
            ))
            logger.info(f"{i()}✅ Event inserted for company number: {company_number}")

        conn.commit()

def update_event(event_id, event):
    """
    Update an event for a company in the database.
    """
    logger.info(f"{i()}🔧📅 Updating event for event ID: {event_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        start_date, end_date = extract_event_dates(event.get('Description', ''))
        cursor.execute('''
            UPDATE events
            SET start_date = ?, end_date = ?, description = ?, link = ?
            WHERE id = ?
        ''', (
            start_date, end_date, event.get('Description', 'Unknown'), event.get('Link', '#'), event_id
        ))
        conn.commit()
    logger.info(f"{i()}✅ Event updated for event ID: {event_id}")

def delete_event(event_id):
    """
    Delete an event for a company from the database.
    """
    logger.info(f"{i()}🔧📅 Deleting event for event ID: {event_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
        conn.commit()
    logger.info(f"{i()}✅ Event deleted for event ID: {event_id}")

def catalog_assertion(company_number, assertion):
    """
    Insert or update an assertion for a company in the database.
    """
    logger.info(f"{i()}🔧📄 Inserting or updating assertion '{assertion.get('Title', 'Unknown')}' for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        conditions = {'company_number': company_number, 'title': assertion.get('Title', '')}
        if record_exists(cursor, 'assertions', conditions):
            existing_record = cursor.fetchone()
            if existing_record:
                if len(assertion['Description']) > len(existing_record[3]):
                    cursor.execute('''
                        UPDATE assertions SET description = ?, link = ?
                        WHERE company_number = ? AND title = ?
                    ''', (assertion['Description'], assertion.get('Link', ''), company_number, assertion['Title']))
                    logger.info(f"{i()}✅ Assertion '{assertion['Title']}' updated for company number: {company_number}")
        else:
            cursor.execute('''
                INSERT INTO assertions (company_number, title, description, link)
                VALUES (?, ?, ?, ?)
            ''', (company_number, assertion['Title'], assertion['Description'], assertion.get('Link', '')))
            logger.info(f"{i()}✅ Assertion '{assertion['Title']}' inserted for company number: {company_number}")

        conn.commit()

def insert_assertion(company_number, assertion):
    """
    Insert an assertion for a company into the database.
    """
    logger.info(f"{i()}🔧📄 Inserting assertion '{assertion.get('Title', 'Unknown')}' for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assertions (company_number, title, description)
            VALUES (?, ?, ?)
        ''', (
            company_number, assertion.get('Title', 'Unknown'), assertion.get('Description', 'Unknown')
        ))
        conn.commit()
    logger.info(f"{i()}✅ Assertion '{assertion.get('Title', 'Unknown')}' inserted for company number: {company_number}")

def update_assertion(assertion_id, assertion):
    """
    Update an assertion for a company in the database.
    """
    logger.info(f"{i()}🔧📄 Updating assertion for assertion ID: {assertion_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE assertions
            SET title = ?, description = ?
            WHERE id = ?
        ''', (
            assertion.get('Title', 'Unknown'), assertion.get('Description', 'Unknown'), assertion_id
        ))
        conn.commit()
    logger.info(f"{i()}✅ Assertion updated for assertion ID: {assertion_id}")

def delete_assertion(assertion_id):
    """
    Delete an assertion for a company from the database.
    """
    logger.info(f"{i()}🔧📄 Deleting assertion for assertion ID: {assertion_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM assertions WHERE id = ?', (assertion_id,))
        conn.commit()
    logger.info(f"{i()}✅ Assertion deleted for assertion ID: {assertion_id}")

def catalog_filing(company_number, filing):
    """
    Insert or update a filing for a company in the database.
    """
    logger.info(f"{i()}🔧📄 Inserting or updating filing for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        conditions = {'company_number': company_number, 'date': filing['Date'], 'description': filing['Description']}
        if record_exists(cursor, 'filings', conditions):
            existing_record = cursor.fetchone()
            if existing_record and existing_record[4]:
                if len(filing.get('Link', '')) > len(existing_record[4]):
                    cursor.execute('''
                        UPDATE filings SET link = ?
                        WHERE company_number = ? AND date = ? AND description = ?
                    ''', (filing.get('Link', ''), company_number, filing['Date'], filing['Description']))
                    logger.info(f"{i()}✅ Filing updated for company number: {company_number}")
        else:
            cursor.execute('''
                INSERT INTO filings (company_number, date, description, link)
                VALUES (?, ?, ?, ?)
            ''', (company_number, filing['Date'], filing['Description'], filing.get('Link', '')))
            logger.info(f"{i()}✅ Filing inserted for company number: {company_number}")

        conn.commit()

def insert_filing(company_number, filing):
    """
    Insert a filing for a company into the database.
    """
    logger.info(f"{i()}🔧📄 Inserting filing for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO filings (company_number, date, description, link)
            VALUES (?, ?, ?, ?)
        ''', (
            company_number, filing.get('Date', 'Unknown'), filing.get('Description', 'Unknown'), filing.get('Link', '#')
        ))
        conn.commit()
    logger.info(f"{i()}✅ Filing inserted for company number: {company_number}")

def update_filing(filing_id, filing):
    """
    Update a filing for a company in the database.
    """
    logger.info(f"{i()}🔧📄 Updating filing for filing ID: {filing_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE filings
            SET date = ?, description = ?, link = ?
            WHERE id = ?
        ''', (
            filing.get('Date', 'Unknown'), filing.get('Description', 'Unknown'), filing.get('Link', '#'), filing_id
        ))
        conn.commit()
    logger.info(f"{i()}✅ Filing updated for filing ID: {filing_id}")

def delete_filing(filing_id):
    """
    Delete a filing for a company from the database.
    """
    logger.info(f"{i()}🔧📄 Deleting filing for filing ID: {filing_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM filings WHERE id = ?', (filing_id,))
        conn.commit()
    logger.info(f"{i()}✅ Filing deleted for filing ID: {filing_id}")

def catalog_branch_relationship(company_number, branch):
    """
    Insert or update a branch relationship for a company in the database.
    """
    logger.info(f"{i()}🔧🏢 Inserting or updating branch relationship for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        conditions = {'company_number': company_number, 'branch_company': branch['Company']}
        if record_exists(cursor, 'branch_relationships', conditions):
            existing_record = cursor.fetchone()
            if existing_record:
                existing_data_size = sum(len(str(field)) for field in existing_record)
                new_data_size = sum(len(str(field)) for field in branch.values())

                if new_data_size > existing_data_size:
                    cursor.execute('''
                        UPDATE branch_relationships SET branch_company_id = ?, jurisdiction = ?, status = ?, type = ?, link = ?, start_date = ?, end_date = ?, statement_link = ?
                        WHERE company_number = ? AND branch_company = ?
                    ''', (
                        branch.get('Company ID', 'Unknown'), branch.get('Jurisdiction', 'Unknown'), branch.get('Status', 'Unknown'), branch.get('Type', 'Unknown'), 
                        branch.get('Link', '#'), branch.get('Start Date', 'Unknown'), branch.get('End Date', 'Unknown'), branch.get('statement_link', '#'),
                        company_number, branch['Company']
                    ))
                    logger.info(f"{i()}✅ Branch relationship updated for company number: {company_number}")
        else:
            cursor.execute('''
                INSERT INTO branch_relationships (company_number, branch_company, branch_company_id, jurisdiction, status, type, link, start_date, end_date, statement_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_number, branch.get('Company', 'Unknown'), branch.get('Company ID', 'Unknown'), branch.get('Jurisdiction', 'Unknown'), 
                branch.get('Status', 'Unknown'), branch.get('Type', 'Unknown'), branch.get('Link', '#'), branch.get('Start Date', 'Unknown'), 
                branch.get('End Date', 'Unknown'), branch.get('statement_link', '#')
            ))
            logger.info(f"{i()}✅ Branch relationship inserted for company number: {company_number}")

        conn.commit()

def insert_branch_relationship(company_number, branch):
    """
    Insert a branch relationship for a company into the database.
    """
    logger.info(f"{i()}🔧🏢 Inserting branch relationship for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO branch_relationships (company_number, branch_company, branch_company_id, jurisdiction, status, type, link, start_date, end_date, statement_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            company_number, branch.get('Company', 'Unknown'), branch.get('Company ID', 'Unknown'), branch.get('Jurisdiction', 'Unknown'),
            branch.get('Status', 'Unknown'), branch.get('Type', 'Unknown'), branch.get('Link', '#'), branch.get('Start Date', 'Unknown'),
            branch.get('End Date', 'Unknown'), branch.get('statement_link', '#')
        ))
        conn.commit()
    logger.info(f"{i()}✅ Branch relationship inserted for company number: {company_number}")

def update_branch_relationship(branch_id, branch):
    """
    Update a branch relationship for a company in the database.
    """
    logger.info(f"{i()}🔧🏢 Updating branch relationship for branch ID: {branch_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE branch_relationships
            SET branch_company = ?, branch_company_id = ?, jurisdiction = ?, status = ?, type = ?, link = ?, start_date = ?, end_date = ?, statement_link = ?
            WHERE id = ?
        ''', (
            branch.get('Company', 'Unknown'), branch.get('Company ID', 'Unknown'), branch.get('Jurisdiction', 'Unknown'),
            branch.get('Status', 'Unknown'), branch.get('Type', 'Unknown'), branch.get('Link', '#'), branch.get('Start Date', 'Unknown'),
            branch.get('End Date', 'Unknown'), branch.get('statement_link', '#'), branch_id
        ))
        conn.commit()
    logger.info(f"{i()}✅ Branch relationship updated for branch ID: {branch_id}")

def delete_branch_relationship(branch_id):
    """
    Delete a branch relationship for a company from the database.
    """
    logger.info(f"{i()}🔧🏢 Deleting branch relationship for branch ID: {branch_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM branch_relationships WHERE id = ?', (branch_id,))
        conn.commit()
    logger.info(f"{i()}✅ Branch relationship deleted for branch ID: {branch_id}")

def catalog_link(company_number, link):
    """
    Insert or update a link for a company in the database.
    """
    logger.info(f"{i()}🔧🔗 Inserting or updating link for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()

        conditions = {'company_number': company_number, 'link': link}
        if record_exists(cursor, 'links', conditions):
            existing_record = cursor.fetchone()
            if existing_record:
                if len(link) > len(existing_record[2]):
                    cursor.execute('''
                        UPDATE links SET link = ?
                        WHERE company_number = ? AND link = ?
                    ''', (link, company_number, link))
                    logger.info(f"{i()}✅ Link updated for company number: {company_number}")
        else:
            cursor.execute('''
                INSERT INTO links (company_number, link)
                VALUES (?, ?)
            ''', (
                company_number, link
            ))
            logger.info(f"{i()}✅ Link inserted for company number: {company_number}")

        conn.commit()

def insert_link(company_number, link):
    """
    Insert a link for a company into the database.
    """
    logger.info(f"{i()}🔧🔗 Inserting link for company number: {company_number}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO links (company_number, link)
            VALUES (?, ?)
        ''', (
            company_number, link
        ))
        conn.commit()
    logger.info(f"{i()}✅ Link inserted for company number: {company_number}")

def update_link(link_id, link):
    """
    Update a link for a company in the database.
    """
    logger.info(f"{i()}🔧🔗 Updating link for link ID: {link_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE links
            SET link = ?
            WHERE id = ?
        ''', (
            link, link_id
        ))
        conn.commit()
    logger.info(f"{i()}✅ Link updated for link ID: {link_id}")

def delete_link(link_id):
    """
    Delete a link for a company from the database.
    """
    logger.info(f"{i()}🔧🔗 Deleting link for link ID: {link_id}")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM links WHERE id = ?', (link_id,))
        conn.commit()
    logger.info(f"{i()}✅ Link deleted for link ID: {link_id}")

def load_data_from_json(file_path):
    """
    Load company data from a JSON file and catalog the data into the database.
    """
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # Loop over each company in the data
    for company_url, company_data in data.items():
        if 'Attributes' in company_data:
            company_number = company_data['Attributes']['Company Number']
            catalog_company(company_number, company_data)
            
            # Insert attributes
            attributes = company_data.get('Attributes', {})
            for key, value in attributes.items():
                catalog_attribute(company_number, key, value)
            
            # Insert officers
            officers = company_data.get('Officers', [])
            for officer in officers:
                catalog_officer(company_number, officer)
            
            # Insert events
            events = company_data.get('Events', [])
            for event in events:
                catalog_event(company_number, event)
            
            # Insert filings
            filings = company_data.get('Filings', [])
            for filing in filings:
                catalog_filing(company_number, filing)
            
            # Insert assertions
            assertions = company_data.get('Assertions', {})
            for assertion_type, assertion_list in assertions.items():
                for assertion in assertion_list:
                    catalog_assertion(company_number, assertion)
            
            # Insert branch relationships
            branches = company_data.get('Branch Relationships', [])
            for branch in branches:
                catalog_branch_relationship(company_number, branch)
        else:
            logger.warning(f"{i()}⚠️ No 'Attributes' key found for company URL: {company_url}")

def load_json_folder(folder_path):
    """
    Load all JSON files in a specified folder and catalog their data.
    """
    try:
        for filename in os.listdir(folder_path):
            if filename.endswith('.json'):
                file_path = os.path.join(folder_path, filename)
                logger.info(f"{i()}🔧🗃️ Loading JSON file: {file_path}")
                try:
                    load_data_from_json(file_path)
                except KeyError as e:
                    logger.error(f"{i()}❌ Error loading JSON file {file_path}: {str(e)}")
                except Exception as e:
                    logger.error(f"{i()}❌ Unexpected error loading JSON file {file_path}: {str(e)}")
    finally:
        logger.info(f"{i()}✅ JSON files loaded successfully from folder: {folder_path}")
        section(f"ENDING LOADING OF THE DATABASE ----- bye bye 👋", "blue1", "center")
