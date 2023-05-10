import os
import time
import json
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import requests
import html2text

# Updated configuration
configs = [
    {
        "start_url": "https://www.law.cornell.edu/uscode/text",
        "selectors": [
            {"selector": '.tocitem a[href*="/uscode/"]', "action": "crawl"},
            {
                "selector": "#content .tab-content",
                "action": "content",
                "title-selector": "#page_title",
                "herarchy-selector": '.breadcrumb',
                "excluded-selector": ["#prevnext", "#tab_default_2"],
                "folder": "content",
            }
        ],
        "log_file": "log_uscode.txt",
    },
    # {
    #     "start_url": "https://www.ecfr.gov/",
    #     "selectors": [
    #         {"selector":'.table.title-list .title-number a[href*="/current/"]', "action": "crawl"},
    #         {"selector":'.table-of-contents a[href*="/current"]', "action": "crawl"},
    #         {"selector": 'li.developer-tools a[href*=".json"]', "action": "save", "folder": "downloads"},
    #         {"selector": 'li.developer-tools a[href*=".xml"]', "action": "save", "folder": "downloads"},
    #     ],
    #     "log_file": "log_ecfr.txt",
    # },
]

def log_visited_url(url, log_file):
    with open(log_file, "a") as log_file:
        log_file.write(f"{url}\n")

def is_url_visited(url, log_file):
    with open(log_file, "r") as log_file:
        return url in log_file.read()

def is_same_domain(url, domain):
    parsed_url = urlparse(url)
    return parsed_url.netloc == domain

def html_to_markdown(html):
    converter = html2text.HTML2Text()
    converter.ignore_links = True
    converter.ignore_images = True
    return converter.handle(html)

def extract_title(element, title_selector):
    title_element = element.find_elements(By.CSS_SELECTOR, title_selector)
    return title_element.text if title_element else ""

def remove_excluded_elements(element, excluded_selectors):
    for selector in excluded_selectors:
        for excluded_element in element.find_elements(By.CSS_SELECTOR, selector):
            driver.execute_script(
                "arguments[0].parentNode.removeChild(arguments[0]);", excluded_element
            )

def save_url_content(url, folder, config):
    response = requests.get(url)
    if response.status_code == 200:
        file_name = url.split("/")[-1]
        file_path = os.path.join(folder, file_name)
        with open(file_path, "wb") as file:
            file.write(response.content)
            log_visited_url(url, config["log_file"])

def save_content_to_json(element, config, folder):
    content = {
        "datetime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "selector": config["selector"],
        "title-selector": config.get("title-selector", ""),
        "herarchy-selector": config.get("herarchy-selector", ""),
        "excluded-selector": config.get("excluded-selector", []),
        "raw-content": element.get_attribute("innerHTML"),
        "title": "",
        "herarchy": "",
        "markdown": "",
    }

    if config.get("title-selector"):
        content["title"] = extract_title(element, config["title-selector"])

    if config.get("herarchy-selector"):
        herarchy_element = element.find_elements(By.CSS_SELECTOR, config["herarchy-selector"])
        content["herarchy"] = herarchy_element.text if herarchy_element else ""

    if config.get("excluded-selector"):
        remove_excluded_elements(element, config["excluded-selector"])
        content["raw-content"] = element.get_attribute("innerHTML")

    content["markdown"] = html_to_markdown(content["raw-content"])

    file_name = f"{urlparse(driver.current_url).path.strip('/').replace('/', '_')}.json"
    file_path = os.path.join(folder, file_name)

    with open(file_path, "w") as file:
        json.dump({driver.current_url: content}, file, indent=2)




def crawl(url, config):
    if is_url_visited(url, config["log_file"]):
        return

    domain = urlparse(config["start_url"]).netloc
    if not is_same_domain(url, domain):
        return

    log_visited_url(url, config["log_file"])
    driver.get(url)

    for selector_info in config["selectors"]:
        selector = selector_info["selector"]
        action = selector_info["action"]

        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        for element in elements:

            if action == "content":
                folder = selector_info.get("folder", "content")
                os.makedirs(folder, exist_ok=True)
                save_content_to_json(element, selector_info, folder)
            else:
                new_url = element.get_attribute("href")
                if new_url and not is_url_visited(new_url, config["log_file"]):
                    if action == "crawl":
                            crawl(new_url, config)
                    elif action == "save":
                        folder = selector_info.get("folder", "downloads")
                        os.makedirs(folder, exist_ok=True)
                        save_url_content(new_url, folder, config)

    time.sleep(1)

driver = webdriver.Chrome() # You can also use Chrome or other browsers

for config in configs:
    crawl(config["start_url"], config)

driver.quit()