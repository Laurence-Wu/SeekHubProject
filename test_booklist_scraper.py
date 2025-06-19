#!/usr/bin/env python3
"""
Test script for Z-Library Booklist Scraper
This script will test the scraper with a limited number of booklists
"""

import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from zlibrary_booklist_scraper import ZLibraryBooklistScraper

def test_booklist_scraper():
    """Test the booklist scraper functionality"""
    scraper = ZLibraryBooklistScraper()
    
    try:
        print("🧪 Starting Booklist Scraper Test")
        print("=" * 50)
        
        # Step 1: Test login
        print("🔐 Testing login...")
        login_successful = scraper.login()
        
        if not login_successful:
            print("❌ Login test failed!")
            return False
        
        print("✅ Login test passed!")
        
        # Step 2: Test booklists page scraping
        print("\n📋 Testing booklists page scraping...")
        booklists = scraper.scrape_booklists_page()
        
        if not booklists:
            print("❌ No booklists found!")
            return False
        
        print(f"✅ Found {len(booklists)} booklists")
        
        # Show first few booklists
        print("\n📚 First few booklists found:")
        for i, booklist in enumerate(booklists[:3], 1):
            print(f"{i}. {booklist.get('title', 'Unknown Title')}")
            print(f"   Creator: {booklist.get('creator', {}).get('name', 'Unknown')}")
            print(f"   Books: {booklist.get('stats', {}).get('book_count', 'Unknown')}")
            print(f"   URL: {booklist.get('url', 'No URL')}")
            print()
        
        # Step 3: Test scraping one booklist (just the first one)
        if booklists:
            print("🔍 Testing individual booklist scraping...")
            first_booklist = booklists[0]
            print(f"Testing with: {first_booklist.get('title', 'Unknown')}")
            
            books = scraper.scrape_individual_booklist(
                first_booklist['url'],
                first_booklist.get('title', 'Test Booklist')
            )
            
            if books:
                print(f"✅ Successfully scraped {len(books)} books from booklist")
                
                # Show first few books
                print("\n📖 First few books found:")
                for i, book in enumerate(books[:3], 1):
                    print(f"{i}. {book.get('title', 'Unknown Title')}")
                    print(f"   Author: {book.get('author', 'Unknown Author')}")
                    print(f"   Type: {book.get('file_type', 'Unknown')}")
                    print()
                
                # Test saving (without download links for speed)
                print("💾 Testing JSON save...")
                filepath = scraper.save_booklist_to_json(first_booklist, books)
                
                if filepath:
                    print(f"✅ Successfully saved to: {os.path.basename(filepath)}")
                else:
                    print("❌ Failed to save JSON file")
                    return False
            else:
                print("⚠️ No books found in the test booklist")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        scraper.close()

def main():
    """Main test function"""
    print("Z-Library Booklist Scraper - Test Mode")
    print("This will test the scraper functionality without doing a full scrape")
    print()
    
    success = test_booklist_scraper()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("You can now run the full scraper using:")
        print("python zlibrary_booklist_scraper.py")
    else:
        print("\n❌ Test failed. Please check the configuration and try again.")

if __name__ == "__main__":
    main()
