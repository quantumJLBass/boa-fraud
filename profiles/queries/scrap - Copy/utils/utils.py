# utils.py
import re
import json
import subprocess
import time
# import logging
import random
# import sys
# import socket
import traceback
from typing import Union, Tuple, List, Dict#, Any
#from datetime import datetime
# from bs4 import BeautifulSoup
#import usaddress
import probablepeople as pp
# import typer
# from rich.console import Console
# from rich.markup import escape
# from rich.logging import RichHandler
# from rich import print as rprint
# from rich.text import Text
# from rich.emoji import Emoji
# import rich.emoji
# from enum import Enum
# from io import BytesIO
import dateparser
import requests
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, WebDriverException
# from loguru import logger
from serivces.applogging import logger
from serivces.scraper import ensure_url
import gs
from .settings.settings import *
# from utils.useollama import *
from db.dbefclasses import Jurisdiction, AddressType
#URLCatalog, RoleType, , Base, Address, Person,
    # Company, Link, Attribute, Assertion, Filing,
    # Event, Officer, PersonOfficer, CompanyOfficer,
    # PeopleAddress, CompanyAddress, RelatedRelationship,
    # SubsidiaryRelationship, IdentifierDelegate, TotalShare,
    # Publication, Classification, GazetteNotice,
    # TrademarkRegistration, LEIData, LEIEntityDetail,
    # LEIAddress, IndustryCode, CompanyIndustryCode,

display_debug = True

def reset_connection_pool() -> None:
    """
    Resets the connection pool used by urllib3 to prevent connection pool leaks, which can lead to
    "too many open files" errors.

    This function is used to prevent memory leaks caused by persistent connections to websites.
    """
    try:
        import urllib3
        pool_manager = urllib3.PoolManager()
        pool_manager.clear()  # Ensure PoolManager instance is used
        logger.info(f"{i()}✅🔌📡 RESET CONNECTION POOL ------ Connection pool reset successfully")
    except Exception as e:
        logger.error(f"{i()}🛑🚨🚩🔌📡 RESET CONNECTION POOL ------ Error resetting connection pool: {e}\n{traceback.format_exc()}")

def get_random_chrome_version():
    """
    Generate a random Chrome version number to mimic different user agents.

    Returns:
        str: A string representing the randomly generated Chrome version number in the format "major_version.minor_version.build_version.patch_version".
    """
    major_version = random.randint(80, 90)
    minor_version = random.randint(0, 4430)
    build_version = random.randint(0, 200)
    patch_version = random.randint(0, 100)
    return f"{major_version}.{minor_version}.{build_version}.{patch_version}"

def get_random_user_agent():
    """
    Generate a random user agent string based on a list of pre-defined templates.

    Returns:
        str: A randomly selected user agent string with a randomly generated Chrome version number.
    """
    user_agent_template = random.choice(USER_AGENTS)
    chrome_version = get_random_chrome_version()
    return user_agent_template.format(version=chrome_version)

def setup_driver():
    """
    Sets up a Chrome WebDriver instance with specific options to mimic a normal user's browser behavior.

    Returns:
        webdriver.Chrome: An instance of the Chrome WebDriver with the specified options.

    Raises:
        None
    """
    options = Options()
    options.add_argument("--headless")  # Run Chrome in headless mode
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-plugins-discovery")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")  # Suppress ChromeDriver logs
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")  # Start maximized
    options.add_argument("--disable-browser-side-navigation")  # Improve page load performance
    options.add_argument("--disable-renderer-backgrounding")
    # Set user agent to mimic a normal user
    #user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version} Safari/537.36"
    user_agent = get_random_user_agent()
    options.add_argument(f"user-agent={user_agent}")

    # Enable the use of automation extensions and remove 'controlled by automated test software' info bar
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Initialize the Chrome WebDriver with the specific path to chromedriver.exe
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    service = Service(DRIVER_PATH)  # Update this path if necessary
    driver = None #starting off with a clean var for the driver

    # Attempt to set up the driver with retries
    for attempt in range(3):
        try:
            driver = webdriver.Chrome(service=service, options=options)
            # Store the PID of the ChromeDriver process
            driver_pid = driver.service.process.pid
            logger.debug(f"{i()}🧨 DRIVER PID --- WebDriver PID: {driver_pid}")
            gs.driver_pid = driver_pid
            gs.current_driver = driver
            simulate_user_actions()
            break
        except WebDriverException as e:
            logger.error(f"{i()}🛑🚨🚩Error setting up WebDriver: {e}")
            logger.error(f"{i()}{traceback.format_exc()}")
            random_wait(1, 2)  # Wait before retrying

    if not driver:
        raise WebDriverException(f"{i()}🛑🚨🚩Failed to initialize WebDriver after multiple attempts.")
    gs.current_driver = driver
    return gs.current_driver

def simulate_user_actions():
    """
    Simulates user actions to mimic real user behavior.

    This function performs a series of actions to mimic real user behavior in the browser. It includes the following steps:
    1. Spoofs the WebDriver property to further mimic a real browser.
    2. Moves the mouse to simulate user interaction.
    3. Scrolls the page up and down to mimic scrolling behavior.
    4. Waits for a random amount of time to mimic real user behavior.

    Args:
        driver (WebDriver): The WebDriver instance used to interact with the browser.

    Returns:
        None
    """
    # Spoof the WebDriver property to further mimic a real browser
    gs.current_driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    logger.debug(f"{i()}✅ ✍️ Spoofed the WebDriver property to further mimic a real browser")
    # # Move mouse
    # actions = webdriver.ActionChains(gs.current_driver)
    # for _ in range(random.randrange(1, 5)):
    #     actions.move_by_offset(random.randint(0, 100), random.randint(0, 100)).perform()
    #     logger.debug(f"{i()}Moved mouse")
    #     time.sleep(random.uniform(0.1, 0.3))

    # # Scroll down the page
    # for _ in range(random.randrange(1, 2)):
    #     gs.current_driver.execute_script("window.scrollBy(0, 500);")
    #     logger.debug(f"{i()}Scrolled down the page")
    #     time.sleep(random.uniform(0.1, 0.3))

    # # Scroll up the page
    # for _ in range(random.randrange(1, 2)):
    #     gs.current_driver.execute_script("window.scrollBy(0, -500);")
    #     logger.debug(f"{i()}Scrolled up the page")
    #     time.sleep(random.uniform(0.1, 0.3))

