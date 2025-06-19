MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "gutenberg"
MONGO_COLLECTION = "books"
MONGO_PAIRS_COLLECTION = "translation_pairs"
# Note: For a real application, the password should not be hardcoded.
# It's included here as per the user's specific request.
MONGO_USERNAME = "user" # Placeholder, will be used if authentication is set up on MongoDB
MONGO_PASSWORD = "123456.a" # As requested by the user

TARGET_LANGUAGES = ["en", "zh"] # English and Chinese

# Selenium WebDriver path (if not in PATH)
# Example: CHROME_DRIVER_PATH = "/path/to/chromedriver"
CHROME_DRIVER_PATH = None

# Base URL for Project Gutenberg
GUTENBERG_BASE_URL = "https://www.gutenberg.org"
GUTENBERG_SEARCH_URL = "https://www.gutenberg.org/ebooks/search/?query=&submit_search=Search&languages={lang}"

# Download settings
DOWNLOAD_DIR = "downloaded_books"
MAX_DOWNLOAD_THREADS = 5
MAX_TRANSLATION_PAIRS = 10 # Max pairs to find and download
MAX_ENGLISH_SEARCH_PAGES_FOR_PAIRS = 10 # Max pages of English books to check for authors
