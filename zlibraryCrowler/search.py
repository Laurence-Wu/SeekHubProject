import json
import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup
from .config import ZLIBRARY_BASE_URL, PREFERRED_YEAR, MAX_PAGES_TO_SCRAPE, get_short_output_filename, SELECTORS, MAX_RETRIES, RETRY_DELAY
from .login import handle_login_session_loss, verify_login_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_and_extract_books(driver, wait, search_url, book_name_for_file, max_pages=1, preferred_file_types=None, include_fuzzy_matches=True, cookies_file=None, email=None, password=None):
    """
    Navigates to the search URL, extracts book information across multiple pages, and saves it to a JSON file.
    Enhanced with robust error handling and login session management.

    Args:
        driver: The Selenium WebDriver instance.
        wait: The Selenium WebDriverWait instance.
        search_url (str): The URL to perform the search on.
        book_name_for_file (str): The name of the book, used for naming the output JSON file.
        max_pages (int): The maximum number of pages to scrape. Default is 1.
        preferred_file_types (list): List of preferred file types. If provided, search terminates when encountering a non-matching type.
        include_fuzzy_matches (bool): If False, stops collecting books when fuzzy match warning is encountered. Default is True.
        cookies_file (str): Path to cookies file for re-login if needed.
        email (str): User email for re-login if needed.
        password (str): User password for re-login if needed.

    Returns:
        bool: True if search and extraction were successful, False otherwise.
        list: A list of dictionaries containing book data, or an empty list if an error occurs.
    """
    try:
        book_data = []
        current_page = 1
        base_url = search_url
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        logger.info(f"Starting search for '{book_name_for_file}' with max_pages={max_pages}")
        
        while current_page <= max_pages:
            page_success = False
            
            for attempt in range(MAX_RETRIES):
                try:
                    # Construct page URL (first page doesn't need page parameter)
                    if current_page == 1:
                        current_url = base_url
                    else:
                        # Check if URL already has query parameters
                        if len(preferred_file_types) != 0:
                            current_url = f"{base_url}&page={current_page}"
                        else:
                            current_url = f"{base_url}?page={current_page}"
                    
                    logger.info(f"Navigating to page {current_page} (attempt {attempt + 1}): {current_url}")
                    
                    # Navigate to the page
                    driver.get(current_url)
                    time.sleep(2)  # Allow page to load
                    
                    # Verify we're still logged in after navigation
                    if not verify_login_status(driver, timeout=5):
                        logger.warning(f"Login session lost on page {current_page}!")
                        
                        # Attempt to handle login session loss
                        if cookies_file and email and password:
                            if handle_login_session_loss(driver, wait, cookies_file, email, password):
                                logger.info("Successfully recovered from login session loss")
                                continue  # Retry this page
                            else:
                                logger.error("Failed to recover from login session loss")
                                return False, book_data
                        else:
                            logger.error("Cannot recover from login session loss - credentials not provided")
                            return False, book_data
                    
                    logger.info(f"Still logged in on page {current_page}!")
                    
                    # Wait for the search results to load with multiple strategies
                    try:
                        wait.until(
                            EC.any_of(
                                EC.presence_of_element_located((By.CLASS_NAME, 'book-item')),
                                EC.presence_of_element_located((By.CLASS_NAME, 'fuzzyMatchesLine')),
                                EC.presence_of_element_located((By.CLASS_NAME, 'no-results'))
                            )
                        )
                    except TimeoutException:
                        logger.warning(f"Timeout waiting for search results on page {current_page}, attempt {attempt + 1}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(RETRY_DELAY)
                            continue
                        else:
                            logger.error(f"No search results found on page {current_page} after {MAX_RETRIES} attempts")
                            break
                    
                    # Get the page source after search results are loaded
                    search_page_source = driver.page_source
                    
                    # Parse the page with BeautifulSoup
                    soup = BeautifulSoup(search_page_source, 'html.parser')

                    # Find all book items
                    book_items = soup.find_all('div', class_='book-item')
                    
                    if not book_items:
                        logger.info(f"No book items found on page {current_page}. This might be the last page.")
                        page_success = True  # Not an error, just no more results
                        break
                        
                    logger.info(f"Found {len(book_items)} potential book items on page {current_page} for '{book_name_for_file}'")
                    
                    # Check for fuzzy match warning element
                    fuzzy_match_element = soup.find('div', class_='fuzzyMatchesLine')
                    stop_after_this_page = False
                    
                    # If we don't want fuzzy matches and the element exists, we need to filter book items
                    if not include_fuzzy_matches and fuzzy_match_element:
                        # Find all book items before the fuzzy match warning
                        exact_match_items = []
                        for item in book_items:
                            # Check if this book item appears before the fuzzy match line in the HTML
                            fuzzy_match_position = str(soup).find(str(fuzzy_match_element))
                            item_position = str(soup).find(str(item))
                            
                            if item_position < fuzzy_match_position:
                                exact_match_items.append(item)
                            
                        logger.info(f"Fuzzy match warning found. Processing only {len(exact_match_items)} exact match items (excluding {len(book_items) - len(exact_match_items)} fuzzy matches).")
                        book_items_to_process = exact_match_items
                        stop_after_this_page = True
                    else:
                        if fuzzy_match_element:
                            logger.info(f"Fuzzy match warning found, but including fuzzy matches as requested.")
                        book_items_to_process = book_items

                    # Extract book information from the filtered book items
                    books_extracted_this_page = 0
                    for item in book_items_to_process:
                        try:
                            # Find the z-bookcard element
                            bookcard = item.find('z-bookcard')
                            if bookcard:
                                book_id = bookcard.get('id')
                                book_href = bookcard.get('href')
                                title_element = bookcard.find('div', {"slot": "title"})
                                title = title_element.text.strip() if title_element else "Unknown Title"
                                
                                author_element = bookcard.find('div', {"slot": "author"})
                                author = author_element.text.strip() if author_element else "Unknown Author"

                                # Get additional book information
                                language_element = bookcard.get('language')
                                extension_element = bookcard.get('extension')
                                filesize_element = bookcard.get('filesize')
                                
                                # Check if file type matches preferred types (if specified)
                                if preferred_file_types and extension_element:
                                    current_file_type = extension_element.upper()
                                    preferred_file_types_upper = [ft.upper() for ft in preferred_file_types]
                                    
                                    if current_file_type not in preferred_file_types_upper:
                                        logger.info(f"Found non-matching file type '{current_file_type}' for book '{title}'. Terminating search as requested.")
                                        logger.info(f"Preferred types: {preferred_file_types}, Found: {current_file_type}")
                                        # Save what we have so far before terminating
                                        if book_data:
                                            save_book_data(book_data)
                                        return True, book_data
                                
                                book_info = {
                                    'id': book_id,
                                    'title': title,
                                    'author': author,
                                    'language': language_element if language_element else "Unknown",
                                    'file_type': extension_element.upper() if extension_element else "Unknown",
                                    'file_size': filesize_element if filesize_element else "Unknown",
                                    'book_page_url': f"{ZLIBRARY_BASE_URL}{book_href}" if book_href else None,
                                    'download_url': None,
                                    'download_links': [] 
                                }
                                
                                book_data.append(book_info)
                                books_extracted_this_page += 1
                        except Exception as e:
                            logger.warning(f"Error extracting individual book info: {e}")
                    
                    logger.info(f"Successfully extracted {books_extracted_this_page} books from page {current_page}")
                    page_success = True
                    consecutive_failures = 0  # Reset failure counter on success
                    break  # Exit retry loop for this page
                    
                except WebDriverException as e:
                    logger.error(f"WebDriver error on page {current_page}, attempt {attempt + 1}: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                except Exception as e:
                    logger.error(f"Unexpected error on page {current_page}, attempt {attempt + 1}: {e}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
            
            # Check if page processing was successful
            if not page_success:
                consecutive_failures += 1
                logger.warning(f"Failed to process page {current_page} after {MAX_RETRIES} attempts. Consecutive failures: {consecutive_failures}")
                
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"Too many consecutive failures ({consecutive_failures}). Stopping search.")
                    break
            
            # If we found fuzzy matches and don't want to include them, stop pagination here
            if stop_after_this_page:
                logger.info("Stopping pagination due to fuzzy match detection and include_fuzzy_matches=False")
                break
            
            # Check if we've reached the end of results using proper termination indicators
            # Look for actual "no more results" or pagination end indicators
            try:
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                next_page_link = soup.find('a', href=lambda href: href and f'page={current_page + 1}' in href)
                
                if not next_page_link and current_page < max_pages:
                    logger.info(f"No next page link found on page {current_page}. This appears to be the last page.")
                    break
            except Exception as e:
                logger.warning(f"Error checking for next page link: {e}")
                
            # Move to the next page
            current_page += 1

        
        # Save the book data to a JSON file
        if book_data:
            save_book_data(book_data)
        else:
            logger.warning("No book data to save")
            
        logger.info(f"Search completed. Total books found: {len(book_data)}")
        return True, book_data
        
    except Exception as e:
        logger.error(f"Critical error during search and extraction for '{book_name_for_file}': {e}")
        # Save any data we managed to collect
        if book_data:
            save_book_data(book_data)
        return False, book_data


def save_book_data(book_data):
    """
    Safely save book data to JSON file with error handling.
    
    Args:
        book_data (list): List of book dictionaries to save.
    """
    try:
        output_filename = get_short_output_filename()
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(book_data, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Saved information for {len(book_data)} books to {output_filename}")
    except Exception as e:
        logger.error(f"Error saving book data: {e}")
        # Try alternative filename
        try:
            alternative_filename = f"emergency_book_data_{int(time.time())}.json"
            with open(alternative_filename, 'w', encoding='utf-8') as f:
                json.dump(book_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Saved book data to alternative file: {alternative_filename}")
        except Exception as alt_e:
            logger.error(f"Failed to save to alternative file: {alt_e}")
