import json
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from .config import ZLIBRARY_BASE_URL,PREFERRED_YEAR,MAX_PAGES_TO_SCRAPE,get_short_output_filename

def search_and_extract_books(driver, wait, search_url, book_name_for_file, max_pages=1, preferred_file_types=None, include_fuzzy_matches=True):
    """
    Navigates to the search URL, extracts book information across multiple pages, and saves it to a JSON file.

    Args:
        driver: The Selenium WebDriver instance.
        wait: The Selenium WebDriverWait instance.
        search_url (str): The URL to perform the search on.
        book_name_for_file (str): The name of the book, used for naming the output JSON file.
        max_pages (int): The maximum number of pages to scrape. Default is 1.
        preferred_file_types (list): List of preferred file types. If provided, search terminates when encountering a non-matching type.
        include_fuzzy_matches (bool): If False, stops collecting books when fuzzy match warning is encountered. Default is True.

    Returns:
        bool: True if search and extraction were successful, False otherwise.
        list: A list of dictionaries containing book data, or an empty list if an error occurs.
    """
    try:
        book_data = []
        current_page = 1
        base_url = search_url
        
        while current_page <= max_pages:
            # Construct page URL (first page doesn't need page parameter)
            if current_page == 1:
                current_url = base_url
            else:
                # Check if URL already has query parameters
                if len(preferred_file_types) != 0:
                    current_url = f"{base_url}&page={current_page}"
                else:
                    current_url = f"{base_url}?page={current_page}"
            print(f"Navigating to page {current_page}: {current_url}")
            
            driver.get(current_url)
            
            # Verify we're still logged in after navigation
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "logout")]'))
                )
                print(f"Still logged in on page {current_page}!")
            except Exception as login_err:
                print(f"WARNING: Login session may have been lost on page {current_page}! Error: {login_err}")
                # Depending on requirements, you might want to return False here or attempt re-login
                break
                
            # Wait for the search results to load
            try:
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CLASS_NAME, 'book-item')),
                        EC.presence_of_element_located((By.CLASS_NAME, 'fuzzyMatchesLine'))
                    )
                )
            except Exception as wait_err:
                print(f"No book items found on page {current_page}. This might be the last page. Error: {wait_err}")
                break
            
            # Get the page source after search results are loaded
            search_page_source = driver.page_source
            
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(search_page_source, 'html.parser')

            # Find all book items
            book_items = soup.find_all('div', class_='book-item')
            
            if not book_items:
                print(f"No book items found on page {current_page}. This might be the last page.")
                break
                
            print(f"Found {len(book_items)} potential book items on page {current_page} for '{book_name_for_file}'")
            
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
                    
                print(f"Fuzzy match warning found. Processing only {len(exact_match_items)} exact match items (excluding {len(book_items) - len(exact_match_items)} fuzzy matches).")
                book_items_to_process = exact_match_items
                stop_after_this_page = True
            else:
                if fuzzy_match_element:
                    print(f"Fuzzy match warning found, but including fuzzy matches as requested.")
                book_items_to_process = book_items

            # Extract book information from the filtered book items
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
                                print(f"Found non-matching file type '{current_file_type}' for book '{title}'. Terminating search as requested.")
                                print(f"Preferred types: {preferred_file_types}, Found: {current_file_type}")
                                # Save what we have so far before terminating
                                if book_data:
                                    output_filename = get_short_output_filename()
                                    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
                                    with open(output_filename, 'w', encoding='utf-8') as f:
                                        json.dump(book_data, f, ensure_ascii=False, indent=4)
                                    print(f"Program ends with {len(book_data)} books found before termination.")
                                    print(f"\nSaved information for {len(book_data)} books to {output_filename} before termination")
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
                except Exception as e:
                    print(f"Error extracting individual book info: {e}")
            
            # If we found fuzzy matches and don't want to include them, stop pagination here
            if stop_after_this_page:
                print("Stopping pagination due to fuzzy match detection and include_fuzzy_matches=False")
                break
            
            # Check if we've reached the end of results using proper termination indicators
            # Look for actual "no more results" or pagination end indicators
            next_page_link = soup.find('a', href=lambda href: href and f'page={current_page + 1}' in href)
            
            if not next_page_link and current_page < max_pages:
                print(f"No next page link found on page {current_page}. This appears to be the last page.")
                break
                
            # Move to the next page
            current_page += 1

        
        # Save the book data to a JSON file
        output_filename = get_short_output_filename()
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(book_data, f, ensure_ascii=False, indent=4)
        print(f"\nSaved information for {len(book_data)} books to {output_filename}")
        return True, book_data
        
    except Exception as e:
        print(f"Error during search and extraction for '{book_name_for_file}': {e}")
        return False, []
