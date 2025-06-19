#!/usr/bin/env python3
"""
Debug script to inspect the Z-Library booklists page structure
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

def debug_booklists_page():
    """Debug the booklists page to see what elements are actually there"""
    chrome_options = Options()
    # Don't use headless for debugging so we can see what's happening
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
        
        booklists_url = f"{ZLIBRARY_BASE_URL}/booklists"
        print(f"🌐 Navigating to: {booklists_url}")
        
        driver.get(booklists_url)
        time.sleep(5)  # Give extra time for page to load
        
        print("📄 Getting page source...")
        page_source = driver.page_source
        
        # Save the raw HTML for inspection
        with open('debug_booklists_page.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        print("💾 Saved page source to debug_booklists_page.html")
        
        soup = BeautifulSoup(page_source, 'html.parser')
        
        print("\n🔍 Analyzing page structure...")
        
        # Check for different possible selectors
        selectors_to_check = [
            ('div.content', 'content divs (original selector)'),
            ('div[class*="content"]', 'divs with content in class name'),
            ('div.book-list', 'book-list divs'),
            ('div[class*="booklist"]', 'divs with booklist in class name'),
            ('div[class*="collection"]', 'divs with collection in class name'),
            ('div[class*="editor"]', 'divs with editor in class name'),
            ('z-booklist', 'z-booklist elements'),
            ('a[href*="booklist"]', 'links containing booklist'),
        ]
        
        for selector, description in selectors_to_check:
            elements = soup.select(selector)
            print(f"  {description}: {len(elements)} found")
            
            if elements and len(elements) <= 5:  # Show details for small numbers
                for i, elem in enumerate(elements[:3], 1):
                    print(f"    {i}. Classes: {elem.get('class', [])}")
                    text_preview = elem.get_text()[:100].replace('\n', ' ').strip()
                    print(f"       Text preview: {text_preview}...")
        
        # Look for the specific structure you mentioned
        print("\n🎯 Looking for specific booklist structure...")
        editors_choice = soup.find_all('div', class_='editors-choice-label')
        print(f"  Editor's Choice labels: {len(editors_choice)} found")
        
        title_divs = soup.find_all('div', class_='title')
        print(f"  Title divs: {len(title_divs)} found")
        
        if title_divs:
            for i, title_div in enumerate(title_divs[:3], 1):
                link = title_div.find('a')
                if link:
                    print(f"    {i}. Title: {link.text.strip()}")
                    print(f"       URL: {link.get('href')}")
        
        z_accounts = soup.find_all('z-account')
        print(f"  z-account elements: {len(z_accounts)} found")
        
        info_blocks = soup.find_all('div', class_='info-block')
        print(f"  info-block divs: {len(info_blocks)} found")
        
        # Check for any booklist-related patterns
        print("\n📋 Checking for booklist patterns...")
        all_links = soup.find_all('a', href=True)
        booklist_links = [link for link in all_links if 'booklist' in link.get('href', '')]
        print(f"  Links containing 'booklist': {len(booklist_links)} found")
        
        for i, link in enumerate(booklist_links[:5], 1):
            print(f"    {i}. {link.text.strip()[:50]}... -> {link.get('href')}")
        
        print(f"\n✅ Debug complete! Check debug_booklists_page.html for full page source.")
        
        # Keep browser open for manual inspection
        input("\n🔍 Press Enter to close browser (you can inspect the page manually now)...")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🐛 Z-Library Booklists Page Debugger")
    print("This will help us understand the actual page structure")
    print()
    debug_booklists_page()
