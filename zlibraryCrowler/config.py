
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# AUTHENTICATION CONFIGURATION
# ============================================================================
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')
COOKIES_FILE = 'zlibrary_cookies.pkl'

# ============================================================================
# SEARCH CONFIGURATION
# ============================================================================
BOOK_NAME_TO_SEARCH = None
PREFERRED_LANGUAGE = "chinese"
PREFERRED_FILE_TYPES = ["EPUB","PDF"]  # Options: ["EPUB", "PDF", "MOBI", "AZW3", "TXT", "FB2", "RTF"] or None for all
PREFERRED_YEAR = 1800 #set to zero to ignore year
INCLUDE_FUZZY_MATCHES = False  # Set to False to exclude fuzzy matches
MAX_PAGES_TO_SCRAPE = 3

# Z-Library website base URL
ZLIBRARY_BASE_URL = "https://zh.z-lib.fm"

# ============================================================================
# DOWNLOAD LINK EXTRACTION CONFIGURATION
# ============================================================================
EXTRACT_DOWNLOAD_LINKS = True  # Set to False to skip download link extraction
USE_ASYNC_EXTRACTION = True    # Set to False to use Selenium method only
MAX_CONCURRENT_REQUESTS = 3    # Reduce if you get rate limited

# ============================================================================
# BROWSER CONFIGURATION
# ============================================================================
USE_HEADLESS_BROWSER = True    # Set to False to see browser window
BROWSER_TIMEOUT = 10           # Timeout for WebDriverWait
BROWSER_SLEEP_TIME = 2         # Sleep time before closing browser

# Browser options
CHROME_OPTIONS = [
    '--disable-gpu',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled'
]

# ============================================================================
# FILE AND OUTPUT CONFIGURATION
# ============================================================================
# Output folders for different types of data
OUTPUT_FOLDERS = {
    'json': './output/json/',           # For JSON search results
    'auth': './output/auth/',           # For passwords, emails, and cookies
    'downloads': './output/downloads/'  # For downloaded files
}

# Process name for downloaded file naming
PROCESS_NAME = "zlibrary_crawler"  # Downloaded files will be named with this prefix

# Output file naming pattern: {process_name}_{book_name}_{language}_{file_types}_books.json
OUTPUT_DIR = OUTPUT_FOLDERS['json']  # Default directory for backward compatibility
COOKIES_DIR = OUTPUT_FOLDERS['auth']  # Directory for cookies and auth data
DOWNLOADS_DIR = OUTPUT_FOLDERS['downloads']  # Directory for downloaded files

# ============================================================================
# RATE LIMITING AND PERFORMANCE
# ============================================================================
# Delays to avoid being detected as bot
REQUEST_DELAY = 1              # Delay between individual requests (seconds)
PAGE_LOAD_DELAY = 2            # Delay after page loads (seconds)
DROPDOWN_CLICK_DELAY = 2       # Delay after clicking dropdown (seconds)

# ============================================================================
# ADVANCED CONFIGURATION
# ============================================================================
# Retry configuration
MAX_RETRIES = 3                # Maximum number of retries for failed requests
RETRY_DELAY = 5                # Delay between retries (seconds)

# ============================================================================
# HTML SELECTORS AND PATTERNS (Advanced - modify with caution)
# ============================================================================
# CSS selectors for different elements on Z-Library pages
SELECTORS = {
    'book_item': 'div.book-item',
    'book_card': 'z-bookcard',
    'download_button': 'a.addDownloadedBook',
    'dropdown_button': '#btnCheckOtherFormats',
    'fuzzy_match_warning': 'div.fuzzyMatchesLine',
    'logout_link': '//a[contains(@href, "logout")]',
    'file_extension': '.book-property__extension',
    'file_size': '.book-property__size'
}

# URL patterns for download links
DOWNLOAD_URL_PATTERN = '/dl/'

