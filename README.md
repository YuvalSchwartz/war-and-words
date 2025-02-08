# War and Words: The Impact of WWI on Sentiment in Literature

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Overview
This project investigates historical sentiment trends in literature, focusing on how World War I influenced literary emotional tones. It combines metadata extraction, book content processing, and sentiment analysis on books from Project Gutenberg.

The research pipeline consists of:
1. **Metadata Extraction**: Retrieving publication years from multiple sources (Project Gutenberg, Library of Congress, Wikipedia).
2. **Book Content Collection**: Downloading full-text books from Project Gutenberg.
3. **Sentiment Analysis**: Computing sentiment polarity scores for each book.
4. **Statistical Analysis & Visualization**: Using preprocessed datasets to analyze sentiment shifts and generate visualizations.

## Repository Structure
- **`book_metadata_collector.py`** - Extracts publication years for books from Project Gutenberg using metadata from the Library of Congress and Wikipedia.
- **`book_content_collector.py`** - Downloads and processes full-text books from Project Gutenberg.
- **`sentiment_analyzer.py`** - Computes sentiment polarity scores for books.
- **`main.py`** - Uses precomputed metadata and sentiment data to generate the final dataset, conduct statistical analysis, and produce visualizations.
- **`utils.py`** - Utility functions for data storage, retrieval, and processing.

## Installation & Setup

### 1. Install Dependencies
Use the provided `requirements.txt` file to install all necessary packages:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Ensure you have a `.env` file in the project directory containing the following keys for Wikipedia API access:
```
WIKIMEDIA_ACCESS_TOKEN=<your_token>
WIKIMEDIA_APP_NAME=<your_app_name>
WIKIMEDIA_EMAIL=<your_email>
```
Replace `<your_token>`, `<your_app_name>`, and `<your_email>` with your actual credentials.

## Running the Project

### 1. Extract Metadata (Run Once)
To collect publication years from various sources and generate metadata files:
```bash
python book_metadata_collector.py
```

### 2. Collect Book Content (Run Once)
To download and clean full-text books from Project Gutenberg:
```bash
python book_content_collector.py
```

### 3. Perform Sentiment Analysis (Run Once)
To compute sentiment polarity scores for the collected books:
```bash
python sentiment_analyzer.py
```

### 4. Generate Dataset, Perform Statistical Analysis & Visualization
Once the metadata and sentiment analysis are precomputed, run:
```bash
python main.py
```
This script loads the precomputed data dictionaries to:
- Generate the final dataset.
- Conduct statistical tests (ANOVA, t-tests) on sentiment trends.
- Produce sentiment trend visualizations.

## License
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.
