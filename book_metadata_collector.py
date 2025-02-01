import csv
import os
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import mwparserfromhell
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from utils import load_pickle, save_pickle


# Data source: https://www.gutenberg.org/cache/epub/feeds/
def get_or_generate_book_id_to_type():
    if os.path.exists("data_dictionaries/book_id_to_type.pkl"):
        book_id_to_type = load_pickle("data_dictionaries/book_id_to_type.pkl")
    else:
        # Initialize an empty dictionary
        book_id_to_type = {}

        # Read the CSV file
        with open('pg_catalog.csv', mode='r', newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                # Add key-value pairs to the dictionary
                book_id_to_type[int(row['Text#'])] = row['Type']

        # Save the dictionary to a pickle file
        save_pickle(book_id_to_type, "data_dictionaries/book_id_to_type.pkl")

    return book_id_to_type


# Data source: https://www.gutenberg.org/cache/epub/feeds/
def get_or_generate_book_id_to_language():
    if os.path.exists("data_dictionaries/book_id_to_language.pkl"):
        book_id_to_language = load_pickle("data_dictionaries/book_id_to_language.pkl")
    else:
        # Initialize an empty dictionary
        book_id_to_language = {}

        # Read the CSV file
        with open('pg_catalog.csv', mode='r', newline='', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                # Add key-value pairs to the dictionary
                book_id_to_language[int(row['Text#'])] = row['Language']

        # Save the dictionary to a pickle file
        save_pickle(book_id_to_language, "data_dictionaries/book_id_to_language.pkl")

    return book_id_to_language


def get_or_generate_book_id_to_name():
    if os.path.exists("data_dictionaries/book_id_to_name.pkl"):
        book_id_to_name = load_pickle("data_dictionaries/book_id_to_name.pkl")
    else:
        book_id_to_name = {}
    return book_id_to_name


def get_or_generate_book_id_to_author():
    if os.path.exists("data_dictionaries/book_id_to_author.pkl"):
        book_id_to_author = load_pickle("data_dictionaries/book_id_to_author.pkl")
    else:
        book_id_to_author = {}
    return book_id_to_author


def get_or_generate_book_id_to_wikipedia_url():
    if os.path.exists("data_dictionaries/book_id_to_wikipedia_url.pkl"):
        book_id_to_wikipedia_url = load_pickle("data_dictionaries/book_id_to_wikipedia_url.pkl")
    else:
        book_id_to_wikipedia_url = {}
    return book_id_to_wikipedia_url


def get_or_generate_book_id_to_lccn():
    if os.path.exists("data_dictionaries/book_id_to_lccn.pkl"):
        book_id_to_lccn = load_pickle("data_dictionaries/book_id_to_lccn.pkl")
    else:
        book_id_to_lccn = {}
    return book_id_to_lccn


def get_or_generate_book_id_to_year():
    if os.path.exists("data_dictionaries/book_id_to_year.pkl"):
        book_id_to_year = load_pickle("data_dictionaries/book_id_to_year.pkl")
    else:
        book_id_to_year = {}
    return book_id_to_year


def get_gutenberg_book_details(book_id):
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    driver.set_page_load_timeout(60)

    book_name = None
    book_author = None
    book_wikipedia_url = None
    book_lccn = None
    book_year = None
    try:
        driver.get(f'https://www.gutenberg.org/ebooks/{book_id}')

        content_div = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, "content")))
        title_div = content_div.find_element(By.TAG_NAME, 'h1')
        title = title_div.text
        splitted_title = title.split('by')
        name = splitted_title[0].rstrip()
        if name != 'No title':
            book_name = name
            if len(splitted_title) > 1:
                author = splitted_title[1].lstrip()
                if author != 'Anonymous' and author != 'Various' and author != 'Unknown':
                    book_author = author
            bibrec = content_div.find_element(By.ID, 'bibrec')
            trs = bibrec.find_elements(By.TAG_NAME, 'tr')
            for tr in trs:
                try:
                    th = tr.find_element(By.TAG_NAME, 'th')
                    th_text = th.text.strip()
                    if th_text == 'Note':
                        td = tr.find_element(By.TAG_NAME, 'td')
                        td_text = td.text.strip()
                        wikipedia_url_search = re.search(r'https://en.wikipedia.org/wiki/\S+', td_text)
                        if wikipedia_url_search:
                            book_wikipedia_url = wikipedia_url_search.group()
                    elif th_text == 'LoC No.':
                        td = tr.find_element(By.TAG_NAME, 'td')
                        td_text = td.text.strip()
                        book_lccn = td_text
                    elif th_text == 'Original Publication':
                        td = tr.find_element(By.TAG_NAME, 'td')
                        td_text = td.text.strip()
                        year_search = re.search(r'\b[12]\d{3}\b', td_text)
                        if year_search:
                            book_year = int(year_search.group())
                    if book_wikipedia_url and book_lccn and book_year:
                        break
                except NoSuchElementException:
                    # If <th> or <td> is not found, skip to the next row
                    continue
    finally:
        driver.quit()

    return book_name, book_author, book_wikipedia_url, book_lccn, book_year


