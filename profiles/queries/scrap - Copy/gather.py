# gather.py
import multiprocessing
import time
import traceback
from contextlib import contextmanager

from rich.console import Console
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# from sqlalchemy.exc import IntegrityError
from typer import Typer

import gs
from db import *
from db.dbefclasses import URLCatalog
from gui.main import MainWindow
from services.applogging import logger
from services.scraper import scrape_data
from services.signal_handler import check_and_terminate, setup_signal_handling
from services.url_handlers import (
    warm_cache,  # , extract_jurisdiction_from_url, extract_company_number_from_url
)
from services.webdriver import exiting, get_current_ip, opening
from settings import *
from utils.function_utils import sig_listener
from utils.useollama import *

app = Typer()
gs.console = Console()


def create_session_manager(db_file):
    """
    Creates a session manager for the given database file.

    Args:
        db_file (str): The path to the database file.

    Returns:
        callable: A context manager that provides a session for interacting with the database.
            The session is automatically committed on successful execution and rolled back
            on exception.
    """
    engine = create_engine(f"sqlite:///{db_file}")
    sessionlocal = sessionmaker(bind=engine)

    @contextmanager
    def get_session():
        session = sessionlocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return get_session


def connect_db_read():
    """
    Connects to the database file specified by DB_FILE for read operations.
    Initializes a session manager for the database, and stores it in gs.read.
    If the session manager initialization fails, logs an error message.
    """
    DB_FILE = "db/cache-write.db"
    try:
        gs.read = create_session_manager(DB_FILE)
    except Exception as e:
        logger.error(f"💥🚩 Error initializing read session for {DB_FILE}: {e}")


def connect_db_write():
    """
    Connects to the database file specified by DB_FILE for write operations.
    Initializes a session manager for the database, and stores it in gs.write.
    If the session manager initialization fails, logs an error message.
    """
    DB_FILE = "db/cache-write.db"
    try:
        gs.write = create_session_manager(DB_FILE)
    except Exception as e:
        logger.error(f"💥🚩 Error initializing write session for {DB_FILE}: {e}")


def sig_check(target_func):
    """
    Wraps a function to check for termination signals before and after execution.

    Args:
        func (callable): The function to be wrapped.

    Returns:
        callable: The wrapped function with signal checking.
    """

    def wrapper(*args, **kwargs):
        logger.debug(f"{i()}🔄 Calling wrapped function: {target_func.__name__}")
        check_and_terminate()  # Check before execution
        result = target_func(*args, **kwargs)
        check_and_terminate()  # Check after execution
        logger.debug(f"{i()}🔄 Function {target_func.__name__} completed.")
        return result

    return wrapper


@sig_listener
def initialize():
    """
    Initializes the application by setting up signal handling,
    getting the initial IP address, connecting to the databases,
    and displaying a section message.

    This function does not take any parameters.

    This function does not return anything.
    """
    # print("initialize...")
    setup_signal_handling()
    gs.initial_ip = get_current_ip()
    # logger = logging.getLogger('app')
    logger.info(f"{i()}Initial IP: {gs.initial_ip}")
    connect_db_write()
    connect_db_read()
    section(
        f"{i()}hello, I'm starting the scraper 🕵️‍♂️. let's go!!! 🚀",
        "dark_sea_green4",
        "center",
    )

    # Start the Typer app, wrapped in the sig_check to ensure it handles termination globally
    logger.info(f"{i()}🚀 Starting the Typer app with signal checks.")
    app()
    # sig_check(app)()  # Wrapping the entire Typer app to check for termination signals


