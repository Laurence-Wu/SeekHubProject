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

class ZLibraryBooklistScraper:
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
    
    def scrape_booklists_page(self):
        """Scrape the main booklists page to get all booklist URLs"""
        try:
            print(f"Navigating to booklists page: {self.booklists_url}")
            self.driver.get(self.booklists_url)
            
            # Wait for the page to load and z-booklist elements to be ready
            time.sleep(5)  # Give extra time for dynamic content to load
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find all z-booklist elements (the actual structure used by Z-Library)
            booklist_elements = soup.find_all('z-booklist')
            
            print(f"Found {len(booklist_elements)} z-booklist elements")
            
            booklists = []
            
            for element in booklist_elements:
                try:
                    booklist_data = self.parse_z_booklist_element(element)
                    if booklist_data:
                        booklists.append(booklist_data)
                except Exception as e:
                    print(f"Error parsing z-booklist element: {e}")
                    continue
            
            return booklists
            
        except Exception as e:
            print(f"Error scraping booklists page: {e}")
            return []
    
    def parse_z_booklist_element(self, element):
        """Parse a z-booklist element to extract metadata and booklist URL"""
        try:
            booklist_data = {
                'booklist_id': element.get('id'),
                'title': element.get('topic'),
                'url': f"{ZLIBRARY_BASE_URL}{element.get('href')}" if element.get('href') else None,
                'creator': {
                    'name': element.get('author'),
                    'profile_url': f"{ZLIBRARY_BASE_URL}{element.get('authorprofile')}" if element.get('authorprofile') else None,
                    'avatar_url': element.get('authoravatar') if element.get('authoravatar') else None
                },
                'stats': {
                    'book_count': element.get('quantity'),
                    'views': element.get('views'),
                    'comments': element.get('comments')
                },
                'description': element.get('description', ''),
                'color': element.get('color'),
                'is_favorite': element.get('favorite') is not None,
                'is_editors_choice': element.get('editorschoice') is not None
            }
            
            # Extract preview books from within the z-booklist element
            booklist_data['preview_books'] = self.extract_preview_books_from_z_booklist(element)
            
            return booklist_data
            
        except Exception as e:
            print(f"Error parsing z-booklist element: {e}")
            return None

    def extract_preview_books_from_z_booklist(self, element):
        """Extract preview books from within a z-booklist element"""
        preview_books = []
        
        try:
            # Find all z-cover elements within this z-booklist
            z_covers = element.find_all('z-cover')
            
            for cover in z_covers:
                book_preview = {
                    'id': cover.get('id'),
                    'title': cover.get('title'),
                    'author': cover.get('author'),
                    'book_url': None
                }
                
                # Get the parent <a> tag to extract the book URL
                parent_link = cover.find_parent('a')
                if parent_link and parent_link.get('href'):
                    book_preview['book_url'] = f"{ZLIBRARY_BASE_URL}{parent_link.get('href')}"
                
                preview_books.append(book_preview)
        
        except Exception as e:
            print(f"Error extracting preview books from z-booklist: {e}")
        
        return preview_books

    def parse_booklist_div(self, div):
        """Parse a single booklist div to extract metadata and booklist URL (legacy method)"""
        try:
            booklist_data = {}
            
            # Extract editor's choice label if present
            label_element = div.find('div', class_='editors-choice-label')
            if label_element:
                booklist_data['label'] = label_element.text.strip()
            
            # Extract title and URL
            title_div = div.find('div', class_='title')
            if title_div:
                title_link = title_div.find('a')
                if title_link:
                    booklist_data['title'] = title_link.text.strip()
                    booklist_data['url'] = f"{ZLIBRARY_BASE_URL}{title_link.get('href')}"
                    # Extract booklist ID from URL
                    href = title_link.get('href')
                    if href and '/booklist/' in href:
                        # Extract ID from URL like /booklist/27086/cc3f23/101-books.html
                        parts = href.split('/booklist/')[1].split('/')
                        if parts:
                            booklist_data['booklist_id'] = parts[0]
                else:
                    return None
            else:
                return None
            
            # Extract creator information
            account_element = div.find('z-account')
            if account_element:
                booklist_data['creator'] = {
                    'name': account_element.text.strip(),
                    'id': account_element.get('id'),
                    'profile_url': f"{ZLIBRARY_BASE_URL}{account_element.get('href')}" if account_element.get('href') else None
                }
            
            # Extract statistics (book count, views, comments)
            stats = {}
            info_blocks = div.find_all('div', class_='info-block')
            
            for block in info_blocks:
                icon_span = block.find('span', class_='icon')
                value_span = block.find('span', class_='value')
                
                if icon_span and value_span:
                    icon_classes = icon_span.get('class', [])
                    value = value_span.text.strip()
                    
                    if 'zlibicon-bookmark' in icon_classes:
                        stats['book_count'] = value
                    elif 'zlibicon-eye' in icon_classes:
                        stats['views'] = value
                    elif 'zlibicon-comment' in icon_classes:
                        stats['comments'] = value
            
            booklist_data['stats'] = stats
            
            # Extract preview books from the carousel
            books_div = div.find('div', class_='books')
            if books_div:
                booklist_data['preview_books'] = self.extract_preview_books_from_carousel(books_div)
            
            return booklist_data
            
        except Exception as e:
            print(f"Error parsing booklist div: {e}")
            return None
    
    def extract_preview_books_from_carousel(self, books_div):
        """Extract preview books from the z-carousel"""
        preview_books = []
        
        try:
            # Find all z-cover elements within the carousel
            z_covers = books_div.find_all('z-cover')
            
            for cover in z_covers:
                book_preview = {
                    'id': cover.get('id'),
                    'title': cover.get('title'),
                    'author': cover.get('author'),
                    'book_url': None
                }
                
                # Get the parent <a> tag to extract the book URL
                parent_link = cover.find_parent('a')
                if parent_link and parent_link.get('href'):
                    book_preview['book_url'] = f"{ZLIBRARY_BASE_URL}{parent_link.get('href')}"
                
                preview_books.append(book_preview)
        
        except Exception as e:
            print(f"Error extracting preview books: {e}")
        
        return preview_books
    
    def scrape_individual_booklist(self, booklist_url, booklist_title="Unknown"):
        """Scrape all books from an individual booklist page"""
        try:
            print(f"Scraping booklist: {booklist_title}")
            print(f"URL: {booklist_url}")
            
            self.driver.get(booklist_url)
            time.sleep(3)
            
            all_books = []
            page_num = 1
            
            while True:
                try:
                    print(f"Scraping page {page_num}...")
                    
                    # Get page source
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    
                    # Find all book elements (they might be in different formats)
                    # Look for z-bookcard elements first
                    book_elements = soup.find_all('z-bookcard')
                    
                    # If no z-bookcard found, look for other book item patterns
                    if not book_elements:
                        book_elements = soup.find_all('div', class_='book-item')
                    
                    if not book_elements:
                        print(f"No book elements found on page {page_num}")
                        break
                    
                    print(f"Found {len(book_elements)} books on page {page_num}")
                    
                    # Extract book information
                    for book_element in book_elements:
                        book_info = self.extract_book_from_Element(book_element)
                        if book_info:
                            all_books.append(book_info)
                    
                    # Check for next page
                    try:
                        # Look for pagination links
                        next_link = soup.find('a', {'rel': 'next'})
                        if next_link and next_link.get('href'):
                            next_url = f"{ZLIBRARY_BASE_URL}{next_link.get('href')}"
                            self.driver.get(next_url)
                            time.sleep(3)
                            page_num += 1
                        else:
                            print("No next page found")
                            break
                    except Exception as e:
                        print(f"Error checking for next page: {e}")
                        break
                
                except Exception as e:
                    print(f"Error scraping page {page_num}: {e}")
                    break
            
            print(f"Total books extracted from '{booklist_title}': {len(all_books)}")
            return all_books
            
        except Exception as e:
            print(f"Error scraping individual booklist: {e}")
            return []
    
    def extract_book_from_Element(self, element):
        """Extract book information from a book element"""
        try:
            book_info = {}
            
            # Handle z-bookcard elements (the actual structure used by Z-Library)
            if element.name == 'z-bookcard':
                book_info = {
                    'id': element.get('id'),
                    'isbn': element.get('isbn'),
                    'title': None,
                    'author': None,
                    'language': element.get('language'),
                    'file_type': element.get('extension', '').upper() if element.get('extension') else None,
                    'file_size': element.get('filesize'),
                    'year': element.get('year'),
                    'book_page_url': f"{ZLIBRARY_BASE_URL}{element.get('href')}" if element.get('href') else None,
                    'download_url': f"{ZLIBRARY_BASE_URL}{element.get('download')}" if element.get('download') else None,
                    'download_links': [f"{ZLIBRARY_BASE_URL}{element.get('download')}"] if element.get('download') else [],
                    'read_url': element.get('read'),
                    'deleted': element.get('deleted') == '1' if element.get('deleted') else False
                }
                
                # Extract title from slot
                title_slot = element.find('div', {'slot': 'title'})
                if title_slot:
                    book_info['title'] = title_slot.text.strip()
                
                # Extract author from slot  
                author_slot = element.find('div', {'slot': 'author'})
                if author_slot:
                    book_info['author'] = author_slot.text.strip()
                
                # If title or author is still None, try to get from attributes
                if not book_info['title']:
                    book_info['title'] = element.get('title', 'Unknown Title')
                if not book_info['author']:
                    book_info['author'] = element.get('author', 'Unknown Author')
            
            # Handle other book item formats (fallback)
            else:
                # Look for book card within the element
                bookcard = element.find('z-bookcard')
                if bookcard:
                    return self.extract_book_from_Element(bookcard)
                
                # Fallback: extract from generic book item structure
                book_info = {
                    'id': None,
                    'title': 'Unknown Title',
                    'author': 'Unknown Author',
                    'language': None,
                    'file_type': None,
                    'file_size': None,
                    'year': None,
                    'book_page_url': None,
                    'download_url': None,
                    'download_links': []
                }
                
                # Try to extract what we can
                title_elem = element.find(['h3', 'h4', '.title', '.book-title'])
                if title_elem:
                    book_info['title'] = title_elem.text.strip()
                
                author_elem = element.find(['.author', '.book-author'])
                if author_elem:
                    book_info['author'] = author_elem.text.strip()
            
            # Only return if we have at least a title
            return book_info if book_info.get('title') and book_info.get('title') != 'Unknown Title' else None
            
        except Exception as e:
            print(f"Error extracting book info: {e}")
            return None
    
    def get_download_links_for_books(self, books):
        """Get download links for books using existing selenium method"""
        try:
            # Check if books already have download links from z-bookcard parsing
            books_with_existing_links = sum(1 for book in books if book.get('download_links') and len(book.get('download_links', [])) > 0)
            books_without_links = [book for book in books if not book.get('download_links') or len(book.get('download_links', [])) == 0]
            
            print(f"Books already have download links: {books_with_existing_links}/{len(books)}")
            
            if books_without_links:
                print(f"Extracting download links for {len(books_without_links)} books that don't have them...")
                updated_books_without_links = process_books_selenium_fallback(self.driver, self.wait, books_without_links)
                
                # Merge the results
                updated_books = []
                for book in books:
                    if book.get('download_links') and len(book.get('download_links', [])) > 0:
                        # Book already has links, keep as is
                        updated_books.append(book)
                    else:
                        # Find the updated version of this book
                        updated_book = next((b for b in updated_books_without_links if b.get('id') == book.get('id')), book)
                        updated_books.append(updated_book)
                
                total_books_with_links = sum(1 for book in updated_books if book.get('download_links') and len(book.get('download_links', [])) > 0)
                print(f"Total books with download links: {total_books_with_links}/{len(books)}")
                
                return updated_books
            else:
                print("All books already have download links from z-bookcard parsing!")
                return books
                
        except Exception as e:
            print(f"Error getting download links: {e}")
            return books
    
    def save_booklist_to_json(self, booklist_metadata, books, output_dir="output/json"):
        """Save booklist data to JSON file"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate safe filename
            title = booklist_metadata.get('title', 'unknown_booklist')
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"zlibrary_booklist_{safe_title}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # Prepare output data
            output_data = {
                'booklist_metadata': booklist_metadata,
                'scraping_info': {
                    'scraped_at': datetime.now().isoformat(),
                    'total_books_found': len(books),
                    'scraper_version': '1.0',
                    'source_url': booklist_metadata.get('url')
                },
                'books': books
            }
            
            # Save to JSON file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Saved booklist data to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error saving booklist data: {e}")
            return None
    
    def run_full_scraping(self, max_booklists=None, extract_download_links=True):
        """Run the complete scraping process"""
        try:
            # Step 1: Get all booklists from the main page
            print("Step 1: Scraping booklists page...")
            booklists = self.scrape_booklists_page()
            
            if not booklists:
                print("❌ No booklists found!")
                return
            
            print(f"✅ Found {len(booklists)} booklists")
            
            # Limit number of booklists if specified
            if max_booklists and max_booklists < len(booklists):
                booklists = booklists[:max_booklists]
                print(f"📝 Limited to first {max_booklists} booklists")
            
            # Step 2: Scrape each booklist
            for i, booklist_metadata in enumerate(booklists, 1):
                try:
                    print(f"\n{'='*80}")
                    print(f"📚 Processing booklist {i}/{len(booklists)}")
                    print(f"Title: {booklist_metadata.get('title', 'Unknown')}")
                    print(f"Creator: {booklist_metadata.get('creator', {}).get('name', 'Unknown')}")
                    print(f"Books: {booklist_metadata.get('stats', {}).get('book_count', 'Unknown')}")
                    print(f"{'='*80}")
                    
                    # Scrape all books from this booklist
                    books = self.scrape_individual_booklist(
                        booklist_metadata['url'],
                        booklist_metadata.get('title', 'Unknown')
                    )
                    
                    if not books:
                        print(f"⚠️ No books found in booklist: {booklist_metadata.get('title')}")
                        continue
                    
                    # Step 3: Extract download links if requested
                    if extract_download_links and EXTRACT_DOWNLOAD_LINKS:
                        print("🔗 Extracting download links...")
                        books = self.get_download_links_for_books(books)
                    
                    # Step 4: Save to JSON
                    self.save_booklist_to_json(booklist_metadata, books)
                    
                    # Add delay between booklists to be respectful
                    if i < len(booklists):
                        print("⏳ Waiting before next booklist...")
                        time.sleep(3)
                
                except Exception as e:
                    print(f"❌ Error processing booklist {i}: {e}")
                    continue
            
            print(f"\n{'='*80}")
            print("🎉 BOOKLIST SCRAPING COMPLETED")
            print(f"📁 Check the output/json folder for {len(booklists)} JSON files")
            print(f"{'='*80}")
            
        except Exception as e:
            print(f"❌ Error in full scraping process: {e}")
    
    def close(self):
        """Close the browser"""
        try:
            time.sleep(BROWSER_SLEEP_TIME)
            self.driver.quit()
        except:
            pass


def main():
    """Main function"""
    scraper = ZLibraryBooklistScraper()
    
    try:
        # Step 1: Login
        print("🔐 Logging in to Z-Library...")
        login_successful = scraper.login()
        
        if not login_successful:
            print("❌ Login failed! Cannot proceed.")
            return
        
        print("✅ Login successful!")
        
        # Step 2: Run the scraping process
        # Parameters you can adjust:
        # - max_booklists: Number of booklists to scrape (None for all)
        # - extract_download_links: Whether to get download links for each book
        scraper.run_full_scraping(
            max_booklists=3,  # Start with 3 booklists for testing
            extract_download_links=True
        )
        
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Error in main: {e}")
    finally:
        print("🔄 Closing browser...")
        scraper.close()


if __name__ == "__main__":
    main()
