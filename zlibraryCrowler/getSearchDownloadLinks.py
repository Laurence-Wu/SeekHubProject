# filepath: /Users/laurence/Library/CloudStorage/OneDrive-GeorgiaInstituteofTechnology/Mac/Desktop/Coding/SeekHubProject/zlibraryCrowler/getSearchDownloadLinks.py

import json
import asyncio
import aiohttp
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
from typing import List, Dict, Optional
from .config import ZLIBRARY_BASE_URL, USE_ASYNC_EXTRACTION, MAX_CONCURRENT_REQUESTS, get_output_filename

# Import cookie management functions
from .getCookies import get_cookies_from_selenium


async def fetch_page_content(session: aiohttp.ClientSession, url: str, cookies: dict = None) -> Optional[str]:
    """
    Fetch page content asynchronously using aiohttp.
    
    Args:
        session: aiohttp session
        url: URL to fetch
        cookies: Cookies to include with request
        
    Returns:
        Page content as string or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with session.get(url, headers=headers, cookies=cookies, timeout=30) as response:
            if response.status == 200:
                content = await response.text()
                return content
            else:
                print(f"Failed to fetch {url}: Status {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def extract_download_links_from_page(html_content: str, book_id: str) -> List[Dict[str, str]]:
    """
    Extract download links from a book page HTML content.
    
    Args:
        html_content: HTML content of the book page
        book_id: Book ID for reference
        
    Returns:
        List of download link dictionaries
    """
    download_links = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for the main download button first
        main_download_btn = soup.find('a', class_='addDownloadedBook')
        if main_download_btn:
            href = main_download_btn.get('href')
            if href:
                # Extract file format and size
                extension_elem = main_download_btn.find('span', class_='book-property__extension')
                extension = extension_elem.text.strip() if extension_elem else 'unknown'
                
                # Look for file size in the button text
                btn_text = main_download_btn.get_text()
                size = "unknown"
                if 'MB' in btn_text or 'KB' in btn_text or 'GB' in btn_text:
                    # Extract size using simple text parsing
                    parts = btn_text.split()
                    for i, part in enumerate(parts):
                        if part.endswith(('MB', 'KB', 'GB')):
                            if i > 0:
                                size = f"{parts[i-1]} {part}"
                            break
                
                download_links.append({
                    'format': extension.upper(),
                    'size': size,
                    'download_url': f"{ZLIBRARY_BASE_URL}{href}" if href.startswith('/') else href,
                    'type': 'primary'
                })
        
        # Look for dropdown menu with additional formats
        # Find all download links in dropdown menus
        dropdown_links = soup.find_all('a', {'data-book_id': book_id, 'class': 'addDownloadedBook'})
        
        for link in dropdown_links:
            href = link.get('href')
            if href and link != main_download_btn:  # Avoid duplicating main download
                # Extract format from the link
                extension_elem = link.find('b', class_='book-property__extension') or link.find('span', class_='book-property__extension')
                extension = extension_elem.text.strip() if extension_elem else 'unknown'
                
                # Extract size
                size_elem = link.find('span', class_='book-property__size')
                size = size_elem.text.strip() if size_elem else 'unknown'
                
                download_links.append({
                    'format': extension.upper(),
                    'size': size,
                    'download_url': f"{ZLIBRARY_BASE_URL}{href}" if href.startswith('/') else href,
                    'type': 'alternative'
                })
        
        # If no links found, try alternative selectors
        if not download_links:
            # Look for any download links with specific patterns
            all_download_links = soup.find_all('a', href=lambda href: href and '/dl/' in href)
            
            for link in all_download_links:
                href = link.get('href')
                if href:
                    # Try to extract format and size from link text or attributes
                    link_text = link.get_text()
                    extension = 'unknown'
                    size = 'unknown'
                    
                    # Look for format indicators
                    for fmt in ['epub', 'pdf', 'mobi', 'azw3', 'txt', 'fb2', 'rtf']:
                        if fmt.lower() in link_text.lower():
                            extension = fmt.upper()
                            break
                    
                    # Look for size indicators
                    if 'MB' in link_text or 'KB' in link_text or 'GB' in link_text:
                        parts = link_text.split()
                        for i, part in enumerate(parts):
                            if part.endswith(('MB', 'KB', 'GB')):
                                if i > 0:
                                    size = f"{parts[i-1]} {part}"
                                break
                    
                    download_links.append({
                        'format': extension,
                        'size': size,
                        'download_url': f"{ZLIBRARY_BASE_URL}{href}" if href.startswith('/') else href,
                        'type': 'detected'
                    })
        
    except Exception as e:
        print(f"Error extracting download links for book {book_id}: {e}")
    
    return download_links


def extract_download_links_selenium(driver, wait, book_url: str, book_id: str) -> List[Dict[str, str]]:
    """
    Extract download links using Selenium (for JavaScript-heavy pages).
    
    Args:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
        book_url: URL of the book page
        book_id: Book ID for reference
        
    Returns:
        List of download link dictionaries
    """
    download_links = []
    
    try:
        print(f"Fetching download links for book {book_id} using Selenium...")
        driver.get(book_url)
        
        # Wait for page to load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        # Look for the main download button
        try:
            main_download_btn = driver.find_element(By.CSS_SELECTOR, 'a.addDownloadedBook')
            href = main_download_btn.get_attribute('href')
            
            if href:
                # Extract format and size
                try:
                    extension_elem = main_download_btn.find_element(By.CSS_SELECTOR, '.book-property__extension')
                    extension = extension_elem.text.strip()
                except:
                    extension = 'unknown'
                
                btn_text = main_download_btn.text
                size = "unknown"
                if 'MB' in btn_text or 'KB' in btn_text or 'GB' in btn_text:
                    parts = btn_text.split()
                    for i, part in enumerate(parts):
                        if part.endswith(('MB', 'KB', 'GB')):
                            if i > 0:
                                size = f"{parts[i-1]} {part}"
                            break
                
                download_links.append({
                    'format': extension.upper(),
                    'size': size,
                    'download_url': href,
                    'type': 'primary'
                })
        except NoSuchElementException:
            print(f"Main download button not found for book {book_id}")
        
        # Try to click dropdown button to reveal more formats
        try:
            dropdown_btn = driver.find_element(By.ID, 'btnCheckOtherFormats')
            driver.execute_script("arguments[0].click();", dropdown_btn)
            
            # Wait for dropdown content to load
            time.sleep(2)
            
            # Look for additional download links in dropdown
            dropdown_links = driver.find_elements(By.CSS_SELECTOR, f'a[data-book_id="{book_id}"].addDownloadedBook')
            
            for link in dropdown_links:
                href = link.get_attribute('href')
                if href and href not in [dl['download_url'] for dl in download_links]:
                    # Extract format and size
                    try:
                        extension_elem = link.find_element(By.CSS_SELECTOR, 'b.book-property__extension, .book-property__extension')
                        extension = extension_elem.text.strip()
                    except:
                        extension = 'unknown'
                    
                    try:
                        size_elem = link.find_element(By.CSS_SELECTOR, '.book-property__size')
                        size = size_elem.text.strip()
                    except:
                        size = 'unknown'
                    
                    download_links.append({
                        'format': extension.upper(),
                        'size': size,
                        'download_url': href,
                        'type': 'alternative'
                    })
                    
        except NoSuchElementException:
            print(f"Dropdown button not found for book {book_id}")
        except Exception as e:
            print(f"Error clicking dropdown for book {book_id}: {e}")
        
    except Exception as e:
        print(f"Error extracting download links with Selenium for book {book_id}: {e}")
    
    return download_links


async def process_book_async(session: aiohttp.ClientSession, book: Dict, cookies: dict = None) -> Dict:
    """
    Process a single book to extract download links asynchronously.
    
    Args:
        session: aiohttp session
        book: Book dictionary
        cookies: Cookies for authentication
        
    Returns:
        Updated book dictionary with download links
    """
    book_url = book.get('book_page_url')
    book_id = book.get('id')
    
    if not book_url or not book_id:
        print(f"Missing URL or ID for book: {book.get('title', 'Unknown')}")
        return book
    
    print(f"Processing book: {book.get('title', 'Unknown')} (ID: {book_id})")
    
    # Fetch page content
    html_content = await fetch_page_content(session, book_url, cookies)
    
    if html_content:
        # Extract download links
        download_links = extract_download_links_from_page(html_content, book_id)
        
        # Update book with download links
        book['download_links'] = download_links
        
        # Set primary download URL if available
        primary_links = [link for link in download_links if link.get('type') == 'primary']
        if primary_links:
            book['download_url'] = primary_links[0]['download_url']
        elif download_links:
            book['download_url'] = download_links[0]['download_url']
        
        print(f"Found {len(download_links)} download links for book {book_id}")
    else:
        print(f"Failed to fetch content for book {book_id}")
    
    return book


async def process_books_async(books: List[Dict], cookies: dict = None, max_concurrent: int = 5) -> List[Dict]:
    """
    Process multiple books asynchronously to extract download links.
    
    Args:
        books: List of book dictionaries
        cookies: Cookies for authentication
        max_concurrent: Maximum number of concurrent requests
        
    Returns:
        List of updated book dictionaries
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_semaphore(session, book):
        async with semaphore:
            return await process_book_async(session, book, cookies)
    
    async with aiohttp.ClientSession() as session:
        tasks = [process_with_semaphore(session, book) for book in books]
        updated_books = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        result = []
        for i, book_result in enumerate(updated_books):
            if isinstance(book_result, Exception):
                print(f"Error processing book {i}: {book_result}")
                result.append(books[i])  # Return original book if processing failed
            else:
                result.append(book_result)
        
        return result


