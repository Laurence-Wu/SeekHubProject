#!/usr/bin/env python3
"""
Alternative configuration for testing without MongoDB
This version stores data in local JSON files instead of MongoDB
"""

# MongoDB settings (will be replaced with file storage)
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "gutenberg"
MONGO_COLLECTION = "books"
MONGO_PAIRS_COLLECTION = "translation_pairs"
MONGO_USERNAME = "user"
MONGO_PASSWORD = "123456.a"

# Alternative: File-based storage settings
USE_FILE_STORAGE = True
DATA_DIR = "data"
BOOKS_FILE = "books.json"
PAIRS_FILE = "translation_pairs.json"

TARGET_LANGUAGES = ["en", "zh"]

# Selenium WebDriver path (if not in PATH)
CHROME_DRIVER_PATH = None

# Base URL for Project Gutenberg
GUTENBERG_BASE_URL = "https://www.gutenberg.org"
GUTENBERG_SEARCH_URL = "https://www.gutenberg.org/ebooks/search/?query=&submit_search=Search&languages={lang}"

# Download settings
DOWNLOAD_DIR = "downloaded_books"
MAX_DOWNLOAD_THREADS = 5
MAX_TRANSLATION_PAIRS = 10
MAX_ENGLISH_SEARCH_PAGES_FOR_PAIRS = 10
