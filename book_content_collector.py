import os

import requests

from book_metadata_collector import (get_or_generate_book_id_to_language,
                                     get_or_generate_book_id_to_type)
from utils import load_pickle, save_pickle


def get_or_generate_book_id_to_path(book_id_to_type, book_id_to_language):
    """
    Loads or generates a dictionary mapping Gutenberg book IDs to their file paths.
    This ensures only English books of type 'Text' are included.

    Args:
        book_id_to_type (dict): Dictionary mapping book IDs to their types.
        book_id_to_language (dict): Dictionary mapping book IDs to their languages.

    Returns:
        dict: Dictionary mapping book IDs to file paths.
    """
    # Check if the mapping already exists in a stored pickle file
    if os.path.exists("data_dictionaries/book_id_to_path.pkl"):
        return load_pickle("data_dictionaries/book_id_to_path.pkl")

    book_ids_to_exclude = set()
    book_id_to_path = {}

    # Walk through the Project Gutenberg directory to find valid book files
    for root, _, files in os.walk("C:\\ProjectGutenberg"):
        for file in files:
            file_path = os.path.join(root, file)

            # Filter valid book files (English text books, not in 'old' directories)
            if file.endswith("-0.txt") and "old" not in file_path:
                try:
                    book_id = int(file.split("-0.txt")[0])
                except ValueError:
                    continue  # Skip files that do not have a numeric ID prefix

                # Ensure book meets criteria
                if book_id_to_type.get(book_id) == "Text" and book_id_to_language.get(book_id) == "en":
                    if book_id in book_id_to_path:
                        print(f"Duplicate book_id {book_id}")
                        book_ids_to_exclude.add(book_id)
                        del book_id_to_path[book_id]
                    elif book_id not in book_ids_to_exclude:
                        book_id_to_path[book_id] = file_path

    # Save the mapping to a pickle file for future use
    save_pickle(book_id_to_path, "data_dictionaries/book_id_to_path.pkl")
    return book_id_to_path


def copy_books_to_local_directory(book_id_to_path):
    """
    Copies relevant book files from the repository directory to a local directory.

    Args:
        book_id_to_path (dict): Dictionary mapping book IDs to repository file paths.

    Returns:
        list: List of book IDs that failed to copy (due to read or write errors).
    """
    problematic_book_ids = []

    for book_id, path in book_id_to_path.items():
        destination = os.path.join("books", f"{book_id}.txt")

        # Only copy if the book does not already exist in the local directory
        if not os.path.exists(destination):
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                with open(destination, "w", encoding="utf-8") as f:
                    f.write(text)
            except UnicodeDecodeError:
                problematic_book_ids.append(book_id)  # Log books with encoding issues

    return problematic_book_ids


def get_book_ids_to_download(book_id_to_type, book_id_to_language, existing_books):
    """
    Identifies book IDs that need to be downloaded from the Project Gutenberg website.

    Args:
        book_id_to_type (dict): Dictionary mapping book IDs to their types.
        book_id_to_language (dict): Dictionary mapping book IDs to their languages.
        existing_books (set): Set of book IDs already stored locally.

    Returns:
        list: List of book IDs to download.
    """
    return [
        book_id for book_id, book_type in book_id_to_type.items()
        if book_type == "Text" and book_id_to_language.get(book_id) == "en" and book_id not in existing_books
    ]


def delete_book(book_id):
    """
    Deletes a book entry from all metadata dictionaries.

    Args:
        book_id (int): Gutenberg book ID to remove.
    """
    metadata_files = [
        "book_id_to_type.pkl", "book_id_to_language.pkl", "book_id_to_name.pkl",
        "book_id_to_author.pkl", "book_id_to_year.pkl", "book_id_to_lccn.pkl",
        "book_id_to_wikipedia_url.pkl", "book_id_to_path.pkl"
    ]

    for file in metadata_files:
        metadata_dict = load_pickle(f"data_dictionaries/{file}")
        if book_id in metadata_dict:
            del metadata_dict[book_id]
            save_pickle(metadata_dict, f"data_dictionaries/{file}")


def download_books(book_ids_to_download):
    """
    Downloads books directly from Project Gutenberg and saves them locally.

    Args:
        book_ids_to_download (list): List of book IDs to download.
    """
    for book_id in book_ids_to_download:
        local_path = f"books/{book_id}.txt"
        if not os.path.exists(local_path):
            url = f"https://gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(local_path, "w", encoding="utf-8") as f:
                        f.write(response.text)
                elif response.status_code == 404:
                    print(f"Book {book_id} not found")
                    delete_book(book_id)  # Remove metadata for missing books
                else:
                    print(f"Failed to download book {book_id}: {response.status_code}")
            except Exception as e:
                print(f"Failed to download book {book_id}: {e}")


def main():
    """
    Main function to manage book metadata, identify missing books, and download required books.
    """
    # Load or generate book metadata
    book_id_to_type = get_or_generate_book_id_to_type()
    book_id_to_language = get_or_generate_book_id_to_language()
    book_id_to_path = get_or_generate_book_id_to_path(book_id_to_type, book_id_to_language)

    # Copy books to local storage and remove problematic files
    problematic_book_ids = copy_books_to_local_directory(book_id_to_path)
    for book_id in problematic_book_ids:
        del book_id_to_path[book_id]

    # Identify and download missing books
    book_ids_to_download = get_book_ids_to_download(book_id_to_type, book_id_to_language, book_id_to_path)
    download_books(book_ids_to_download)


if __name__ == "__main__":
    main()