def process_books_selenium_fallback(driver, wait, books: List[Dict]) -> List[Dict]:
    """
    Process books using Selenium as fallback when async method fails.
    
    Args:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
        books: List of book dictionaries
        
    Returns:
        List of updated book dictionaries
    """
    updated_books = []
    
    for book in books:
        book_url = book.get('book_page_url')
        book_id = book.get('id')
        
        if not book_url or not book_id:
            print(f"Missing URL or ID for book: {book.get('title', 'Unknown')}")
            updated_books.append(book)
            continue
        
        print(f"Processing book with Selenium: {book.get('title', 'Unknown')} (ID: {book_id})")
        
        try:
            download_links = extract_download_links_selenium(driver, wait, book_url, book_id)
            
            # Update book with download links
            book['download_links'] = download_links
            
            # Set primary download URL if available
            primary_links = [link for link in download_links if link.get('type') == 'primary']
            if primary_links:
                book['download_url'] = primary_links[0]['download_url']
            elif download_links:
                book['download_url'] = download_links[0]['download_url']
            
            print(f"Found {len(download_links)} download links for book {book_id}")
            
        except Exception as e:
            print(f"Error processing book {book_id} with Selenium: {e}")
        
        updated_books.append(book)
        
        # Small delay to avoid overwhelming the server
        time.sleep(1)
    
    return updated_books


