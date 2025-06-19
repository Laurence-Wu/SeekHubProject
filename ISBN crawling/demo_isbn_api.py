"""
Demo script for ISBNdb API Client
This script demonstrates how to use the ISBNdbAPI class
"""

from isbn_api_class import ISBNdbAPI, SubscriptionPlan, ISBNdbAPIError
import json


def demo_isbn_api():
    """
    Demonstrate various ISBNdb API functionalities
    """
    # Replace with your actual API key
    API_KEY = "YOUR_API_KEY_HERE"
    
    # Initialize the client (change subscription plan as needed)
    client = ISBNdbAPI(API_KEY, SubscriptionPlan.BASIC)
    
    print("=== ISBNdb API Demo ===\n")
    
    # Demo 1: Get book details by ISBN
    print("1. Getting book details by ISBN...")
    try:
        isbn = "9780134093413"  # Clean Code book
        book_details = client.get_book_details(isbn)
        print(f"Book Title: {book_details.get('title', 'N/A')}")
        print(f"Authors: {book_details.get('authors', 'N/A')}")
        print(f"Publisher: {book_details.get('publisher', 'N/A')}")
        print(f"Publication Date: {book_details.get('date_published', 'N/A')}")
    except ISBNdbAPIError as e:
        print(f"Error: {e.message}")
    print()
    
    # Demo 2: Search for books
    print("2. Searching for books...")
    try:
        search_results = client.search_books_get("python programming", page=1, page_size=5)
        books = search_results.get('books', [])
        print(f"Found {len(books)} books:")
        for i, book in enumerate(books[:3], 1):  # Show first 3 results
            print(f"  {i}. {book.get('title', 'Unknown Title')} by {book.get('authors', ['Unknown Author'])[0] if book.get('authors') else 'Unknown Author'}")
    except ISBNdbAPIError as e:
        print(f"Error: {e.message}")
    print()
    
    # Demo 3: Advanced book search
    print("3. Advanced book search...")
    try:
        advanced_results = client.advanced_book_search(
            title="machine learning",
            subject="computers",
            page=1,
            page_size=3
        )
        books = advanced_results.get('books', [])
        print(f"Found {len(books)} machine learning books:")
        for book in books:
            print(f"  - {book.get('title', 'Unknown Title')}")
    except ISBNdbAPIError as e:
        print(f"Error: {e.message}")
    print()
    
    # Demo 4: Search authors
    print("4. Searching for authors...")
    try:
        author_results = client.search_authors("martin fowler", page=1, page_size=3)
        authors = author_results.get('authors', [])
        print(f"Found {len(authors)} authors:")
        for author in authors:
            print(f"  - {author.get('name', 'Unknown Name')}")
    except ISBNdbAPIError as e:
        print(f"Error: {e.message}")
    print()
    
    # Demo 5: Search publishers
    print("5. Searching for publishers...")
    try:
        publisher_results = client.search_publishers("oreilly", page=1, page_size=3)
        publishers = publisher_results.get('publishers', [])
        print(f"Found {len(publishers)} publishers:")
        for publisher in publishers:
            print(f"  - {publisher.get('name', 'Unknown Name')}")
    except ISBNdbAPIError as e:
        print(f"Error: {e.message}")
    print()
    
    # Demo 6: Get database statistics
    print("6. Getting database statistics...")
    try:
        stats = client.get_database_stats()
        print("Database Statistics:")
        print(f"  - Total Books: {stats.get('total_books', 'N/A')}")
        print(f"  - Total Authors: {stats.get('total_authors', 'N/A')}")
        print(f"  - Total Publishers: {stats.get('total_publishers', 'N/A')}")
    except ISBNdbAPIError as e:
        print(f"Error: {e.message}")
    print()
    
    # Demo 7: ISBN validation
    print("7. ISBN validation examples...")
    test_isbns = ["9780134093413", "0134093410", "invalid-isbn", "978-0-13-409341-3"]
    for isbn in test_isbns:
        is_valid = client.validate_isbn(isbn)
        formatted = client.format_isbn(isbn)
        print(f"  {isbn} -> Valid: {is_valid}, Formatted: {formatted}")
    print()
    
    # Demo 8: Multiple books lookup
    print("8. Looking up multiple books...")
    isbn_list = ["9780134093413", "9780596009205", "9781491946008"]
    try:
        results = client.get_multiple_books(isbn_list)
        for result in results:
            if result['success']:
                title = result['data'].get('title', 'Unknown Title')
                print(f"  {result['isbn']}: {title}")
            else:
                print(f"  {result['isbn']}: Error - {result['error']}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    print("=== Demo Complete ===")
    print("\nTo run this demo with real data:")
    print("1. Replace 'YOUR_API_KEY_HERE' with your actual ISBNdb API key")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run: python demo_isbn_api.py")


def test_isbn_validation():
    """
    Test ISBN validation functionality
    """
    print("=== ISBN Validation Tests ===")
    
    # Create a client instance (no API key needed for validation)
    client = ISBNdbAPI("dummy_key")
    
    test_cases = [
        ("9780134093413", True),  # Valid ISBN-13
        ("0134093410", True),     # Valid ISBN-10
        ("978-0-13-409341-3", True),  # Valid ISBN-13 with hyphens
        ("0-13-409341-0", True),  # Valid ISBN-10 with hyphens
        ("invalid", False),       # Invalid
        ("123", False),          # Too short
        ("12345678901234", False),  # Too long
        ("978013409341X", False),  # Invalid check digit for ISBN-13
    ]
    
    for isbn, expected in test_cases:
        result = client.validate_isbn(isbn)
        status = "✓" if result == expected else "✗"
        print(f"{status} {isbn} -> {result} (expected: {expected})")
    
    print("=== Validation Tests Complete ===")


if __name__ == "__main__":
    print("Choose demo to run:")
    print("1. Full API Demo (requires API key)")
    print("2. ISBN Validation Test (no API key required)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        demo_isbn_api()
    elif choice == "2":
        test_isbn_validation()
    else:
        print("Invalid choice. Running validation test...")
        test_isbn_validation()
