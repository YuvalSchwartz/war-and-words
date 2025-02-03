import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from textblob import TextBlob
from tqdm import tqdm

from utils import load_pickle, save_pickle


def preprocess_book(book_text):
    """
    Preprocess the book text by removing the Project Gutenberg header and footer.

    Args:
        book_text (str): Original text of the book.

    Returns:
        str: Preprocessed book text.
    """
    # Regular expression to match the start of the book
    starting_pattern = r'(?s)\*\*\*\s?START OF TH(IS|E) PROJECT GUTENBERG EBOOK.*?\*\*\*'
    # Find the book starting match
    starting_match = re.search(starting_pattern, book_text)

    # Regular expression to match the end of the book
    ending_pattern = r'(?s)\*\*\*\s?END OF TH(IS|E) PROJECT GUTENBERG EBOOK.*?\*\*\*'
    # Find the book ending match
    ending_match = re.search(ending_pattern, book_text)

    # Extract the book content
    book_text = book_text[starting_match.end():ending_match.start()].lstrip('\n').rstrip()

    if book_text.startswith('This file was produced from images'):
        book_text = '\n'.join(book_text.split('\n')[1:]).lstrip('\n')

    small_print_ending_pattern = r'\*\s?END\s?\*THE SMALL PRINT! FOR PUBLIC DOMAIN ETEXTS.*\*\s?END\s?\*'
    small_print_ending_match = re.search(small_print_ending_pattern, book_text)
    if small_print_ending_match:
        book_text = book_text[small_print_ending_match.end():].lstrip('\n')

    possible_endings = ['End of the Project Gutenberg EBook of ', "End of Project Gutenberg's "]
    for possible_ending in possible_endings:
        ending_index = book_text.rfind(possible_ending)
        if ending_index != -1:
            book_text = book_text[:ending_index].rstrip()
            break

    return book_text


def get_polarity(book_id):
    """
    Get the sentiment polarity of a book.

    Args:
        book_id (int): Gutenberg book ID.

    Returns:
        float: Sentiment polarity of the book.
    """
    with open(f'books/{book_id}.txt', 'r', encoding='utf-8') as f:
        book_text = f.read()
    book_text = preprocess_book(book_text)
    blob = TextBlob(book_text)
    polarity = blob.sentiment.polarity

    return polarity


def get_or_generate_book_id_to_polarity():
    """
    Get or generate the dictionary mapping Gutenberg book IDs to sentiment polarities.

    Returns:
        dict: Dictionary mapping Gutenberg book IDs to sentiment polarities.
    """
    if os.path.exists("data_dictionaries/book_id_to_polarity.pkl"):
        book_id_to_polarity = load_pickle("data_dictionaries/book_id_to_polarity.pkl")
    else:
        book_id_to_polarity = {}

    return book_id_to_polarity


def main():
    """
    Main function to generate sentiment polarities for books.
    """
    book_id_to_polarity = get_or_generate_book_id_to_polarity()
    book_id_to_year = load_pickle('data_dictionaries/book_id_to_year.pkl')
    relevant_book_ids = [book_id for book_id, year in book_id_to_year.items() if year is not None and book_id not in book_id_to_polarity]
    total_tasks = len(relevant_book_ids)  # Total number of tasks for tqdm
    books_added = False
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(get_polarity, book_id): book_id for book_id in relevant_book_ids}

        # Wrap as_completed with tqdm to show progress
        for future in tqdm(as_completed(futures), total=total_tasks, desc="Processing book IDs"):
            book_id = futures[future]
            try:
                book_id_to_polarity[book_id] = future.result()
                books_added = True
            except Exception as e:
                print(f"Error processing book_id {book_id}: {e}")
    if books_added:
        save_pickle(book_id_to_polarity, "data_dictionaries/book_id_to_polarity.pkl")


if __name__ == '__main__':
    main()