@app.command()
def main():
    """
    Executes the main logic of the program.

    This function initializes the necessary variables, sets up the VPN which upon success logins into the website
    at which point it then enters a loop to iterate over the `urls` list and scrape the data.
    For every 5th iteration, it switches the VPN and WebDriver by calling the `switch_vpn_and_driver` function.

    Inside the loop, it performs the following steps:
    - Retrieves the current URL from the `urls` list.
    - Sends the WebDriver to the current URL.
    - Scrapes the data from the current URL using the `scrape_data` function.
    - Saves the scraped data using the `save_data_intermediate` function.
    - Logs the scraped data.
    - Performs a random wait of between 10 and 30 seconds.

    After the loop, it closes the WebDriver and terminates the VPN process.

    Parameters:
    - None

    Returns:
    - None
    """

    try:
        while True:
            # on each loop of 20 urls we will close the old vpn, and open a new one
            gathering_urls = URLCatalog.fetch(
                limit=20,
                where=" completed = FALSE AND (html_content IS NOT NULL AND html_content != '' AND url LIKE 'https://opencorporates.com/companies/%/%' AND LENGTH(url) - LENGTH(REPLACE(url, '/', '')) = 5) AND NOT EXISTS ( SELECT 1 FROM companies c WHERE c.company_number = url_catalog.company_number )",
            )
            logger.info(f"{i()}🧺 Gathering URLs: {gathering_urls}")

            if not gathering_urls:
                logger.info(f"{i()}📜🏁🚩✅ All URLs have been processed.")
                break

            opening()  # should we really mess with the vpn here?
            k = 1
            for gathering in gathering_urls:
                # Check for termination signal within the loop
                check_and_terminate()

                gs.console.rule()
                gs.console.rule(f"{k}")
                k += 1

                gs.current_url = gathering[1]
                gs.current_company_number = gathering[2]
                gs.current_jurisdiction = gathering[3]

                section(f"⌛⛏️⛏️ Working on {gs.current_url}", "sky_blue1", "right")

                company_data = scrape_data()
                if company_data:
                    # save_data_intermediate({url: company_data})
                    # should the saved in the db by now and we are not saving to json anymore
                    # the note creation is what happens next
                    # note_the_data(gs.current_url)
                    logger.info(f"{i()}✍️✍️⛏️ Scrapped URL data: {company_data}")
                    # mark_url_as_processed(url)
                else:
                    logger.warning(
                        f"{i()}🛑🚨🚩 Scrapping URL data failed. Main content not found for URL {gs.current_url}"
                    )

                rando = random.uniform(1, 5)
                logger.info(
                    f"{i()} ✅ just a breathe for {rando}time, we are done with {gs.current_url}"
                )
                gs.console.rule()
                time.sleep(rando)
                gs.console.rule()
                gs.console.rule()
                gs.console.rule()
            exiting()  # should we really mess with the vpn here?

        logger.info(
            f"{i()} ✅ Scrapping URL data ----- Data successfully saved to company_data.json"
        )
    finally:
        exiting()
        shutdown_logger()
        section("ENDING SCRAPPING ----- bye bye 👋", "blue1", "center")