def get_random_vpn_index():
    """
    Generates a random index from the list of VPN configurations excluding the current index.

    This function uses the global variable `gs.current_vpn_index` to track the index
    of the current VPN configuration. It generates a random index that excludes the current index.

    Returns:
    -------
    int
        A random index from the list of VPN configurations excluding the current index.

    Raises:
    ------
    ValueError
        If there are no other indices to choose from because the list of VPN configurations
        contains one or zero elements.
    """
    current_index = gs.current_vpn_index

    if len(VPN_CONFIGS.config_files) <= 1:
        raise ValueError(f"{i()}🛑🚨🚩Not enough VPN configurations to select a different random index.")

    # Generate a random index excluding the current index
    random_index = current_index
    while random_index == current_index:
        random_index = random.randint(0, len(VPN_CONFIGS.config_files) - 1)

    return random_index

def wait_for_vpn_state(
    connection: bool = True
) -> bool:
    """
    Waits until the VPN is connected or disconnected by checking the current IP address.

    Args:
        connection (bool, optional): If True, waits until the VPN is connected.
            If False, waits until the VPN is disconnected. Defaults to True.

    Returns:
        bool: True if the desired VPN state is achieved, False otherwise.
    """
    logger.debug(f"{i()}⌛ WAITING FOR VPN STATE")
    retry_count = 0

    while retry_count < MAX_VPN_RETRIES:
        random_wait(1, 2)
        current_ip = get_current_ip()
        logger.debug(f"{i()}♻️ VPN connection attempt {retry_count}, current IP: {current_ip}")

        if connection and current_ip and current_ip != gs.initial_ip:
            gs.current_ip = current_ip
            logger.debug(f"{i()}✅ VPN connected. Current IP: {current_ip}")
            return True
        elif not connection and (current_ip is None or current_ip == gs.initial_ip):
            logger.debug(f"{i()}✅ VPN disconnected. Current IP: {current_ip}")
            return True
        retry_count += 1

    logger.error(f"{i()}🛑🚨🚩Max VPN retries reached ({MAX_VPN_RETRIES}). Could not achieve desired VPN state.")
    return False

