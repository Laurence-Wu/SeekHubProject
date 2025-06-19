# ISBNdb API Client

A comprehensive Python client for interacting with the ISBNdb API v2. This client provides easy access to all ISBNdb API endpoints with built-in rate limiting, error handling, and support for different subscription plans.

## Features

- **Complete API Coverage**: Supports all ISBNdb API v2 endpoints
- **Rate Limiting**: Automatic rate limiting based on subscription plan
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Multiple Subscription Plans**: Support for Basic, Premium, and Pro plans
- **ISBN Validation**: Built-in ISBN format validation
- **Batch Operations**: Support for multiple book lookups
- **Advanced Search**: Complex search queries with multiple criteria

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Get your API key from [ISBNdb.com](https://isbndb.com/)

## Quick Start

```python
from isbn_api_class import ISBNdbAPI, SubscriptionPlan

# Initialize the client
api_key = "YOUR_API_KEY_HERE"
client = ISBNdbAPI(api_key, SubscriptionPlan.BASIC)

# Get book details by ISBN
book = client.get_book_details("9780134093413")
print(f"Title: {book.get('title')}")

# Search for books
results = client.search_books_get("python programming")
print(f"Found {len(results.get('books', []))} books")
```

## API Endpoints

### Books
- `get_book_details(isbn)` - Get details for a specific book
- `search_books_get(query)` - Search books using GET method
- `search_books_post(criteria)` - Search books using POST with advanced criteria
- `advanced_book_search()` - Advanced search with multiple filters

### Authors
- `get_author_details(name)` - Get details for a specific author
- `search_authors(query)` - Search for authors

### Publishers
- `get_publisher_details(name)` - Get details for a specific publisher
- `search_publishers(query)` - Search for publishers

### Subjects
- `get_subject_details(name)` - Get details for a specific subject
- `search_subjects(query)` - Search for subjects

### General
- `search_all_databases(index, query)` - Search across all databases
- `get_database_stats()` - Get database statistics

### Utilities
- `validate_isbn(isbn)` - Validate ISBN format
- `format_isbn(isbn)` - Format ISBN (remove spaces/hyphens)
- `get_multiple_books(isbn_list)` - Get details for multiple books

## Subscription Plans

The client supports three subscription plans with different rate limits:

- **Basic**: 1 request per second (api2.isbndb.com)
- **Premium**: 3 requests per second (api.premium.isbndb.com)
- **Pro**: 5 requests per second (api.pro.isbndb.com)

```python
# For Premium subscribers
client = ISBNdbAPI(api_key, SubscriptionPlan.PREMIUM)

# For Pro subscribers
client = ISBNdbAPI(api_key, SubscriptionPlan.PRO)
```

## Examples

### Basic Book Search
```python
# Search for books
results = client.search_books_get("machine learning", page=1, page_size=10)
for book in results.get('books', []):
    print(f"{book.get('title')} by {book.get('authors', ['Unknown'])[0]}")
```

### Advanced Book Search
```python
# Advanced search with multiple criteria
results = client.advanced_book_search(
    title="python",
    author="lutz",
    publisher="oreilly",
    subject="programming",
    year="2020"
)
```

### Author Search
```python
# Search for authors
authors = client.search_authors("martin fowler")
for author in authors.get('authors', []):
    print(f"Author: {author.get('name')}")
```

### Multiple Book Lookup
```python
# Get details for multiple books
isbn_list = ["9780134093413", "9780596009205", "9781491946008"]
results = client.get_multiple_books(isbn_list)

for result in results:
    if result['success']:
        print(f"{result['isbn']}: {result['data'].get('title')}")
    else:
        print(f"{result['isbn']}: Error - {result['error']}")
```

### ISBN Validation
```python
# Validate ISBN format
isbn = "978-0-13-409341-3"
if client.validate_isbn(isbn):
    formatted = client.format_isbn(isbn)  # Returns: 9780134093413
    book = client.get_book_details(formatted)
```

## Error Handling

The client includes comprehensive error handling:

```python
from isbn_api_class import ISBNdbAPIError

try:
    book = client.get_book_details("invalid-isbn")
except ISBNdbAPIError as e:
    print(f"API Error: {e.message}")
    if e.status_code:
        print(f"Status Code: {e.status_code}")
```

## Rate Limiting

Rate limiting is automatically handled based on your subscription plan:
- The client will automatically wait between requests to respect rate limits
- No additional configuration needed

## Demo Script

Run the demo script to see all features in action:

```bash
python demo_isbn_api.py
```

The demo includes:
1. Book details lookup
2. Book search
3. Advanced search
4. Author search
5. Publisher search
6. Database statistics
7. ISBN validation
8. Multiple book lookup

## API Response Examples

### Book Details Response
```json
{
    "book": {
        "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
        "authors": ["Robert C. Martin"],
        "publisher": "Prentice Hall",
        "isbn": "9780134093413",
        "isbn13": "9780134093413",
        "date_published": "2008-08-01",
        "subjects": ["Computer programming", "Software engineering"],
        "pages": 464,
        "language": "en"
    }
}
```

### Search Results Response
```json
{
    "books": [
        {
            "title": "Learning Python",
            "authors": ["Mark Lutz"],
            "publisher": "O'Reilly Media",
            "isbn13": "9781449355739"
        }
    ],
    "total": 1500,
    "page": 1,
    "pageSize": 20
}
```

## Requirements

- Python 3.6+
- requests library
- Valid ISBNdb API key

## Files

- `isbn_api_class.py` - Main API client class
- `demo_isbn_api.py` - Demonstration script
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## License

This project is provided as-is for educational and commercial use.

## Support

For ISBNdb API support, visit [ISBNdb.com](https://isbndb.com/)