@app.command()
def warm():
    """
    Pre-warms the cache by fetching and caching the SOAP objects for all URLs.

    This command initializes the WebDriver, pre-warms the cache, and then exits.

    Parameters:
    - None

    Returns:
    - None
    """

    section("⛏️🖨️ WARMING THE CACHE 🖨️⛏️", "sea_green2", "center")
    # j = 0
    try:
        while True:
            logger.info(f"{i()} just before get_uncached_urls")
            uncached_urls = URLCatalog.fetch(
                limit=20,
                random_sample=True,
                where=[
                    # "((html_content IS NULL OR html_content = '') AND (url LIKE '%/officers%' OR (url LIKE 'https://opencorporates.com/companies/%/%' AND LENGTH(url) - LENGTH(REPLACE(url, '/', '')) = 5)))"
                    # " (html_content IS NULL OR html_content = '') AND url LIKE 'https://opencorporates.com/companies/%/%' AND LENGTH(url) - LENGTH(REPLACE(url, '/', '')) = 5"
                    # "(html_content IS NULL OR html_content = '')"
                    # " AND url LIKE 'https://opencorporates.com/companies/%/%'",
                    # "LENGTH(url) - LENGTH(REPLACE(url, '/', '')) = 5"
                    "(html_content IS NULL OR html_content = '')",
                    " (url LIKE '%/officers%' OR url LIKE '%relationship%' OR url LIKE '%events%' OR url LIKE '%/merger%')",
                    # "(html_content IS NULL OR html_content = '')"
                    # " AND url LIKE 'https://opencorporates.com/companies/%/%'",
                    # "LENGTH(url) - LENGTH(REPLACE(url, '/', '')) = 5",
                ],
            )
            logger.info(f"{i()} {uncached_urls}")
            # break
            if not uncached_urls:
                logger.info(f"{i()}📜🏁🚩✅ All URLs have been processed.")
                break
            # pretty = Pretty([url for url, _, _ in uncached_urls])
            # panel = Panel(pretty)
            # gs.console.rule("[bold red] URL LIST")
            # logger.info(f"{i()}📜 These are the list of urls we are doing:")
            # gs.console.print(panel)
            # gs.console.rule()
            opening()
            k = 1
            for url_record in uncached_urls:
                # Check for termination signal within the loop
                check_and_terminate()

                gs.console.rule()
                gs.console.rule(f"{k}")

                k += 1
                gs.current_url = url_record[1]
                gs.current_company_number = url_record[2]
                gs.current_jurisdiction = url_record[3]

                section(f"⌛⛏️⛏️ Working on {gs.current_url}", "sky_blue1", "right")

                warm_cache()
                gs.console.rule()
                gs.console.rule()
                gs.console.rule()
                gs.console.rule()
                rando = random.uniform(1, 5)
                logger.info(
                    f"{i()} ✅ just a breathe for {rando}time, we are done with {gs.current_url}"
                )
                gs.console.rule()
                time.sleep(rando)
                # mark_url_as_processed(gs.current_url)
                # break
                # j+=1
            exiting()
            # break
        logger.info(
            f"{i()} ✅ Scrapping URL data ----- Data successfully saved to database"
        )
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(f"{traceback.format_exc()}")
        section("💀 SCRAPPING ----- 💀💀💀💀💀💀", "red", "center")
        exiting()
        shutdown_logger()
    finally:
        exiting()
        shutdown_logger()
        section("ENDING SCRAPPING ----- bye bye 👋", "blue1", "center")


# @app.command()
# def addurls():
#     """
#     Inserts a list of base URLs into the database, and then inserts derived URLs using URL_PATTERNS with the base URL's ID as the parent_id.
#     """
#     base_urls = [
#         "https://opencorporates.com/companies/us_wy/2023-001310337"
#     ]

#     URL_PATTERNSs = [
#         "/statements/subsidiary_relationship_object",
#         "/statements/subsidiary_relationship_subject",
#         "/statements/branch_relationship_subject",
#         "/statements/branch_relationship_object",
#         "/statements/total_shares_object",
#         "/statements/total_shares_subject",
#         "/statements/share_parcel_object",
#         "/statements/share_parcel_subject",
#         "/statements/merger_object",
#         "/statements/merger_subject",
#         "/statements/trademark_registration",
#         "/statements/identifier_delegate",
#         "/statements/gazette_notice_delegate",
#         "/statements/control_statement_subject",
#         "/statements/control_statement_object",
#         "/statements/industry_code",
#         "/statements/supplier_relationship",
#         "/statements/subsequent_registration",
#         "/statements/alternate_registration",
#         "/filings",
#         "/events",
#         "/officers"
#     ]

#     try:
#         for base_url in base_urls:
#             # Initialize base_url_id to ensure it's defined before usage
#             base_url_id = None

#             # Extract company ID and jurisdiction
#             company_id = extract_company_number_from_url(base_url)
#             jurisdiction = extract_jurisdiction_from_url(base_url)
#             existing_base_url = None