def start_vpn() -> None:
    """
    Starts the VPN using the specified configuration file and ensures it is connected.

    Args:
        None

    Returns:
        subprocess.Popen: The process object representing the running VPN process, or None if all VPN attempts fail.

    Raises:
        None

    Description:
        This function kills any existing OpenVPN process, waits until the VPN is disconnected,
        and then starts a new OpenVPN connection using a random configuration file from the list.
        It retries with different VPN configurations until a successful connection is established
        or all configurations have been tried. It returns the process object representing the
        running VPN process, or None if all attempts fail.
    Notes:
        - Kills any existing OpenVPN process before starting the new connection.
        - Waits until the VPN is connected by checking the current IP address.
        - Logs the start of the VPN connection and the connected IP address.
    """
    logger.debug(f"{i()}📡 STARTING  VPN ----- Starting progress")
    for _ in range(len(VPN_CONFIGS.config_files)):
        gs.current_vpn_index = get_random_vpn_index()
        config_path = VPN_CONFIGS[gs.current_vpn_index]

        # Terminate existing VPN and ensure it is disconnected
        # if not terminate_vpn():
        #     logger.error(f"{i()}🛑🚨🚩STARTING  VPN FAIL ----- Failed to disconnect VPN before starting a new one. Exiting.")
        #     return None

        # Start the new OpenVPN connection
        gs.current_vpn = subprocess.Popen(["openvpn", "--config", config_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.debug(f"{i()}📡 STARTING  VPN ----- Starting VPN with config: {config_path}")

        # Wait until VPN is connected by checking the IP address
        if wait_for_vpn_state(connection=True):
            logger.debug(f"{i()}✅📡 STARTING  VPN ----- VPN connected. Current IP: {gs.current_ip}")
            return None
            # return gs.current_vpn
        else:
            logger.error(f"{i()}🛑📡🚨🚩STARTING  VPN FAIL ----- Failed to connect VPN with config: {config_path}")

    logger.error(f"{i()}🛑📡🚨🚩STARTING  VPN FAIL ----- All VPN attempts failed.")
    return None

def is_process_running(
    process_name
):
    """
    Checks if a process with the given name is running.

    Parameters:
        process_name (str): The name of the process to check.

    Returns:
        bool: True if the process is running, False otherwise.

    Notes:
        - Uses psutil to iterate over all running processes and checks if any have the given name.
        - Logs the process name and the result of the check.
        - Returns False and logs an error if an exception occurs while checking the process.
    """
    logger.debug(f"{i()}🔍CHECKING IF PROCESS {process_name} IS RUNNING")
    try:
        # Check if the process is running using psutil
        running = any(proc.name().lower() == process_name.lower() for proc in psutil.process_iter())
        logger.debug(f"{i()}🔍FOUND THAT PROCESS {process_name} RUNNING {running}")
        return running
    except Exception as e:
        logger.error(f"{i()}📛💀Error checking process: {e}")
        logger.error(traceback.format_exc())
        return False

def terminate_vpn():
    """
    Terminates the VPN process and ensures it is disconnected.

    This function terminates the global VPN process if it is running. It first checks if the `gs.current_vpn` variable is not None, and if so, it gracefully terminates the process using the `terminate()` method. If the process is still running after termination, it forcefully kills it using the `kill()` method. The function then waits for the process to terminate using the `wait()` method.

    After terminating the VPN process, the function kills any lingering `openvpn.exe` processes forcefully using the `taskkill` command. It logs a debug message indicating that any lingering processes are being killed.

    The function resets the `gs.current_vpn` variable to None and sets `gs.current_vpn_index` to -1 to indicate that there is no current VPN process.

    Finally, the function ensures that the VPN is fully disconnected by checking the current IP state using the `wait_for_vpn_state()` function with the argument `False`. The function returns the result of the `wait_for_vpn_state()` function.

    Parameters:
        None

    Returns:
        bool: The result of the `wait_for_vpn_state()` function indicating whether the VPN is fully disconnected.

    Notes:
        - The function terminates the VPN process by calling the `terminate()` method on the `gs.current_vpn` process object.
        - If the VPN process is still running after termination, it forcefully kills it using the `kill()` method.
        - The function waits for the VPN process to terminate by calling the `wait()` method.
        - The function kills any lingering `openvpn.exe` processes forcefully using the `taskkill` command.
        - The function resets the `gs.current_vpn` variable to None and sets `gs.current_vpn_index` to -1.
        - The function ensures that the VPN is fully disconnected by checking the current IP state using the `wait_for_vpn_state()` function.

    Example:
        >>> terminate_vpn()
        True
    """
    logger.debug(f"{i()}🧨📡TERMINATING VPN ----- Starting ")
    if gs.current_vpn:
        logger.debug(f"{i()}🧨📡TERMINATING VPN ----- Killing current VPN process.")
        gs.current_vpn.terminate()  # Gracefully terminate the global VPN process
        gs.current_vpn.kill()  # Forcefully kill the global VPN process if it's still running
        gs.current_vpn.wait()  # Wait for the process to terminate
        logger.debug(f"{i()}✅📡TERMINATING VPN ----- Successfully Killed current VPN process.")

    if is_process_running("openvpn.exe"):
        try:
            # Kill any lingering openvpn.exe processes forcefully
            logger.debug(f"{i()}🧨📡TERMINATING VPN ----- Killing any lingering openvpn.exe processes.")
            subprocess.run(["taskkill", "/f", "/im", "openvpn.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.debug(f"{i()}✅💥📡openvpn.exe has been terminated.")
        except Exception as e:
            logger.error(f"{i()}⚠️📛📡Error terminating process: {e}")
            logger.error(f"{i()}{traceback.format_exc()}")
    else:
        logger.info(f"{i()}✅💀📡openvpn.exe is not running.")


    gs.current_vpn = None  # Reset the global VPN process variable
    gs.current_vpn_index = -1
    logger.info(f"{i()}✅📡 TERMINATING VPN ----- Terminated and killed the global VPN process.")

    # Ensure the VPN is fully disconnected by checking the current IP state
    return wait_for_vpn_state(False)

def terminate_driver() -> None:
    """
    Terminates the WebDriver instance.

    Args:
        driver (webdriver.Chrome): The WebDriver instance to terminate.

    Returns:
        None

    Raises:
        None

    Notes:
        - Quits the WebDriver instance.

    Example:
        >>> driver = setup_driver()
        >>> terminate_driver(driver)
    """
    section("🧨⌛TERMINATING DRIVER","dark_orange")
    logger.debug(f"{i()}🧨⌛TERMINATING DRIVER --- Starting termination")

    def safe_execute(driver, command, url):
        for attempt in range(3):  # Retry up to 3 times
            try:
                driver.execute(command, url)
                return True  # Exit loop if successful
            except Exception as e:
                logger.error(f"{i()}🛑🚨🚩 TERMINATING DRIVER FAIL --- Error during {command}: {e}")
                logger.error(f"{i()}{traceback.format_exc()}")
                time.sleep(2)  # Wait before retrying
        return False

    if isinstance(gs.current_driver, webdriver.Chrome):
        try:
            logout()
        except Exception as e:
            logger.error(f"{i()}🛑🚨🚩TERMINATING DRIVER FAIL --- Error during logout: {e}")
            logger.error(f"{i()}{traceback.format_exc()}")
        finally:
            try:
                logger.debug(f"{i()}🧨 CLOSING DRIVER --- terminating WebDriver")
                gs.current_driver.close()
            except Exception as e:
                logger.error(f"{i()}🛑🚨🚩 TERMINATING DRIVER FAIL --- Error during driver.close(): {e}")
                logger.error(f"{i()}{traceback.format_exc()}")
            finally:
                # try:
                #     logger.debug(f"{i()}🧨 DELETING ALL NETWORK CONDITIONS --- terminating WebDriver")
                #     driver.delete_network_conditions()
                # except Exception as e:
                #     logger.error(f"{i()}🛑🚨🚩 TERMINATING DRIVER FAIL --- Error during driver.delete_network_conditions(): {e}")
                if not safe_execute(gs.current_driver, "DELETE", "/session/{sessionId}/chromium/network_conditions"):
                    logger.error(f"{i()}🛑🚨🚩 TERMINATING DRIVER FAIL --- Failed to delete network conditions after retries")

                if not safe_execute(gs.current_driver, "DELETE", "/session/{sessionId}/window"):
                    logger.error(f"{i()}🛑🚨🚩 TERMINATING DRIVER FAIL --- Failed to delete window after retries")

                try:
                    logger.debug(f"{i()}🧨 QUITING THE DRIVER --- terminating WebDriver")
                    gs.current_driver.quit()
                except Exception as e:
                    logger.error(f"{i()}🛑🚨🚩 TERMINATING DRIVER FAIL --- Error during driver.quit(): {e}")
                finally:
                    # Additional step to ensure all WebDriver processes are terminated
                    if is_process_running("chromedriver.exe"):
                        try:
                            # Kill any lingering openvpn.exe processes forcefully
                            logger.debug(f"{i()}🧨🛰️TERMINATING DRIVER ----- Killing any lingering chromedriver.exe processes.")
                            subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                            logger.debug(f"{i()}✅💥🛰️ chromedriver.exe has been terminated.")
                        except Exception as e:
                            logger.error(f"{i()}⚠️📛🛰️ Error terminating chromedriver.exe process: {e}")
                            logger.error(f"{i()}{traceback.format_exc()}")
                    else:
                        logger.info(f"{i()}⚠️💀🛰️ chromedriver.exe is not running.")
                    # Additional step to ensure the specific WebDriver process is terminated
                    try:
                        if gs.driver_pid:
                            logger.debug(f"{i()}🧨 TERMINATING SPECIFIC DRIVER PROCESS --- PID: {gs.driver_pid}")
                            driver_process = psutil.Process(gs.driver_pid)
                            driver_process.terminate()
                            driver_process.wait()
                            subprocess.run(["kill", "-9", str(gs.driver_pid)], check=True)
                            logger.info(f"{i()}🧨✅ TERMINATED SPECIFIC DRIVER PROCESS --- PID: {gs.driver_pid}")
                    except Exception as e:
                        logger.error(f"{i()}🛑🚨🚩 TERMINATING SPECIFIC DRIVER PROCESS FAIL --- Error: {e}")
                        logger.error(f"{i()}{traceback.format_exc()}")
                    finally:

                        # Ensure the driver reference is set to None to completely nullify the session
                        logger.info(f"{i()}🧨✅🗑️ TERMINATING DRIVER --- WebDriver instance set to None.")
                        gs.current_driver = None
                        # Nullify the session
                        logger.info(f"{i()}🧨✅🗑️TERMINATING DRIVER --- Session nullified.")
                        logger.info(f"{i()}🧨✅🗑️TERMINATING DRIVER --- WebDriver terminated.")
    else:
        logger.error(f"{i()}🛑🚨🚩 TERMINATING DRIVER FAIL --- Invalid driver instance: {gs.current_driver}")

def opening() -> None:
    """
    Opens the program by starting the VPN and driver processes.

    This function calls the `start_vpn()` and `setup_driver()` functions to start the VPN and WebDriver processes, respectively. It also logs a message indicating that the program is starting.

    Parameters:
        None

    Returns:
        None

    Raises:
        None

    Notes:
        - The function calls `start_vpn()` and `setup_driver()` to start the VPN and WebDriver processes.
        - The function logs a message indicating that the program is starting.

    Example:
        >>> opening()
    """
    section("📡⌛STARTING SERVICES AND CONNECTIONS","dark_orange")
    logger.debug(f"{i()}📡OPENING ------starting to start")
    retries = 0
    while retries < MAX_VPN_RETRIES:
        try:

            logger.debug(f"{i()}📡⚙️OPENING ------ VPN startup")
            start_vpn()
            logger.debug(f"{i()}📡⚙️✅OPENING ------ Completed VPN startup")

            logger.debug(f"{i()}📡⚙️OPENING ------ Starting the driver")
            setup_driver()
            logger.debug(f"{i()}📡⚙️✅OPENING ------ Completed the driver startup")

            logger.debug(f"{i()}📡⚙️OPENING ------ logging in to the user")
            login(True)
            logger.debug(f"{i()}📡✅OPENING ------ All start up steps are completed")
            return None
            # return driver
        except Exception as e:
            logger.error(f"{i()}🛑📡🚨🚩OPENING ------Error starting a VPN: {e}")
            logger.error(f"{i()}{traceback.format_exc()}")
            retries += 1

    raise Exception(f"{i()}🛑📡🚨🚩OPENING ------Failed to open a VPN after multiple retries")

def exiting() -> None:
    """
    Exits the program by terminating the VPN and driver processes.

    This function calls the `terminate_vpn()` and `terminate_driver()` functions to gracefully terminate the VPN and WebDriver processes, respectively. It also logs a message indicating that the program is exiting.

    Parameters:
        None

    Returns:
        None

    Raises:
        None

    Notes:
        - The function calls `terminate_vpn()` and `terminate_driver()` to gracefully terminate the VPN and WebDriver processes.
        - The function logs a message indicating that the program is exiting.

    Example:
        >>> exiting()
    """
    section("📡⌛EXITING SERVICES AND CONNECTIONS","dark_orange")
    logger.debug(f"{i()}📡EXITING ------starting to exit")

    reset_connection_pool()

    if gs.current_driver:
        terminate_driver()
        logger.debug(f"{i()}📡🗑️💥✅EXITING ------ deleted all cookies before quitting driver")

    if gs.current_vpn_index != -1:
        terminate_vpn()
        logger.debug(f"{i()}📡💥✅EXITING ------ Terminated current VPN process")

    logger.info(f"{i()}📡✅EXITING ------ Finished closing services and connections down")

def switch_vpn_and_driver() -> None:
    """
    Switches the VPN and driver by terminating the existing VPN process, waiting for the VPN state to be disconnected,
    selecting a random VPN configuration, starting a new VPN process, and setting up a new WebDriver instance.

    This function performs the following steps:
        1. Logs the start of the VPN switch process.
        2. Terminates the current VPN process if it is not the first VPN switch.
        3. Terminates the current WebDriver instance if it is provided.
        4. Generates a random VPN index to select a new VPN configuration.
        5. Starts a new VPN process using the selected VPN configuration.
        6. Waits for the VPN connection to be established.
        7. Sets up a new WebDriver instance.
        8. Performs a login with the new WebDriver instance.
        9. Returns the new WebDriver instance and the new VPN process.

    Args:
        driver (webdriver.Chrome, optional): The current WebDriver instance to be terminated. Defaults to None.

    Returns:
        Tuple[webdriver.Chrome, subprocess.Popen]: A tuple containing the new WebDriver instance and the process object representing the running VPN process.

    Raises:
        subprocess.CalledProcessError: If the taskkill command fails to terminate the openvpn.exe process.

    Example:
        >>> driver, vpn_process = switch_vpn_and_driver()

    Notes:
        - It is important to ensure that the current WebDriver and VPN process are properly terminated before starting new ones.
        - The function logs the progress and actions taken for debugging and monitoring purposes.
        - The VPN configurations are selected randomly from a predefined list of configurations (VPN_CONFIGS).
    """

    section("📡⌛VPN SWITCH","dark_orange")
    logger.debug(f"{i()}📡VPN SWITCH ------starting VPN switch")

    reset_connection_pool()

    if gs.current_driver:
        terminate_driver()
        logger.debug(f"{i()}📡🗑️💥✅VPN SWITCH ------ deleted all cookies before quitting driver")

    if gs.current_vpn_index != -1:
        terminate_vpn()
        logger.debug(f"{i()}📡💥✅VPN SWITCH ------ Terminated current VPN process")

    retries = 0
    while retries < MAX_VPN_RETRIES:
        try:
            start_vpn()
            setup_driver()
            login(True)
            logger.debug(f"{i()}📡💥✅VPN SWITCH ------ Completed VPN switch")
        except Exception as e:
            logger.error(f"{i()}🛑📡🚨🚩VPN SWITCH ------Error switching VPN: {e}")
            logger.error(f"{i()}{traceback.format_exc()}")
            retries += 1

    raise Exception(f"{i()}🛑📡🚨🚩VPN SWITCH ------Failed to switch VPN after multiple retries")

def login(forced:bool=False) -> None:
    """
    Logs in to the OpenCorporates website using the provided web driver.

    Args:
        driver (webdriver.Chrome): The web driver used to interact with the website.
        forced (bool, optional): Whether to force a logout before logging in. Defaults to False.

    Raises:
        NoSuchElementException: If the logout button or login form elements cannot be found.
        Exception: If all login attempts fail.

    Returns:
        None: If the user is already logged in or if a forced logout is performed.

    Description:
        This function logs in to the OpenCorporates website using the provided web driver. It performs the following steps:
        1. Sets the login URL to "https://opencorporates.com/users/sign_in".
        2. Navigates the web driver to the login page.
        3. Waits for the page to load by sleeping for 3 seconds.
        4. Checks if the user is already logged in by checking if the "Logout" element is present in the page source.
            - If the user is already logged in and the `forced` parameter is False, the function logs a message and returns.
            - If the user is already logged in and the `forced` parameter is True, the function logs out the current user by finding and clicking the "Logout" button.
        5. If the user is not already logged in, the function loops through the `CREDENTIALS` list to try different credentials.
            - For each set of credentials, the function finds the necessary input fields for the login form (email, password, submit button).
            - The function fills in the login form with the current set of credentials and clicks the submit button

    """
    logger.info(f"{i()}🔐⏳ LOGIN ----- Starting login.")
    account_url = "https://opencorporates.com/users/account"
    login_url = "https://opencorporates.com/users/sign_in"
    gs.current_driver.get(account_url)
    random_wait(1, 1)  # Wait for the page to load

    # Check if already logged in by checking the presence of user-specific element
    if "Logout" in gs.current_driver.page_source:
        if forced:
            try:
                logout()
                logger.info(f"{i()}✅🔐💥 LOGOUT(from login) ----- Forced logout completed.")
            except NoSuchElementException as e:
                logger.error(f"{i()}🛑🚨🚩LOGOUT(from login) ----- Logout button not found: {e}")
                logger.error(f"{i()}{traceback.format_exc()}")
                raise e
        else:
            logger.info(f"{i()}✅🔓 LOGIN ----- AUTH CHECK: Already logged in.")
            return
    else:
        logger.info(f"{i()}🔒LOGIN ----- AUTH CHECK: Not logged in.")

    gs.current_driver.get(login_url)
    random_wait(1, 1)
    retries = 0
    while retries < len(CREDENTIALS):
        username, password = random.choice(CREDENTIALS)
        logger.debug(f"{i()}🔑⏳LOGIN ----- Using credentials: {username}")
        try:
            # Find the necessary input fields for login
            email_input = gs.current_driver.find_element(By.ID, "user_email")
            password_input = gs.current_driver.find_element(By.ID, "user_password")
            submit_button = gs.current_driver.find_element(By.NAME, "submit")

            # Set the redirect URL using JavaScript for the hidden input
            gs.current_driver.execute_script(f'document.getElementById("redirect_to").value="{account_url}";')

            # Fill in the login form
            email_input.send_keys(username)
            password_input.send_keys(password)
            submit_button.click()
            logger.debug(f"{i()}🔑🔒⌛⏳‼️LOGIN ----- AUTH CHECK: Attempting to log in with {username}.")
            random_wait(1, 1)  # Wait for login to complete

            # Verify login success
            gs.current_driver.get(account_url)
            random_wait(1, 1)
            if "Logout" in gs.current_driver.page_source:
                logger.info(f"{i()}✅🔓 LOGIN ----- Login successful with {username}.")
                return
            else:
                logger.error(f"{i()}🛑🔐🚨LOGIN ----- Login failed with {username}. Retrying with different credentials.")
                retries += 1
        except NoSuchElementException as e:
            logger.error(f"{i()}🛑🔐❌LOGIN ----- Login form elements not found: {e}")
            logger.error(f"{i()}{traceback.format_exc()}")
            raise e
        except ElementNotInteractableException as e:
            logger.error(f"{i()}🛑🔐❌LOGIN ----- Element not interactable: {e}")
            logger.error(f"{i()}{traceback.format_exc()}")
            retries += 1
        except Exception as e:
            logger.error(f"{i()}🛑🔐🚨🚩LOGIN ----- Login attempt failed with error: {e}")
            logger.error(f"{i()}{traceback.format_exc()}")
            retries += 1

    raise Exception(f"{i()}🛑🔐🚨🚩LOGIN ----- All login attempts failed.")

def logout() -> None:
    """
    Logs out from the current session using the provided WebDriver.

    Args:
        driver (WebDriver): The WebDriver instance used to interact with the browser.

    Returns:
        None

    Raises:
        NoSuchElementException: If the logout button or link is not found.

    Description:
        This function attempts to find and click the logout button or link on the current page to log out from the session.
        It should be customized to match the specific implementation of the logout process for the target website.
    """
    try:
        # Replace with the actual locator for the logout button/link
        logout_button = gs.current_driver.find_element(By.XPATH, "//a[@data-method='delete' and @href='/users/sign_out']")
        logout_button.click()
        random_wait(1, 1)  # Wait for logout to complete
        logger.info(f"{i()}✅🔐💥LOGOUT----- Successfully logged out.")
    except NoSuchElementException:
        logger.error(f"{i()}🛑🔐🚨🚩LOGOUT----- Logout button not found.")
        logger.error(f"{i()}{traceback.format_exc()}")

def get_current_ip() -> str:
    """
    Get the current IP address.

    This function sends a GET request to 'https://api.ipify.org/' to retrieve the current IP address.
    If the request is successful, the IP address is returned. Otherwise, an error message is logged and None is returned.

    Returns:
        str or None: The current IP address if the request is successful, None otherwise.
    """

    try:
        response = requests.get('https://api.ipify.org/',timeout=5)
        gs.current_ip = response.text
        logger.debug(f"{i()}✅⚙️fetched IP address: {gs.current_ip}")
        return gs.current_ip
    except requests.RequestException as e:
        logger.error(f"{i()}🛑🚨🚩Error fetching IP address: {e}")
        logger.error(f"{i()}{traceback.format_exc()}")
        return None

def check_content_length(url: str) -> tuple[bool, int]:
    """
    Performs a GET request with stream=True and checks the content length by streaming.

    Args:
        url (str): The URL to fetch the headers for.

    Returns:
        bool: True if the content length is greater than the minimum size, False otherwise.
        int: The HTTP status code.
    """
    user_agent = get_random_user_agent()
    headers = {'User-Agent': user_agent}

    try:
        response = requests.get(url, headers=headers, allow_redirects=True, stream=True, timeout=5)
        status_code = response.status_code
        pattern = next((p for p in MIN_CONTENT_SIZE if p in url), None)
        min_size = MIN_CONTENT_SIZE.get(pattern, 1600)  # Default min size is 1600 bytes

        # Log all information from the response
        logger.info(f"⚠️📄🌎🚧 HEADERS FOR URL {url}")
        logger.info(f"⚠️📄🌎🚧Status Code: {status_code}")
        logger.info("⚠️📄🌎🚧Response Headers:")
        for header, value in response.headers.items():
            logger.info(f"⚠️📄🌎🚧{header}: {value}")
        logger.info(f"⚠️📄🌎🚧URL: {response.url}")
        logger.info(f"⚠️📄🌎🚧cookies: {response.cookies}")
        for name, value in response.cookies.items():
            logger.info(f"⚠️📄🌎🚧cookie:: {name}: {value}")
        logger.info(f"⚠️📄🌎🚧Encoding: {response.encoding}")
        logger.info(f"⚠️📄🌎🚧History: {response.history}")
        logger.info(f"⚠️📄🌎🚧Elapsed Time: {response.elapsed}")
        logger.info("⚠️📄🌎🚧Request Headers:")
        for header, value in response.request.headers.items():
            logger.info(f"⚠️📄🌎🚧{header}: {value}")
        logger.info(f"⚠️📄🌎🚧Request URL: {response.request.url}")
        logger.info(f"⚠️📄🌎🚧Request hooks: {response.request.hooks}")
        logger.info(f"⚠️📄🌎🚧Request method: {response.request.method}")
        logger.info(f"⚠️📄🌎🚧Request body: {response.request.body}")


        # Reading raw content
        raw_content = b''
        for chunk in response.iter_content(chunk_size=1024):
            raw_content += chunk
        raw_content_length = len(raw_content)

        # Actual content length
        # content_length = len(response.content)

        # Log content lengths
        logger.info(f"⚠️📄🌎🚧Request raw content_length: {raw_content_length}")
        # logger.info(f"⚠️📄🌎🚧Request content content_length: {content_length}")

        # Log first 100 bytes of the raw content for verification
        logger.info(f"⚠️📄🌎🚧raw content: {raw_content}")



        # Detailed raw response log
        logger.info(f"⚠️📄🌎🚧Raw Response: HTTP version: {response.raw.version}, Status: {response.raw.status}, Reason: {response.raw.reason}, Headers: {response.raw.headers}")

        # Detailed cookies log
        for cookie in response.cookies:
            logger.info(f"⚠️📄🌎🚧Cookie: {cookie.name} = {cookie.value}, Domain: {cookie.domain}, Path: {cookie.path}, Expires: {cookie.expires}")


        if status_code in SKIP_HTTP_CODES:
            logger.info(f"⏭️🌎🚧 CONTENT CHECK ----- Skipping URL {url} due to HTTP status code: {status_code}")
            return False, status_code

        if raw_content_length < min_size:
            logger.info(f"⏭️🌎🚧 CONTENT CHECK ----- Skipping URL {url} due to content length: {raw_content_length} bytes (min size: {min_size} bytes)")
            return False, status_code

        logger.info(f"⏭️🌎✅ CONTENT CHECK ----- {url} has sufficient content length: {raw_content_length} bytes (min size: {min_size} bytes)")
        return True, status_code
    except requests.RequestException as e:
        logger.error(f"💀💥🌎🚧 CONTENT CHECK ----- Error fetching headers for {url}: {e}")
        logger.error(f"{i()}{traceback.format_exc()}")
        return False, -1




def random_wait(min_seconds, max_seconds):
    """
    Generates a random wait time between the given minimum and maximum seconds, logs the wait time, and then sleeps for that amount of time.

    :param min_seconds: A float representing the minimum number of seconds to wait.
    :param max_seconds: A float representing the maximum number of seconds to wait.
    :return: None
    """
    wait_time = random.uniform(min_seconds, max_seconds)
    logger.info(f"{i()}⌛⏳ WAIT ----- Waiting for {wait_time:.2f} seconds.")
    time.sleep(wait_time)

def normalize_textblocks(text: str) -> str:
    """
    Normalizes a given text by removing newlines, tabs, and non-breaking spaces, replacing multiple spaces with a single space,
    removing specific strings, and stripping leading/trailing spaces.

    Parameters:
        text (str): The text to be normalized.

    Returns:
        str: The normalized text.

    Example:
        >>> normalize_textblocks("Hello\nWorld\t\u00a0")
        'Hello World'
    """
    logger.debug(f"{i()}✍️〽️NORMALIZE TEXT ----- Text before normalization: {text}")
    # Remove newlines, tabs, and non-breaking spaces
    text = re.sub(r'[\n\r\t\u00a0]+', ' ', text)

    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)

    # Remove specific strings
    text = text.replace(' (US)', '').replace('United States', '').replace(' UNITED STATES', '')
    #
    # Strip leading/trailing spaces
    text = text.strip()
    logger.debug(f"{i()}✅✍️〽️ NORMALIZE TEXT ----- Text after normalization: {text}")

    return text

def load_json_data() -> Tuple[Dict[str, str], Dict[str, str], List[Dict[str, Union[str, int]]]]:
    """
    Load the JSON data from the 'address-normalization-data.json' file and return the address parts, directionals, and US state cities.

    Returns:
        Tuple[Dict[str, str], Dict[str, str], List[Dict[str, Union[str, int]]]]: A tuple containing the address parts, directionals, and US state cities.
    """
    with open('odd&ends/address-normalization-data.json', encoding='utf-8') as fc:
        data = json.load(fc)

    this_address_parts = data['address_parts']
    this_directionals = data['directionals']
    this_us_state_cities = data['us_state_cities']

    return this_address_parts, this_directionals, this_us_state_cities

address_parts, directionals, us_state_cities = load_json_data()

def convert_name_to_last_first_mi(
    name: str
) -> str:
    """
    Convert a name in the format "First Middle Last" or "Last, First Middle" to "Last, First MI, Suffix".

    This function takes a name in various formats such as "First Middle Last", "Last, First Middle", and
    converts it to the format "Last, First MI, Suffix". The middle initial is extracted from the middle
    name if not provided, and generational suffixes are included if present.

    Parameters:
    ----------
    name : str
        The name to be converted. It can be in the format "First Middle Last", "Last, First Middle",
        or other variations handled by probablepeople.

    Returns:
    -------
    str
        The converted name in the format "Last, First MI, Suffix".

    Example:
        >>> convert_name_to_last_first_mi("John Smith Doe")
        'Doe, John S'
        >>> convert_name_to_last_first_mi("Doe, John Smith")
        'Doe, John S'
        >>> convert_name_to_last_first_mi("John Q. Public Jr.")
        'Public, John Q, Jr.'
        >>> convert_name_to_last_first_mi("Dr. Emily R. Stone")
        'Stone, Emily R'
    """
    logger.debug(f"{i()}♻️ ✍️ Converting name: {name}")
    try:
        parsed_name, name_type = pp.tag(name)
        if name_type == 'Person':
            parts = {
                'PrefixMarital': parsed_name.get('PrefixMarital', '').strip(),
                'PrefixOther': parsed_name.get('PrefixOther', '').strip(),
                'GivenName': parsed_name.get('GivenName', '').strip(),
                'FirstInitial': parsed_name.get('FirstInitial', '').strip(),
                'MiddleName': parsed_name.get('MiddleName', '').strip(),
                'MiddleInitial': parsed_name.get('MiddleInitial', '').strip(),
                'Surname': parsed_name.get('Surname', '').strip(),
                'LastInitial': parsed_name.get('LastInitial', '').strip(),
                'SuffixGenerational': parsed_name.get('SuffixGenerational', '').strip(),
                'SuffixOther': parsed_name.get('SuffixOther', '').strip(),
                'Nickname': parsed_name.get('Nickname', '').strip()
            }

            # If MiddleName is present but not MiddleInitial, derive MiddleInitial from MiddleName
            if parts['MiddleName'] and not parts['MiddleInitial']:
                parts['MiddleInitial'] = parts['MiddleName'][0]

            # Construct new name with or without SuffixGenerational
            new_name = f"{parts['Surname']}, {parts['GivenName']} {parts['MiddleInitial']}".strip()
            if parts['SuffixGenerational']:
                new_name = f"{new_name}, {parts['SuffixGenerational']}"

            logger.debug(f"{i()}✅ ✍️ Converted name: {new_name}")
            return new_name
        else:
            logger.debug(f"{i()}✅ ✍️ {name} read as a type of {name_type}")
            return name
    except pp.RepeatedLabelError as e:
        logger.error(f"{i()}🔹🚨🚩🌍📫〽️✍️🛑Error parsing name: {e}")
        logger.error(f"{i()}🔹🚨🚩🌍📫〽️✍️🛑Original String: {e.original_string}")
        logger.error(f"{i()}🔹🚨🚩🌍📫〽️✍️🛑Parsed String: {e.parsed_string}")
        logger.error(traceback.format_exc())
        return name


def extract_company_number_from_url(
    url: str = None
) -> Union[str, None]:
    """
    Extracts the company number from a given URL using regex.

    Parameters:
    ----------
    url : str, optional
        The URL from which to extract the company number. Defaults to gs.current_url.

    Returns:
    -------
    str or None
        The extracted company number, or None if no company number is found.

    This function takes a URL as input and extracts the company number from it using a regex pattern.
    It matches patterns like 'us_mo/00345772' or 'us_il/CORP_66442861' and extracts the company number part.

    Example usage:
    ----------
    url = "https://opencorporates.com/companies/us_mo/00345772"
    company_number = extract_company_number_from_url(url)
    print(company_number)  # Output: 00345772
    """
    try:
        url = ensure_url(url)
        # Define the regex pattern to match the company number
        pattern = re.compile(r'/companies/[a-zA-Z]{2}_[a-zA-Z]{2}/([^/]+)')

        # Search for the pattern in the URL
        match = pattern.search(url)

        if match:
            # Extract and return the company number
            company_number = match.group(1)
            logger.debug(f"{i()}🗃️🌎 Extracted company number: {company_number}")
            return company_number
        else:
            logger.debug(f"{i()}🗃️🌎 No company number found in URL: {url}")
            return None
    except Exception as e:
        logger.error(f"{i()}🛑🧺🚨 Error extracting company number from URL: {e}")
        logger.error(f"{traceback.format_exc()}")
        return None

def extract_jurisdiction_from_url(
    url: str = None
) -> Union[str, None]:
    """
    Extracts the jurisdiction from a given URL.

    Parameters:
    ----------
    url : str, optional
        The URL from which to extract the jurisdiction. Defaults to gs.current_url.

    Returns:
    -------
    str or None
        The extracted jurisdiction name, or None if no jurisdiction is found.

    This function takes a URL as input and extracts the jurisdiction from it. It splits the URL and matches the
    jurisdiction code (e.g., 'us_mo') to retrieve the corresponding jurisdiction name from the database.

    Example usage:
    ----------
    url = "https://opencorporates.com/companies/us_mo/00345772"
    jurisdiction = extract_jurisdiction_from_url(url)
    print(jurisdiction)  # Output: Missouri
    """
    try:
        url = ensure_url(url)
        # Extract the jurisdiction code from the URL
        jurisdiction_code = url.split('/')[4].lower()  # Extract 'us_**' part from the URL

        # Query the database for the jurisdiction name
        jurisdiction_record = gs.read.query(Jurisdiction).filter_by(code=jurisdiction_code).first()

        if jurisdiction_record:
            jurisdiction_name = jurisdiction_record.name
            logger.debug(f"{i()}🗃️🌎 Extracted jurisdiction: {jurisdiction_name}")
            return jurisdiction_name
        else:
            logger.debug(f"{i()}🗃️🌎 No jurisdiction found for code: {jurisdiction_code}")
            return None
    except Exception as e:
        logger.error(f"{i()}🛑🧺🚨 Error extracting jurisdiction from URL: {e}")
        logger.error(f"{traceback.format_exc()}")
        return None

def normalize_date(
    date_string
) -> Union[str, None]:
    """
    Normalizes various date formats to YYYY-MM-DD.

    Args:
        date_string (str): The date string to normalize.

    Returns:
        str: The normalized date in YYYY-MM-DD format, or None if parsing fails.
    """
    try:
        # Parse the date string
        parsed_date = dateparser.parse(date_string, settings={'PREFER_DAY_OF_MONTH': 'first', 'PREFER_DATES_FROM': 'past'})

        # If parsing is successful, return the formatted date
        if parsed_date:
            return parsed_date.strftime('%Y-%m-%d')
        else:
            return None
    except Exception as e:
        logger.error(f"{i()}🛑🧺🚨 Error normalizing date '{date_string}': {str(e)}")
        logger.error(f"{traceback.format_exc()}")
        return None



def determine_address_type(
    dt_text: str
) -> str:
    """
    Determines the address type based on the dt_text.

    Args:
        dt_text (str): The text of the dt element.

    Returns:
        str: The determined address type code.
    """
    dt_text_lower = dt_text.lower()
    address_types = AddressType.fetch_records(columns=['code', 'name'])
    for code, name in address_types:
        if name.lower() in dt_text_lower:
            return code
    return 'company'  # Default to company address if type is unclear
