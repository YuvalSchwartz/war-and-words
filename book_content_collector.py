import os

import requests

from book_metadata_collector import get_or_generate_book_id_to_language, get_or_generate_book_id_to_type
from utils import load_pickle, save_pickle


def get_or_generate_book_id_to_path(book_id_to_type, book_id_to_language):
    if os.path.exists("book_id_to_path.pkl"):
        book_id_to_path = load_pickle("book_id_to_path.pkl")
    else:
        book_ids_to_exclude = set()
        book_id_to_path = {}
        for root, dirs, files in os.walk("C:\\ProjectGutenberg"):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith("-0.txt") and "old" not in file_path:
                    try:
                        book_id = int(file.split("-0.txt")[0])
                    except ValueError:
                        continue
                    if book_id_to_type[book_id] == "Text" and book_id_to_language[book_id] == "en":
                        if book_id in book_id_to_path:
                            print(f"Duplicate book_id {book_id}")
                            book_ids_to_exclude.add(book_id)
                            del book_id_to_path[book_id]
                        elif book_id not in book_ids_to_exclude:
                            book_id_to_path[book_id] = os.path.join(root, file)
        save_pickle(book_id_to_path, "book_id_to_path.pkl")
    return book_id_to_path


def copy_books_to_local_directory(book_id_to_path):
    problematic_book_ids = []
    for book_id, path in book_id_to_path.items():
        destination = os.path.join("books", f"{book_id}.txt")
        if not os.path.exists(destination):
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                with open(destination, "w", encoding="utf-8") as f:
                    f.write(text)
            except UnicodeDecodeError:
                problematic_book_ids.append(book_id)
    return problematic_book_ids


def get_book_ids_to_download(book_id_to_type, book_id_to_language, existing_books):
    books_to_download = []
    for book_id, book_type in book_id_to_type.items():
        if book_type == "Text" and book_id_to_language[book_id] == "en" and book_id not in existing_books:
            books_to_download.append(book_id)
    return books_to_download


def delete_book(book_id):
    book_id_to_type = load_pickle("book_id_to_type.pkl")
    if book_id in book_id_to_type:
        del book_id_to_type[book_id]
        save_pickle(book_id_to_type, "book_id_to_type.pkl")

    book_id_to_language = load_pickle("book_id_to_language.pkl")
    if book_id in book_id_to_language:
        del book_id_to_language[book_id]
        save_pickle(book_id_to_language, "book_id_to_language.pkl")

    book_id_to_name = load_pickle("book_id_to_name.pkl")
    if book_id in book_id_to_name:
        del book_id_to_name[book_id]
        save_pickle(book_id_to_name, "book_id_to_name.pkl")

    book_id_to_author = load_pickle("book_id_to_author.pkl")
    if book_id in book_id_to_author:
        del book_id_to_author[book_id]
        save_pickle(book_id_to_author, "book_id_to_author.pkl")

    book_id_to_year = load_pickle("book_id_to_year.pkl")
    if book_id in book_id_to_year:
        del book_id_to_year[book_id]
        save_pickle(book_id_to_year, "book_id_to_year.pkl")

    book_id_to_lccn = load_pickle("book_id_to_lccn.pkl")
    if book_id in book_id_to_lccn:
        del book_id_to_lccn[book_id]
        save_pickle(book_id_to_lccn, "book_id_to_lccn.pkl")

    book_id_to_wikipedia_url = load_pickle("book_id_to_wikipedia_url.pkl")
    if book_id in book_id_to_wikipedia_url:
        del book_id_to_wikipedia_url[book_id]
        save_pickle(book_id_to_wikipedia_url, "book_id_to_wikipedia_url.pkl")

    book_id_to_path = load_pickle("book_id_to_path.pkl")
    if book_id in book_id_to_path:
        del book_id_to_path[book_id]
        save_pickle(book_id_to_path, "book_id_to_path.pkl")


def download_books(book_ids_to_download):
    for book_id in book_ids_to_download:
        if not os.path.exists(f"books/{book_id}.txt"):
            url = f"https://gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(f"books/{book_id}.txt", "w", encoding="utf-8") as f:
                        f.write(response.text)
                elif response.status_code == 404:
                    print(f"Book {book_id} not found")
                    delete_book(book_id)
                else:
                    print(f"Failed to download book {book_id}: {response.status_code}")
            except Exception as e:
                print(f"Failed to download book {book_id}: {e}")


def main():
    book_id_to_type = get_or_generate_book_id_to_type()
    book_id_to_language = get_or_generate_book_id_to_language()
    book_id_to_path = get_or_generate_book_id_to_path(book_id_to_type, book_id_to_language)
    problematic_book_ids = copy_books_to_local_directory(book_id_to_path)
    for problematic_book_id in problematic_book_ids:
        del book_id_to_path[problematic_book_id]
    book_ids_to_download = get_book_ids_to_download(book_id_to_type, book_id_to_language, book_id_to_path)
    download_books(book_ids_to_download)


if __name__ == "__main__":
    main()