def get_year_from_lccn(lccn):
    """
    Retrieves the publication year of a book using its Library of Congress Control Number (LCCN) via JSON.

    Args:
        lccn (str): The Library of Congress Control Number.

    Returns:
        int: The publication year, or None if not found.
    """
    # API URL for the LCCN with format=json
    url = f"https://www.loc.gov/item/{lccn}/?fo=json"

    try:
        # Make the API request
        response = requests.get(url)
        time.sleep(10)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            date = data['item']['date']
            year_search = re.search(r'\b[12]\d{3}\b', date)
            if year_search:
                return int(year_search.group())
    except Exception as e:
        print(f"Error retrieving publication year for {lccn}: {e}")

    return None


def get_year_from_wikipedia(wikipedia_url):
    """
    Extracts a publication year from a Wikipedia article.

    Args:
        wikipedia_url (str): The URL of the Wikipedia page.

    Returns:
        int or None: The extracted year, or None if not found.
    """
    # Wikipedia API endpoint (full page content)
    api_url = "https://en.wikipedia.org/w/api.php"

    # Wikimedia credentials
    WIKIMEDIA_ACCESS_TOKEN = os.getenv('WIKIMEDIA_ACCESS_TOKEN')
    WIKIMEDIA_APP_NAME = os.getenv('WIKIMEDIA_APP_NAME')
    WIKIMEDIA_EMAIL = os.getenv('WIKIMEDIA_EMAIL')

    # Headers for authentication
    headers = {
        "Authorization": f"Bearer {WIKIMEDIA_ACCESS_TOKEN}",
        "User-Agent": f"{WIKIMEDIA_APP_NAME} ({WIKIMEDIA_EMAIL})"
    }

    # Extract the title from the URL
    title_encoded = wikipedia_url.split('/')[-1]
    title_decoded = urllib.parse.unquote(title_encoded)
    title = title_decoded.replace('_', ' ')

    # Parameters for retrieving full page content
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main"
    }

    # Make the API request
    response = requests.get(api_url, headers=headers, params=params)
    time.sleep(10)

    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()

        # Extract the page content
        pages = data.get("query", {}).get("pages", {})
        for page_id, page_content in pages.items():
            if "revisions" in page_content:
                content = page_content["revisions"][0]["slots"]["main"]["*"]

                # Parse the content with mwparserfromhell
                wikicode = mwparserfromhell.parse(content)

                # 1. Check templates for certain keys
                for template in wikicode.filter_templates():
                    # Extract the publication year from the template
                    for param in template.params:
                        key = param.name.strip()
                        if key in {'release_date', 'date_created', 'pub_date', 'published'}:
                            year_search = re.search(r'\b[12]\d{3}\b', param.value.strip())
                            if year_search:
                                return int(year_search.group())

                # 2. Check templates for short description
                for template in wikicode.filter_templates():
                    if "Short description" in template.name.strip():
                        # Extract the publication year from the template
                        for param in template.params:
                            year_search = re.search(r'\b[12]\d{3}\b', param.value.strip())
                            if year_search:
                                return int(year_search.group())

                # 3. Check categories for year
                for category in wikicode.filter_wikilinks():
                    if category.title.startswith("Category:"):
                        year_search = re.search(r'\b[12]\d{3}\b', category.title[9:])
                        if year_search:
                            return int(year_search.group())

    # Return None if no year found
    return None


