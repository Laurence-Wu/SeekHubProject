#!/usr/bin/env python3
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import config

def test_gutenberg_page_structure():
    """Test to understand Gutenberg's page structure"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Test search page
        search_url = config.GUTENBERG_SEARCH_URL.format(lang="en")
        print(f"Testing search URL: {search_url}")
        driver.get(search_url)
        time.sleep(3)
        
        # Check for book elements
        book_elements = driver.find_elements(By.CSS_SELECTOR, "li.booklink")
        print(f"Found {len(book_elements)} book elements")
        
        if book_elements:
            first_book = book_elements[0]
            link_elem = first_book.find_element(By.CSS_SELECTOR, "a.link")
            book_url = link_elem.get_attribute("href")
            print(f"First book URL: {book_url}")
            
            # Test individual book page
            driver.get(book_url)
            time.sleep(2)
            
            try:
                title = driver.find_element(By.CSS_SELECTOR, "div#content h1").text
                print(f"Book title: {title}")
            except:
                print("Could not find title")
            
            try:
                download_table = driver.find_element(By.CSS_SELECTOR, "table.files")
                links = download_table.find_elements(By.CSS_SELECTOR, "a.link")
                print(f"Found {len(links)} download links")
                for link in links[:3]:  # Show first 3
                    print(f"  - {link.text}: {link.get_attribute('href')}")
            except:
                print("Could not find download table")
                
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_gutenberg_page_structure()