#             with gs.read() as readsession:
#                 # Check if the base URL already exists
#                 existing_base_url = readsession.query(URLCatalog).filter_by(url=base_url).first()
#                 if existing_base_url:
#                     base_url_id = existing_base_url.id  # Extract base_url_id while still in the session
#                     logger.info(f"Base URL existed: {base_url} with ID: {base_url_id}, Company ID: {company_id}, Jurisdiction: {jurisdiction}")


#             if not existing_base_url:
#                 # Insert the base URL
#                 new_base_url_record = URLCatalog(
#                     url=base_url,
#                     company_number=company_id,
#                     jurisdiction=jurisdiction,
#                     completed=False
#                 )

#                 with gs.write() as writesession:
#                     writesession.add(new_base_url_record)
#                     writesession.commit()
#                     # Access ID after commit
#                     writesession.refresh(new_base_url_record)  # Ensures it's refreshed and bound
#                     base_url_id = new_base_url_record.id
#                 logger.info(f"Base URL saved: {base_url} with ID: {base_url_id}, Company ID: {company_id}, Jurisdiction: {jurisdiction}")

#             # Insert derived URLs using the base URL as the parent_id
#             for pattern in URL_PATTERNSs:
#                 derived_url = f"{base_url}{pattern}"
#                 existing_derived_url =  None
#                 with gs.read() as readsession:
#                     existing_derived_url =  readsession.query(URLCatalog).filter_by(url=derived_url).first()
#                 if not existing_derived_url:
#                     derived_url_record = URLCatalog(
#                         url=derived_url,
#                         company_number=company_id,
#                         jurisdiction=jurisdiction,
#                         completed=False,
#                         parent_id=base_url_id
#                     )
#                     with gs.write() as writesession:
#                         writesession.add(derived_url_record)
#                     logger.info(f"Derived URL saved: {derived_url} with parent ID: {base_url_id}, Company ID: {company_id}, Jurisdiction: {jurisdiction}")
#                 else:
#                     logger.info(f"Derived URL existed: {derived_url} with parent ID: {base_url_id}, Company ID: {company_id}, Jurisdiction: {jurisdiction}")

#     except IntegrityError as e:
#         with gs.write() as writesession:
#             writesession.rollback()
#         logger.error(f"Error inserting URLs: {e}")


# @app.command()
# def init_db(
#     fix: bool = Option(False, "--fix", "-f", help="Attempt to fix schema mismatches.")
# ):
#     """
#     Initialize the database. If the 'fix' flag is provided, it attempts to fix schema mismatches.
#     """
#     # print("init_db...")
#     # logger = logging.getLogger('app')
#     logger.info(f"{i()}🔧📄 Initializing the database.")
#     try:
#         # print(get_base_url_id("0551741","California"))
#         # insert_urls_with_patterns()
#         # initialize_db(fix)
#         print("doing nothing")
#     finally:
#         logger.info(f"{i()}✅ Database initialized successfully.")
#         exiting()
#         shutdown_logger()
#         section("ENDING DATABASE INITIALIZING ----- bye bye 👋","blue1","center")


# @app.command()
# def do_addresses():
#     """
#     Inserts address data from the specified directory into the database.
#     """
#     logger.info(f"{i()}🔧📄 Initializing the database.")
#     try:
#         insert_addresses()
#         print("doing nothing")
#     finally:
#         logger.info(f"{i()}✅ Database initialized successfully.")
#         section("ENDING ADDRESS INSERTION ----- bye bye 👋", "blue1", "center")
#         shutdown_logger()
@app.command()
def gui():
    """
    Run the GUI application.
    """
    logger.info("Starting GUI")
    gs.app = MainWindow()
    gs.appcolors = gs.app.style.colors
    gs.app.mainloop()


if __name__ == "__main__":
    # print("main...")
    multiprocessing.freeze_support()
    setup_logger()
    exclude_files_from_console(
        [
            "utils.py",
            # "mixins.py",
            "cache.py",
            "url_handlers.py",
            "base.py",
            "webdriver.py",
            "remote_connection.py",
            "connectionpool.py",
            "service.py",
            "retry.py",
        ]
    )
    initialize()
    # app()