async def get_download_links_from_json(json_file_path: str, output_file_path: str = None, 
                                      use_selenium: bool = False, driver=None, wait=None,
                                      max_concurrent: int = 5) -> bool:
    """
    Main function to get download links from a JSON file containing book page links.
    
    Args:
        json_file_path: Path to the JSON file containing book data
        output_file_path: Path for the output file (defaults to input file with '__downloadLinks' suffix)
        use_selenium: Whether to use Selenium for processing
        driver: Selenium WebDriver instance (required if use_selenium=True)
        wait: WebDriverWait instance (required if use_selenium=True)
        max_concurrent: Maximum number of concurrent requests for async processing
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if file exists first
        if not os.path.exists(json_file_path):
            print(f"Error: JSON file not found: {json_file_path}")
            return False
        
        # Check if file is readable and has valid content
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                books = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in file {json_file_path}: {e}")
            return False
        except IOError as e:
            print(f"Error: Unable to read file {json_file_path}: {e}")
            return False
        
        if not isinstance(books, list):
            print(f"Error: Expected a list of books in {json_file_path}, got {type(books)}")
            return False
        
        if len(books) == 0:
            print(f"Warning: No books found in {json_file_path}")
            return True
        
        print(f"Loaded {len(books)} books from {json_file_path}")
        
        if use_selenium and driver and wait:
            # Use Selenium for processing
            print("Using Selenium for download link extraction...")
            updated_books = process_books_selenium_fallback(driver, wait, books)
        else:
            # Use async processing
            print("Using async processing for download link extraction...")
            cookies = {}
            if driver:
                cookies = get_cookies_from_selenium(driver)
            
            updated_books = await process_books_async(books, cookies, max_concurrent)
        
        # Determine output file path
        if not output_file_path:
            # Extract just the filename without directory path for base_name
            input_filename = os.path.basename(json_file_path)
            base_name = os.path.splitext(input_filename)[0]
            output_file_path = get_output_filename(f"{base_name}__downloadLinks").replace("_books.json", ".json")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        
        # Save updated books to JSON file
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_books, f, ensure_ascii=False, indent=4)
            print(f"Saved updated book data with download links to {output_file_path}")
        except IOError as e:
            print(f"Error saving output file {output_file_path}: {e}")
            return False
        
        # Print summary
        books__downloadLinks = sum(1 for book in updated_books if book.get('download_links'))
        print(f"Successfully extracted download links for {books__downloadLinks}/{len(updated_books)} books")
        
        return True
        
    except Exception as e:
        print(f"Error processing JSON file {json_file_path}: {e}")
        return False

def process_existing_json_with_download_links(driver, wait, json_file_path):
    """
    Process an existing JSON file to extract download links.
    
    Args:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance  
        json_file_path: Path to the JSON file to process
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Processing existing JSON file: {json_file_path}")
        
        # Check if file exists
        if not os.path.exists(json_file_path):
            print(f"File not found: {json_file_path}")
            return False
        
        # Load books from JSON
        with open(json_file_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
        
        print(f"Loaded {len(books)} books from {json_file_path}")
        
        # Check if books already have download links
        books_with_existing_links = sum(1 for book in books if book.get('download_links'))
        if books_with_existing_links == len(books):
            print("All books already have download links. Skipping extraction.")
            return True
        
        print(f"Found {books_with_existing_links} books with existing links, processing {len(books) - books_with_existing_links} remaining books...")
        
        # Try async method first if enabled
        if USE_ASYNC_EXTRACTION:
            try:
                print("Attempting async download link extraction...")
                cookies = get_cookies_from_selenium(driver)
                
                async def extract_links():
                    return await get_download_links_from_json(
                        json_file_path=json_file_path,
                        output_file_path=None,
                        use_selenium=False,
                        driver=driver,
                        wait=wait,
                        max_concurrent=MAX_CONCURRENT_REQUESTS
                    )
                
                success = asyncio.run(extract_links())
                
                if success:
                    print("Async extraction completed successfully!")
                    return True
                else:
                    print("Async method failed, trying Selenium fallback...")
                    
            except Exception as e:
                print(f"Async method error: {e}, trying Selenium fallback...")
        else:
            print("Async extraction disabled, using Selenium method...")
        
        # Fallback to Selenium method
        print("Using Selenium for download link extraction...")
        updated_books = process_books_selenium_fallback(driver, wait, books)
        
        # Save updated books
        input_filename = os.path.basename(json_file_path)
        base_name = os.path.splitext(input_filename)[0]
        output_filename = get_output_filename(f"{base_name}__downloadLinks").replace("_books.json", ".json")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(updated_books, f, ensure_ascii=False, indent=4)
            
            books__downloadLinks = sum(1 for book in updated_books if book.get('download_links'))
            print(f"Saved updated book data to {output_filename}")
            print(f"Successfully extracted download links for {books__downloadLinks}/{len(updated_books)} books")
        except IOError as e:
            print(f"Error saving output file {output_filename}: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error processing existing JSON file: {e}")
        return False
