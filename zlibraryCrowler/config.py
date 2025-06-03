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
PREFERRED_YEAR = 2000 #set to zero to ignore year
PREFERRED_CONTENT_TYPES = ["book"]  # Options: ["book", "article"] or None for all
PREFERRED_ORDER = "bestmatch"  # Options: ["popular", "bestmatch", "newest", "oldest"] - corresponds to popularity, relevance, date desc, date asc
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
MAX_RETRIES = 5                # Maximum number of retries for failed requests
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

# Content type options
SUPPORTED_CONTENT_TYPES = ['book', 'article']

# Order options mapping to Z-Library parameters
SUPPORTED_ORDER_OPTIONS = {
    'popular': 'popular',
    'bestmatch': 'bestmatch', 
    'newest': 'newest',
    'oldest': 'oldest'
}

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
    
    # Validate content types
    if PREFERRED_CONTENT_TYPES:
        invalid_content_types = [ct for ct in PREFERRED_CONTENT_TYPES if ct.lower() not in SUPPORTED_CONTENT_TYPES]
        if invalid_content_types:
            errors.append(f"Invalid content types: {invalid_content_types}. Supported: {SUPPORTED_CONTENT_TYPES}")
    
    # Validate order option
    if PREFERRED_ORDER and PREFERRED_ORDER.lower() not in SUPPORTED_ORDER_OPTIONS:
        errors.append(f"Invalid order option: {PREFERRED_ORDER}. Supported: {list(SUPPORTED_ORDER_OPTIONS.keys())}")
    
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
    Only includes parameters that would actually appear in the URL.
    
    Returns:
        str: Search parameters string
    """
    params = [PROCESS_NAME]
    
    # Only add book name if it exists and is not None/empty
    if BOOK_NAME_TO_SEARCH:
        params.append(BOOK_NAME_TO_SEARCH)
    
    # Only add language if it's specified and not default/empty
    if PREFERRED_LANGUAGE:
        params.append(PREFERRED_LANGUAGE)
    
    # Only add file types if specified (not None or empty list)
    if PREFERRED_FILE_TYPES:
        file_types_str = '_'.join(PREFERRED_FILE_TYPES)
        params.append(file_types_str)
    
    # Only add content types if specified and not default
    if PREFERRED_CONTENT_TYPES:
        content_types_str = '_'.join(PREFERRED_CONTENT_TYPES)
        params.append(content_types_str)
    
    # Only add order if specified and not default
    if PREFERRED_ORDER:
        params.append(PREFERRED_ORDER)
    
    # Only add year if specified and greater than 0
    if PREFERRED_YEAR and PREFERRED_YEAR > 0:
        params.append(str(PREFERRED_YEAR))
    
    return '_'.join(params)

def get_output_filename(suffix=""):
    """
    Generate output filename based on search parameters.
    
    Args:
        suffix (str): Optional suffix to add to filename
        
    Returns:
        str: Complete output filename
    """
    # Get base name and clean it for filename use
    base_name = get_search_params_string().replace(' ', '_').replace('/', '_').replace('\\', '_')
    
    # Remove any problematic characters for filenames
    import re
    base_name = re.sub(r'[<>:"|?*]', '_', base_name)
    
    # Ensure the base name isn't too long (max 200 chars before extension)
    if len(base_name) > 200:
        base_name = base_name[:200]
    
    if suffix:
        return f"{OUTPUT_DIR}{base_name}_{suffix}.json"
    else:
        return f"{OUTPUT_DIR}{base_name}_books.json"

def get_short_output_filename(suffix=""):
    """
    Generate a shorter output filename for cases where full parameter string is too long.
    
    Args:
        suffix (str): Optional suffix to add to filename
        
    Returns:
        str: Complete output filename with shortened parameters
    """
    import hashlib
    
    # Create a hash of the full search parameters for uniqueness
    full_params = get_search_params_string()
    param_hash = hashlib.md5(full_params.encode()).hexdigest()[:8]
    
    # Build short name with only essential non-empty parameters
    short_parts = [PROCESS_NAME]
    
    # Add book name if exists (truncated)
    if BOOK_NAME_TO_SEARCH:
        book_name = BOOK_NAME_TO_SEARCH[:30]
        # Clean the book name for filename use
        import re
        book_name = re.sub(r'[<>:"|?*/\\]', '_', book_name)
        short_parts.append(book_name)
    
    # Add language if exists (truncated)
    if PREFERRED_LANGUAGE:
        language = PREFERRED_LANGUAGE[:10]
        short_parts.append(language)
    
    # Always add hash for uniqueness
    short_parts.append(param_hash)
    
    short_name = '_'.join(short_parts)
    
    if suffix:
        return f"{OUTPUT_DIR}{short_name}_{suffix}.json"
    else:
        return f"{OUTPUT_DIR}{short_name}_books.json"

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

def get_zlibrary_order_param():
    """
    Get the Z-Library order parameter value based on PREFERRED_ORDER.
    
    Returns:
        str: Z-Library order parameter value
    """
    return SUPPORTED_ORDER_OPTIONS.get(PREFERRED_ORDER.lower(), 'popular') if PREFERRED_ORDER else 'popular'

def get_content_types_param():
    """
    Get content types parameter for Z-Library URL formatting.
    
    Returns:
        list: List of content types for URL parameters
    """
    return PREFERRED_CONTENT_TYPES if PREFERRED_CONTENT_TYPES else ['book', 'article']

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
    print(f"Content Types: {PREFERRED_CONTENT_TYPES if PREFERRED_CONTENT_TYPES else 'All'}")
    print(f"Order: {PREFERRED_ORDER}")
    print(f"Preferred Year: {PREFERRED_YEAR if PREFERRED_YEAR > 0 else 'Any'}")
    print(f"Max Pages: {MAX_PAGES_TO_SCRAPE}")
    print(f"Fuzzy Matches: {'Included' if INCLUDE_FUZZY_MATCHES else 'Excluded'}")
    print(f"Download Links: {'Enabled' if EXTRACT_DOWNLOAD_LINKS else 'Disabled'}")
    print(f"Async Extraction: {'Enabled' if USE_ASYNC_EXTRACTION else 'Disabled'}")
    print(f"Max Concurrent: {MAX_CONCURRENT_REQUESTS}")
    print(f"Headless Browser: {'Yes' if USE_HEADLESS_BROWSER else 'No'}")
    print("="*60)

def update_preferred_year(new_year):
    import re
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'^PREFERRED_YEAR\s*=\s*\d+.*$'
        replacement = f'PREFERRED_YEAR = {new_year} #set to zero to ignore year'
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if new_content == content:
            return False
        
        with open(__file__, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        global PREFERRED_YEAR
        PREFERRED_YEAR = new_year
        return True
    except Exception:
        return False

def update_preferred_language(new_language):
    import re
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'^PREFERRED_LANGUAGE\s*=\s*["\'].*["\'].*$'
        replacement = f'PREFERRED_LANGUAGE = "{new_language}"'
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if new_content == content:
            return False
        
        with open(__file__, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        global PREFERRED_LANGUAGE
        PREFERRED_LANGUAGE = new_language
        return True
    except Exception:
        return False

def update_book_search_name(new_book_name):
    import re
    try:
        with open(__file__, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'^BOOK_NAME_TO_SEARCH\s*=\s*.*$'
        replacement = 'BOOK_NAME_TO_SEARCH = None' if new_book_name is None else f'BOOK_NAME_TO_SEARCH = "{new_book_name}"'
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if new_content == content:
            return False
        
        with open(__file__, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        global BOOK_NAME_TO_SEARCH
        BOOK_NAME_TO_SEARCH = new_book_name
        return True
    except Exception:
        return False
    
    # ============================================================================
    # DIRECTORY INITIALIZATION
    # ============================================================================
# Create output directories at import time
create_output_directories()