def process_book(book_id, book_id_to_type, book_id_to_language, book_id_to_name, book_id_to_author, book_id_to_wikipedia_url, book_id_to_lccn, book_id_to_year, lock):
    if book_id_to_type[book_id] != 'Text' or book_id_to_language[book_id] != 'en':
        return None  # Skip non-text or non-English books

    try:
        # Fetch name and author if not already present
        if book_id not in book_id_to_name or book_id not in book_id_to_author or book_id not in book_id_to_wikipedia_url or book_id not in book_id_to_lccn or book_id not in book_id_to_year:
            book_name, book_author, book_wikipedia_url, book_lccn, book_year = get_gutenberg_book_details(book_id)
            with lock:
                book_id_to_name[book_id] = book_name
                book_id_to_author[book_id] = book_author
                book_id_to_wikipedia_url[book_id] = book_wikipedia_url
                book_id_to_lccn[book_id] = book_lccn
                book_id_to_year[book_id] = book_year
        else:
            # book_name = book_id_to_name[book_id]
            # book_author = book_id_to_author[book_id]
            book_wikipedia_url = book_id_to_wikipedia_url[book_id]
            book_lccn = book_id_to_lccn[book_id]
            book_year = book_id_to_year[book_id]

        # Fetch publication year if not already present
        if book_year is None:
            if book_lccn:
                book_year = get_year_from_lccn(book_lccn)
            if book_year is None and book_wikipedia_url:
                book_year = get_year_from_wikipedia(book_wikipedia_url)
            if book_year:
                with lock:
                    book_id_to_year[book_id] = book_year
    except Exception as e:
        print(f"Error processing book {book_id}: {e}")
        return None

    return book_id


def main():
    # Load existing dictionaries
    book_id_to_type = get_or_generate_book_id_to_type()
    book_id_to_language = get_or_generate_book_id_to_language()
    book_id_to_name = get_or_generate_book_id_to_name()
    book_id_to_author = get_or_generate_book_id_to_author()
    book_id_to_wikipedia_url = get_or_generate_book_id_to_wikipedia_url()
    book_id_to_lccn = get_or_generate_book_id_to_lccn()
    book_id_to_year = get_or_generate_book_id_to_year()

    lock = Lock()  # To ensure thread-safe updates to dictionaries
    processed_count = 0  # Counter for saving progress

    # Multithreading
    # with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for book_id in book_id_to_language:
            futures.append(
                executor.submit(
                    process_book,
                    book_id,
                    book_id_to_type,
                    book_id_to_language,
                    book_id_to_name,
                    book_id_to_author,
                    book_id_to_wikipedia_url,
                    book_id_to_lccn,
                    book_id_to_year,
                    lock,
                )
            )

        for future in as_completed(futures):
            result = future.result()
            if result:
                processed_count += 1

                # Save progress every 10 books
                if processed_count % 10 == 0:
                    with lock:
                        save_pickle(book_id_to_name, "data_dictionaries/book_id_to_name.pkl")
                        save_pickle(book_id_to_author, "data_dictionaries/book_id_to_author.pkl")
                        save_pickle(book_id_to_wikipedia_url, "data_dictionaries/book_id_to_wikipedia_url.pkl")
                        save_pickle(book_id_to_lccn, "data_dictionaries/book_id_to_lccn.pkl")
                        save_pickle(book_id_to_year, "data_dictionaries/book_id_to_year.pkl")
                        print(f"Saved progress for {processed_count} books.")

    # Final save
    with lock:
        save_pickle(book_id_to_name, "data_dictionaries/book_id_to_name.pkl")
        save_pickle(book_id_to_author, "data_dictionaries/book_id_to_author.pkl")
        save_pickle(book_id_to_wikipedia_url, "data_dictionaries/book_id_to_wikipedia_url.pkl")
        save_pickle(book_id_to_lccn, "data_dictionaries/book_id_to_lccn.pkl")
        save_pickle(book_id_to_year, "data_dictionaries/book_id_to_year.pkl")
        print(f"Saved last progress ({processed_count} books).")


if __name__ == "__main__":
    load_dotenv()
    main()