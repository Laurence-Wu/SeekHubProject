from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import time
import os
import json
import sys
import uuid
from datetime import datetime
from bs4 import BeautifulSoup

# Add current directory to Python path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import configuration
from zlibraryCrowler.config import *

# Functions imported from local modules
from zlibraryCrowler.login import perform_login
from zlibraryCrowler.getSearchDownloadLinks import process_books_selenium_fallback
from zlibraryCrowler.getCookies import get_cookies_from_selenium

class BooklistScraper:
    def __init__(self):
        self.chrome_options = Options()
        if USE_HEADLESS_BROWSER:
            self.chrome_options.add_argument('--headless')
        
        # Add all Chrome options from config
        for option in CHROME_OPTIONS:
            self.chrome_options.add_argument(option)
        
        self.driver = webdriver.Chrome(options=self.chrome_options)
        self.wait = WebDriverWait(self.driver, BROWSER_TIMEOUT)
        self.booklists_url = f"{ZLIBRARY_BASE_URL}/booklists"
        
    def login(self):
        """Perform login to Z-Library"""
        return perform_login(self.driver, self.wait, COOKIES_FILE, EMAIL, PASSWORD)
    
    def get_booklist_elements(self):
        """Scrape all booklist elements from the booklists page"""
        try:
            print(f"Navigating to booklists page: {self.booklists_url}")
            self.driver.get(self.booklists_url)
            
            # Wait for the page to load
            time.sleep(3)
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all booklist content elements
            booklist_elements = soup.find_all('div', class_='content')
            
            print(f"Found {len(booklist_elements)} booklist elements")
            
            booklists_data = []
            
            for element in booklist_elements:
                try:
                    booklist_info = self.extract_booklist_info(element)
                    if booklist_info:
                        booklists_data.append(booklist_info)
                except Exception as e:
                    print(f"Error extracting booklist info: {e}")
                    continue
            
            return booklists_data
            
        except Exception as e:
            print(f"Error getting booklist elements: {e}")
            return []
    
    def extract_booklist_info(self, element):
        """Extract information from a single booklist element"""
        try:
            booklist_info = {}
            
            # Extract title and URL
            title_element = element.find('div', class_='title')
            if title_element:
                title_link = title_element.find('a')
                if title_link:
                    booklist_info['title'] = title_link.text.strip()
                    booklist_info['url'] = f"{ZLIBRARY_BASE_URL}{title_link.get('href')}"
                else:
                    return None
            else:
                return None
            
            # Extract author/creator information
            account_element = element.find('z-account')
            if account_element:
                booklist_info['creator'] = account_element.text.strip()
                booklist_info['creator_id'] = account_element.get('id')
                booklist_info['creator_url'] = f"{ZLIBRARY_BASE_URL}{account_element.get('href')}" if account_element.get('href') else None
            
            # Extract statistics
            info_blocks = element.find_all('div', class_='info-block')
            booklist_info['stats'] = {}
            
            for block in info_blocks:
                icon = block.find('span', class_='icon')
                value = block.find('span', class_='value')
                
                if icon and value:
                    if 'zlibicon-bookmark' in icon.get('class', []):
                        booklist_info['stats']['book_count'] = value.text.strip()
                    elif 'zlibicon-eye' in icon.get('class', []):
                        booklist_info['stats']['views'] = value.text.strip()
                    elif 'zlibicon-comment' in icon.get('class', []):
                        booklist_info['stats']['comments'] = value.text.strip()
            
            # Extract labels (like "Editor's Choice")
            label_element = element.find('div', class_='editors-choice-label')
            if label_element:
                booklist_info['label'] = label_element.text.strip()
            
            # Extract preview books from the carousel
            books_element = element.find('div', class_='books')
            if books_element:
                booklist_info['preview_books'] = self.extract_preview_books(books_element)
            
            return booklist_info
            
        except Exception as e:
            print(f"Error extracting booklist info from element: {e}")
            return None
    
    def extract_preview_books(self, books_element):
        """Extract preview books from the carousel"""
        preview_books = []
        
        try:
            # Find all z-cover elements
            covers = books_element.find_all('z-cover')
            
            for cover in covers:
                book_info = {
                    'id': cover.get('id'),
                    'title': cover.get('title'),
                    'author': cover.get('author'),
                    'url': None
                }
                
                # Get the parent link to extract URL
                parent_link = cover.find_parent('a')
                if parent_link:
                    book_info['url'] = f"{ZLIBRARY_BASE_URL}{parent_link.get('href')}"
                
                preview_books.append(book_info)
        
        except Exception as e:
            print(f"Error extracting preview books: {e}")
        
        return preview_books
    
    def scrape_full_booklist(self, booklist_url):
        """Scrape all books from a specific booklist"""
        try:
            print(f"Scraping full booklist: {booklist_url}")
            self.driver.get(booklist_url)
            
            # Wait for the page to load
            time.sleep(3)
            
            books = []
            page = 1
            
            while True:
                print(f"Scraping page {page} of booklist...")
                
                # Get page source and parse
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Find all book elements on the page
                book_elements = soup.find_all('z-bookcard')
                
                if not book_elements:
                    print(f"No books found on page {page}, ending...")
                    break
                
                print(f"Found {len(book_elements)} books on page {page}")
                
                # Extract book information
                for book_element in book_elements:
                    book_info = self.extract_book_info(book_element)
                    if book_info:
                        books.append(book_info)
                
                # Check if there's a next page
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 'a[rel="next"]')
                    if next_button and next_button.is_enabled():
                        next_button.click()
                        time.sleep(3)
                        page += 1
                    else:
                        break
                except:
                    print("No next page found, ending pagination...")
                    break
            
            return books
            
        except Exception as e:
            print(f"Error scraping full booklist: {e}")
            return []
    
    def extract_book_info(self, book_element):
        """Extract information from a single book element"""
        try:
            book_info = {
                'id': book_element.get('id'),
                'book_page_url': f"{ZLIBRARY_BASE_URL}{book_element.get('href')}" if book_element.get('href') else None,
                'title': None,
                'author': None,
                'language': book_element.get('language'),
                'file_type': book_element.get('extension'),
                'file_size': book_element.get('filesize'),
                'year': book_element.get('year'),
                'download_url': None,
                'download_links': []
            }
            
            # Extract title
            title_element = book_element.find('div', {"slot": "title"})
            if title_element:
                book_info['title'] = title_element.text.strip()
            
            # Extract author
            author_element = book_element.find('div', {"slot": "author"})
            if author_element:
                book_info['author'] = author_element.text.strip()
            
            return book_info
            
        except Exception as e:
            print(f"Error extracting book info: {e}")
            return None
    
    def get_download_links_for_books(self, books):
        """Get download links for all books using the existing method"""
        try:
            print(f"Extracting download links for {len(books)} books...")
            updated_books = process_books_selenium_fallback(self.driver, self.wait, books)
            return updated_books
        except Exception as e:
            print(f"Error getting download links: {e}")
            return books
    
    def save_booklist_data(self, booklist_info, books, output_dir="output/json"):
        """Save booklist data to JSON file"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename
            safe_title = "".join(c for c in booklist_info.get('title', 'unknown') if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"booklist_{safe_title}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # Prepare data structure
            output_data = {
                'booklist_info': booklist_info,
                'total_books': len(books),
                'books': books,
                'scraped_at': datetime.now().isoformat(),
                'scraper_version': '1.0'
            }
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=4)
            
            print(f"Saved booklist data to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error saving booklist data: {e}")
            return None
    
    def scrape_all_booklists(self, max_booklists=None, include_download_links=True):
        """Scrape all booklists and their books"""
        try:
            # Get all booklist elements
            booklists_data = self.get_booklist_elements()
            
            if not booklists_data:
                print("No booklists found!")
                return
            
            print(f"Found {len(booklists_data)} booklists to scrape")
            
            # Limit number of booklists if specified
            if max_booklists:
                booklists_data = booklists_data[:max_booklists]
                print(f"Limited to first {max_booklists} booklists")
            
            for i, booklist_info in enumerate(booklists_data, 1):
                try:
                    print(f"\n{'='*60}")
                    print(f"Processing booklist {i}/{len(booklists_data)}: {booklist_info.get('title', 'Unknown')}")
                    print(f"{'='*60}")
                    
                    # Scrape all books from this booklist
                    books = self.scrape_full_booklist(booklist_info['url'])
                    
                    if books:
                        print(f"Successfully scraped {len(books)} books from booklist")
                        
                        # Get download links if requested
                        if include_download_links and EXTRACT_DOWNLOAD_LINKS:
                            print("Extracting download links...")
                            books = self.get_download_links_for_books(books)
                            books_with_links = sum(1 for book in books if book.get('download_links'))
                            print(f"Successfully extracted download links for {books_with_links}/{len(books)} books")
                        
                        # Save the data
                        self.save_booklist_data(booklist_info, books)
                    else:
                        print(f"No books found in booklist: {booklist_info.get('title', 'Unknown')}")
                    
                    # Add delay between booklists
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"Error processing booklist {booklist_info.get('title', 'Unknown')}: {e}")
                    continue
        
        except Exception as e:
            print(f"Error in scrape_all_booklists: {e}")
    
    def close(self):
        """Close the browser"""
        try:
            time.sleep(BROWSER_SLEEP_TIME)
            self.driver.quit()
        except:
            pass


def main():
    """Main function to run the booklist scraper"""
    scraper = BooklistScraper()
    
    try:
        # Login to Z-Library
        print("Logging in to Z-Library...")
        login_successful = scraper.login()
        
        if not login_successful:
            print("Login failed! Cannot proceed.")
            return
        
        print("Login successful!")
        
        # Scrape all booklists
        # You can modify these parameters:
        # - max_booklists: Number of booklists to scrape (None for all)
        # - include_download_links: Whether to extract download links
        scraper.scrape_all_booklists(max_booklists=5, include_download_links=True)
        
        print("\n" + "="*60)
        print("BOOKLIST SCRAPING COMPLETED")
        print("="*60)
        print("Check the output/json folder for the generated files.")
        
    except Exception as e:
        print(f"Error in main: {e}")
    
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