# File format detection patterns
SUPPORTED_FORMATS = ['epub', 'pdf', 'mobi', 'azw3', 'txt', 'fb2', 'rtf']

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================
def validate_config():
    """
    Validate configuration settings and return any errors.
    
    Returns:
        list: List of validation error messages
    """
    errors = []
    
    # Check required environment variables
    if not EMAIL:
        errors.append("EMAIL environment variable is not set")
    if not PASSWORD:
        errors.append("PASSWORD environment variable is not set")
    
    # Validate file types
    if PREFERRED_FILE_TYPES:
        invalid_types = [ft for ft in PREFERRED_FILE_TYPES if ft.lower() not in SUPPORTED_FORMATS]
        if invalid_types:
            errors.append(f"Invalid file types: {invalid_types}. Supported: {SUPPORTED_FORMATS}")
    
    # Validate numeric values
    if MAX_PAGES_TO_SCRAPE <= 0:
        errors.append("MAX_PAGES_TO_SCRAPE must be greater than 0")
    if MAX_CONCURRENT_REQUESTS <= 0:
        errors.append("MAX_CONCURRENT_REQUESTS must be greater than 0")
    if BROWSER_TIMEOUT <= 0:
        errors.append("BROWSER_TIMEOUT must be greater than 0")
    
    return errors

def get_search_params_string():
    """
    Generate a string representation of search parameters for file naming.
    
    Returns:
        str: Search parameters string
    """
    file_types_str = '_'.join(PREFERRED_FILE_TYPES) if PREFERRED_FILE_TYPES else 'all'
    return f"{PROCESS_NAME}_{BOOK_NAME_TO_SEARCH}_{PREFERRED_LANGUAGE}_{file_types_str}"

def get_output_filename(suffix=""):
    """
    Generate output filename based on search parameters.
    
    Args:
        suffix (str): Optional suffix to add to filename
        
    Returns:
        str: Complete output filename
    """
    base_name = get_search_params_string().replace(' ', '_')
    if suffix:
        return f"{OUTPUT_DIR}{base_name}_{suffix}.json"
    else:
        return f"{OUTPUT_DIR}{base_name}_books.json"

def get_download_filename(original_filename):
    """
    Generate download filename with process name prefix.
    
    Args:
        original_filename (str): Original filename from download
        
    Returns:
        str: Complete download filename with path
    """
    # Extract file extension
    name, ext = os.path.splitext(original_filename)
    # Create new filename with process name prefix
    new_filename = f"{PROCESS_NAME}_{name}{ext}"
    return f"{DOWNLOADS_DIR}{new_filename}"

def get_cookies_filepath():
    """
    Get the full path for cookies file in auth directory.
    
    Returns:
        str: Complete cookies file path
    """
    return f"{COOKIES_DIR}{COOKIES_FILE}"

def create_output_directories():
    """
    Create all necessary output directories if they don't exist.
    
    Returns:
        bool: True if all directories were created/exist, False otherwise
    """
    try:
        for folder_type, folder_path in OUTPUT_FOLDERS.items():
            os.makedirs(folder_path, exist_ok=True)
            print(f"Created/verified {folder_type} directory: {folder_path}")
        return True
    except Exception as e:
        print(f"Error creating output directories: {e}")
        return False

# ============================================================================
# CONFIGURATION SUMMARY
# ============================================================================
def print_config_summary():
    """Print a summary of current configuration settings."""
    print("="*60)
    print("CONFIGURATION SUMMARY")
    print("="*60)
    print(f"Search Query: {BOOK_NAME_TO_SEARCH}")
    print(f"Language: {PREFERRED_LANGUAGE}")
    print(f"File Types: {PREFERRED_FILE_TYPES if PREFERRED_FILE_TYPES else 'All'}")
    print(f"Max Pages: {MAX_PAGES_TO_SCRAPE}")
    print(f"Fuzzy Matches: {'Included' if INCLUDE_FUZZY_MATCHES else 'Excluded'}")
    print(f"Download Links: {'Enabled' if EXTRACT_DOWNLOAD_LINKS else 'Disabled'}")
    print(f"Async Extraction: {'Enabled' if USE_ASYNC_EXTRACTION else 'Disabled'}")
    print(f"Max Concurrent: {MAX_CONCURRENT_REQUESTS}")
    print(f"Headless Browser: {'Yes' if USE_HEADLESS_BROWSER else 'No'}")
    print("="*60)



    # ============================================================================
    # DIRECTORY INITIALIZATION
    # ============================================================================
# Create output directories at import time
create_output_directories()