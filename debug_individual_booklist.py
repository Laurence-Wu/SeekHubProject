#!/usr/bin/env python3
"""
Debug script to inspect an individual booklist page structure
"""

import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from zlibraryCrowler.config import *
from zlibraryCrowler.login import perform_login

def debug_individual_booklist():
    """Debug an individual booklist page to see the book structure"""
    chrome_options = Options()
    # Don't use headless for debugging
    # chrome_options.add_argument('--headless')
    
    for option in CHROME_OPTIONS:
        chrome_options.add_argument(option)
    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, BROWSER_TIMEOUT)
    
    try:
        print("🔐 Logging in...")
        login_successful = perform_login(driver, wait, COOKIES_FILE, EMAIL, PASSWORD)
        
        if not login_successful:
            print("❌ Login failed!")
            return
        
        print("✅ Login successful!")
        
        # Test with the "101 books" booklist
        test_url = "https://zh.z-lib.fm/booklist/27086/cc3f23/101-books.html"
        print(f"🌐 Navigating to: {test_url}")
        
        driver.get(test_url)
        time.sleep(5)  # Give time for page to load
        
        print("📄 Getting page source...")
        page_source = driver.page_source
        
        # Save the raw HTML for inspection
        with open('debug_individual_booklist.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("💾 Saved page source to debug_individual_booklist.html")
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        print("\n🔍 Analyzing individual booklist page structure...")
        
        # Check for different possible book selectors
        selectors_to_check = [
            ('z-bookcard', 'z-bookcard elements'),
            ('div.book-item', 'book-item divs'),
            ('div[class*="book"]', 'divs with book in class name'),
            ('z-cover', 'z-cover elements'),
            ('a[href*="/book/"]', 'links to book pages'),
        ]
        
        for selector, description in selectors_to_check:
            elements = soup.select(selector)
            print(f"  {description}: {len(elements)} found")
            
            if elements and len(elements) <= 10:  # Show details for reasonable numbers
                for i, elem in enumerate(elements[:3], 1):
                    if elem.name:
                        print(f"    {i}. Tag: {elem.name}")
                        print(f"       Classes: {elem.get('class', [])}")
                        print(f"       ID: {elem.get('id', 'No ID')}")
                        if elem.name == 'z-bookcard':
                            print(f"       Title: {elem.get('title', 'No title attr')}")
                            print(f"       Author: {elem.get('author', 'No author attr')}")
                            print(f"       href: {elem.get('href', 'No href')}")
                        elif elem.name == 'a':
                            print(f"       href: {elem.get('href', 'No href')}")
                            print(f"       Text: {elem.get_text()[:50]}...")
                        text_preview = elem.get_text()[:100].replace('\n', ' ').strip()
                        print(f"       Text preview: {text_preview}...")
                        print()
        
        # Look for pagination
        print("📄 Checking for pagination...")
        pagination_elements = soup.find_all('a', href=True)
        next_links = [link for link in pagination_elements if 'next' in link.get('rel', [])]
        print(f"  Next page links: {len(next_links)} found")
        
        page_links = [link for link in pagination_elements if '/booklist/' in link.get('href', '') and ('page=' in link.get('href', '') or link.get_text().isdigit())]
        print(f"  Page number links: {len(page_links)} found")
        
        for i, link in enumerate(page_links[:5], 1):
            print(f"    {i}. {link.get_text()} -> {link.get('href')}")
        
        print(f"\n✅ Debug complete! Check debug_individual_booklist.html for full page source.")
        
        # Keep browser open for manual inspection
        input("\n🔍 Press Enter to close browser (you can inspect the page manually now)...")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🐛 Individual Booklist Page Debugger")
    print("This will help us understand the structure of individual booklist pages")
    print()
    debug_individual_booklist()
