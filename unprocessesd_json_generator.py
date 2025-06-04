from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import time
import os
import json
import asyncio
import sys

# Add current directory to Python path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import configuration
from zlibraryCrowler.config import *

# Functions imported from local modules
from zlibraryCrowler.textProcess import create_filtered_search_url
from zlibraryCrowler.login import perform_login
from zlibraryCrowler.search import search_and_extract_books
from zlibraryCrowler.getSearchDownloadLinks import get_download_links_from_json, process_books_selenium_fallback,process_existing_json_with_download_links
from zlibraryCrowler.getCookies import get_cookies_from_selenium

# # Print configuration summary
# print_config_summary()

chrome_options = Options()
chrome_options.add_argument('--headless')

# Add all Chrome options from config
for option in CHROME_OPTIONS:
    chrome_options.add_argument(option)

driver = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(driver, BROWSER_TIMEOUT)

# Perform login
login_successful = perform_login(driver, wait, COOKIES_FILE, EMAIL, PASSWORD)

if login_successful:
    # Navigate to the search page with configured parameters
    book_name_to_search = BOOK_NAME_TO_SEARCH
    
    # Define search preferences from configuration
    preferred_language = PREFERRED_LANGUAGE
    preferred_file_types = PREFERRED_FILE_TYPES
    include_fuzzy_matches = INCLUDE_FUZZY_MATCHES
    preferred_year = PREFERRED_YEAR
    
    # Create a filtered search URL
    search_url = create_filtered_search_url(
        book_name=book_name_to_search,
        website=ZLIBRARY_BASE_URL, 
        language=preferred_language,
        file_types=preferred_file_types,
        year = preferred_year
    )
    
    print(f"Using filtered search URL: {search_url}")
    
    # Set how many pages to scrape from configuration
    max_pages_to_scrape = MAX_PAGES_TO_SCRAPE
    
    search_success, book_data = search_and_extract_books(
        driver, 
        wait, 
        search_url, 
        book_name_to_search, 
        max_pages_to_scrape, 
        preferred_file_types,
        include_fuzzy_matches,
        cookies_file=COOKIES_FILE,
        email=EMAIL,
        password=PASSWORD
    )
    
    if search_success:
        print(f"Successfully extracted data for {len(book_data)} books related to '{book_name_to_search}' from {max_pages_to_scrape} pages.")
        
        # Generate JSON filename with search parameters
        json_filename = get_short_output_filename()
        
        print(f"Book data saved to: {json_filename}")
        
        # Extract download links if enabled
        if EXTRACT_DOWNLOAD_LINKS:
            print("Starting download link extraction...")
            
            # Extract download links using async method or Selenium fallback
            try:
                links_success = False

                # First try async method for better performance if enabled
                if USE_ASYNC_EXTRACTION:
                    print("Attempting async download link extraction...")
                    
                    # Get cookies from current Selenium session for authentication
                    cookies = get_cookies_from_selenium(driver)
                    
                    # Use async processing for download links
                    async def extract_links_async():
                        return await get_download_links_from_json(
                            json_file_path=json_filename,
                            output_file_path=None,  # Will auto-generate with '_downloadLinks' suffix
                            use_selenium=False,
                            driver=driver,
                            wait=wait,
                            max_concurrent=MAX_CONCURRENT_REQUESTS
                        )
                        
                    # Run async extraction
                    links_success = asyncio.run(extract_links_async())
                else:
                    print("Async extraction is disabled in configuration.")
                    links_success = False
                
                if not links_success:
                    print("Async method failed or disabled, falling back to Selenium method...")
                    # Fallback to Selenium method
                    print("Using Selenium for download link extraction...")
                    updated_books = process_books_selenium_fallback(driver, wait, book_data)
                    
                    # Save the updated books with download links
                    output_filename = get_short_output_filename("downloadLinks")
                    
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        json.dump(updated_books, f, ensure_ascii=False, indent=4)
                    
                    books_downloadLinks = sum(1 for book in updated_books if book.get('download_links'))
                    print(f"Saved updated book data with download links to {output_filename}")
                    print(f"Successfully extracted download links for {books_downloadLinks}/{len(updated_books)} books using Selenium")
                    links_success = True
                
                if links_success:
                    output_file = get_short_output_filename("downloadLinks")
                    print(f"\n{'='*60}")
                    print("DOWNLOAD LINK EXTRACTION COMPLETED")
                    print(f"{'='*60}")
                    print(f"Search query: {book_name_to_search}")
                    print(f"Language: {preferred_language}")
                    print(f"File types: {preferred_file_types}")
                    print(f"Total books found: {len(book_data)}")
                    print(f"Output file with links: {output_file}")

                    # Remove the original books file (without download links) after successful link extraction
                    books_json_to_remove = json_filename  # Use the original filename that was saved
                    if os.path.exists(books_json_to_remove):
                        try:
                            os.remove(books_json_to_remove)
                            print(f"🗑️ Removed original books file: {os.path.basename(books_json_to_remove)}")
                        except Exception as e:
                            print(f"❌ Error removing file {books_json_to_remove}: {e}")
                    else:
                        print(f"📄 Original books file not found to remove: {os.path.basename(books_json_to_remove)}")
                    print(f"{'='*60}")
                else:
                    print("❌ Download link extraction failed!")
                    
            except Exception as e:
                print(f"Error during download link extraction: {e}")
                print("Proceeding without download links...")
        else:
            print("Download link extraction is disabled in configuration.")
            
    else:
        print(f"Failed to extract book data for '{book_name_to_search}'.")
else:
    print("Login failed, cannot proceed with search.")

# Close the browser
time.sleep(BROWSER_SLEEP_TIME)  # Give a moment to see the final state
driver.quit()

# Print final result
if not login_successful:
    print("Process finished: Login failed!")
else:
    if 'search_success' in locals() and search_success:
        print("Process finished: Search and download link extraction completed!")
    else:
        print("Process finished: Search completed (download links may not have been extracted).")
