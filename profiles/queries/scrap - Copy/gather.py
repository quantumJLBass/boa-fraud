# gather.py
import multiprocessing
from contextlib import contextmanager
from typer import Typer#, Option
from rich.console import Console
# from rich import print as rprint
from rich.pretty import Pretty
from rich.panel import Panel
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine#, func, text, and_, or_
from services.signal_handler import setup_signal_handling  # Import the signal handler

# from db.init_db import *

#from services.notes import *
from services.applogging import logger #*
import gs
from utils.useollama import *
#from oneoffs import insert_addresses
from db.dbefclasses import URLCatalog
from db.cache import get_uncached_urls#, get_incomplete_urls, get_base_url_id
from db import *
from .utils.utils import *
from .services.scraper import scrape_data,warm_cache
from .settings import *
# from dbutils.data_loader import load_data_from_json


app = Typer()
gs.console = Console()

def create_session_manager(
    db_file
):
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
    sessionLocal = sessionmaker(bind=engine)

    @contextmanager
    def get_session():
        session = sessionLocal()
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
    DB_FILE = "db/cache.db"
    try:
        gs.read = create_session_manager(DB_FILE)
        # if gs.read:
        #     logger.info(f"🧮🔆 Database read session initialized successfully for {DB_FILE}")
        # else:
        #     logger.error(f"🧮🔆 Failed to initialize read session for {DB_FILE}")
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
        # if gs.write:
        #     logger.info(f"🧮🔆 Database write session initialized successfully for {DB_FILE}")
        # else:
        #     logger.error(f"🧮🔆 Failed to initialize write session for {DB_FILE}")
    except Exception as e:
        logger.error(f"💥🚩 Error initializing write session for {DB_FILE}: {e}")

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
    section(f"{i()}hello, I'm starting the scraper 🕵️‍♂️. let's go!!! 🚀", "dark_sea_green4", "center")

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
        # connect_db_write()
        # connect_db_read()

        # Check if read and write sessions are initialized
        # if gs.read is None or gs.write is None:
        #     logger.error(f"{i()}🔧🗃️ Database sessions are not initialized properly. Attempting to reconnect.")
        #     connect_db_write()
        #     connect_db_read()

        while True:
            # logger.debug(f"{i()}📛📛 WRITE {type(gs.write)}")
            # logger.debug(f"{i()}📛📛 READ {type(gs.read)}")
            # on each loop of 20 urls we will close the old vpn, and open a new one
            opening() # should we really mess with the vpn here?
            gathering_urls = URLCatalog.fetch_records(
                                limit=20,
                                where="completed = FALSE"
                            )
            # logger.debug(f"{i()}📛📛 WRITE {type(gs.write)}")
            # logger.debug(f"{i()}📛📛 READ {type(gs.read)}")
            logger.info(f"{i()}🧺 Gathering URLs: {gathering_urls}")
            # logger.info(f"{i()} {uncached_urls}")
            # break
            if not gathering_urls:
                logger.info(f"{i()}📜🏁🚩✅ All URLs have been processed.")
                break
            k=1
            for gathering in gathering_urls:
                gs.console.rule()
                gs.console.rule(f"{k}")
                k+=1

                gs.current_url = gathering[1]
                gs.current_company_number = gathering[2]
                gs.current_jurisdiction = gathering[3]

                section(f"⌛⛏️⛏️ Working on {gs.current_url}", "sky_blue1", "right")

                logger.debug(f"{i()}📛📛 WRITE {type(gs.write)}")
                logger.debug(f"{i()}📛📛 READ {type(gs.read)}")
                company_data = scrape_data()
                if company_data:
                    #save_data_intermediate({url: company_data})
                    # should the saved in the db by now and we are not saving to json anymore
                    # the note creation is what happens next
                    #note_the_data(gs.current_url)
                    logger.info(f"{i()}✍️✍️⛏️ Scrapped URL data: {company_data}")
                    # mark_url_as_processed(url)
                else:
                    logger.error(f"{i()}🛑🚨🚩 Scrapping URL data failed. Main content not found for URL {gs.current_url}")


                gs.console.rule()
                gs.console.rule()
                gs.console.rule()
                gs.console.rule()
            exiting() # should we really mess with the vpn here?

        logger.info(f"{i()} ✅ Scrapping URL data ----- Data successfully saved to company_data.json")
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
            uncached_urls = get_uncached_urls(
                                limit=20,
                                random_sample=True,
                                where=[
                                    "url LIKE 'https://opencorporates.com/companies/%/%'",
                                    "LENGTH(url) - LENGTH(REPLACE(url, '/', '')) = 5"
                                ]
                            )
            # logger.info(f"{i()} {uncached_urls}")
            # break
            if not uncached_urls:
                logger.info(f"{i()}📜🏁🚩✅ All URLs have been processed.")
                break
            pretty = Pretty([url for url, _, _ in uncached_urls])
            panel = Panel(pretty)
            gs.console.rule("[bold red] URL LIST")
            logger.info(f"{i()}📜 These are the list of urls we are doing:")
            gs.console.print(panel)
            gs.console.rule()
            opening()
            k=1
            for url_record in uncached_urls:
                gs.console.rule()
                gs.console.rule(f"{k}")
                k+=1
                gs.current_url = url_record[1]
                gs.current_company_number = url_record[2]
                gs.current_jurisdiction = url_record[3]
                section(f"⌛⛏️⛏️ Working on {gs.current_url}", "sky_blue1", "right")
                warm_cache()
                gs.console.rule()
                gs.console.rule()
                gs.console.rule()
                gs.console.rule()
                # mark_url_as_processed(gs.current_url)
            exiting()

        logger.info(f"{i()} ✅ Scrapping URL data ----- Data successfully saved to database")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(f"{traceback.format_exc()}")
        section("💥💥💥💥💥 SCRAPPING ----- 💥💥💥💥", "red", "center")
        exiting()
        shutdown_logger()
    finally:
        exiting()
        shutdown_logger()
        section("ENDING SCRAPPING ----- bye bye 👋", "blue1", "center")

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

if __name__ == "__main__":
    # print("main...")
    multiprocessing.freeze_support()
    setup_logger()
    exclude_files_from_console([
        'utils.py',
        # 'mixins.py',
        'remote_connection.py',
        'connectionpool.py',
        'service.py',
        'retry.py'
    ])
    initialize()
    app()
