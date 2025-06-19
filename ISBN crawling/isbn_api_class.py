"""
ISBNdb API Client Class
A comprehensive Python client for interacting with the ISBNdb API v2

Author: GitHub Copilot
Date: June 17, 2025
"""

import requests
import time
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import json


class SubscriptionPlan(Enum):
    """Enumeration for different subscription plans"""
    BASIC = "basic"
    PREMIUM = "premium"
    PRO = "pro"


class ISBNdbAPIError(Exception):
    """Custom exception for ISBNdb API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class RateLimiter:
    """Rate limiter to handle API request limits"""
    
    def __init__(self, requests_per_second: float):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_interval:
            sleep_time = self.min_interval - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()


class ISBNdbAPI:
    """
    A comprehensive client for the ISBNdb API v2
    
    This class provides methods to interact with all ISBNdb API endpoints:
    - Author search and details
    - Book search and details
    - Publisher search and details
    - Subject search and details
    - General search across all databases
    - Database statistics
    """
    
    def __init__(self, api_key: str, subscription_plan: SubscriptionPlan = SubscriptionPlan.BASIC):
        """
        Initialize the ISBNdb API client
        
        Args:
            api_key (str): Your ISBNdb API key
            subscription_plan (SubscriptionPlan): Your subscription plan (BASIC, PREMIUM, or PRO)
        """
        self.api_key = api_key
        self.subscription_plan = subscription_plan
        
        # Set base URL and rate limits based on subscription plan
        if subscription_plan == SubscriptionPlan.PREMIUM:
            self.base_url = "https://api.premium.isbndb.com"
            self.rate_limiter = RateLimiter(3.0)  # 3 requests per second
        elif subscription_plan == SubscriptionPlan.PRO:
            self.base_url = "https://api.pro.isbndb.com"
            self.rate_limiter = RateLimiter(5.0)  # 5 requests per second
        else:
            self.base_url = "https://api2.isbndb.com"
            self.rate_limiter = RateLimiter(1.0)  # 1 request per second
        
        self.headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json',
            'User-Agent': 'ISBNdb-Python-Client/1.0'
        }
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the ISBNdb API with rate limiting
        
        Args:
            method (str): HTTP method (GET, POST, etc.)
            endpoint (str): API endpoint
            params (dict, optional): Query parameters
            data (dict, optional): Request body data
            
        Returns:
            dict: API response data
            
        Raises:
            ISBNdbAPIError: If the API request fails
        """
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data, params=params)
            else:
                raise ISBNdbAPIError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"raw_response": response.text}
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            try:
                error_data = e.response.json() if e.response else {}
                error_message = error_data.get('message', str(e))
            except:
                error_message = str(e)
            raise ISBNdbAPIError(f"HTTP Error: {error_message}", status_code)
        
        except requests.exceptions.RequestException as e:
            raise ISBNdbAPIError(f"Request Error: {str(e)}")
    
    # Author endpoints
    def get_author_details(self, author_name: str) -> Dict[str, Any]:
        """
        Get details for a specific author
        
        Args:
            author_name (str): Name of the author
            
        Returns:
            dict: Author details
        """
        endpoint = f"/author/{author_name}"
        return self._make_request('GET', endpoint)
    
    def search_authors(self, query: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search for authors
        
        Args:
            query (str): Search query for authors
            page (int): Page number (default: 1)
            page_size (int): Number of results per page (default: 20)
            
        Returns:
            dict: Search results
        """
        endpoint = f"/authors/{query}"
        params = {
            'page': page,
            'pageSize': page_size
        }
        return self._make_request('GET', endpoint, params=params)
    
    # Book endpoints
    def get_book_details(self, isbn: str) -> Dict[str, Any]:
        """
        Get details for a specific book by ISBN
        
        Args:
            isbn (str): ISBN of the book (10 or 13 digits)
            
        Returns:
            dict: Book details
        """
        endpoint = f"/book/{isbn}"
        return self._make_request('GET', endpoint)
    
    def search_books_get(self, query: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search for books using GET method
        
        Args:
            query (str): Search query for books
            page (int): Page number (default: 1)
            page_size (int): Number of results per page (default: 20)
            
        Returns:
            dict: Search results
        """
        endpoint = f"/books/{query}"
        params = {
            'page': page,
            'pageSize': page_size
        }
        return self._make_request('GET', endpoint, params=params)
    
    def search_books_post(self, search_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for books using POST method with advanced criteria
        
        Args:
            search_criteria (dict): Advanced search criteria
            Example:
            {
                "text": "python programming",
                "author": "john doe",
                "publisher": "oreilly",
                "subject": "computers",
                "page": 1,
                "pageSize": 20
            }
            
        Returns:
            dict: Search results
        """
        endpoint = "/books"
        return self._make_request('POST', endpoint, data=search_criteria)
    
    # Publisher endpoints
    def get_publisher_details(self, publisher_name: str) -> Dict[str, Any]:
        """
        Get details for a specific publisher
        
        Args:
            publisher_name (str): Name of the publisher
            
        Returns:
            dict: Publisher details
        """
        endpoint = f"/publisher/{publisher_name}"
        return self._make_request('GET', endpoint)
    
    def search_publishers(self, query: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search for publishers
        
        Args:
            query (str): Search query for publishers
            page (int): Page number (default: 1)
            page_size (int): Number of results per page (default: 20)
            
        Returns:
            dict: Search results
        """
        endpoint = f"/publishers/{query}"
        params = {
            'page': page,
            'pageSize': page_size
        }
        return self._make_request('GET', endpoint, params=params)
    
    # Subject endpoints
    def get_subject_details(self, subject_name: str) -> Dict[str, Any]:
        """
        Get details for a specific subject
        
        Args:
            subject_name (str): Name of the subject
            
        Returns:
            dict: Subject details
        """
        endpoint = f"/subject/{subject_name}"
        return self._make_request('GET', endpoint)
    
    def search_subjects(self, query: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search for subjects
        
        Args:
            query (str): Search query for subjects
            page (int): Page number (default: 1)
            page_size (int): Number of results per page (default: 20)
            
        Returns:
            dict: Search results
        """
        endpoint = f"/subjects/{query}"
        params = {
            'page': page,
            'pageSize': page_size
        }
        return self._make_request('GET', endpoint, params=params)
    
    # Search endpoint
    def search_all_databases(self, index: str, query: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Search across all ISBNdb databases
        
        Args:
            index (str): Database index to search ('books', 'authors', 'publishers', 'subjects')
            query (str): Search query
            page (int): Page number (default: 1)
            page_size (int): Number of results per page (default: 20)
            
        Returns:
            dict: Search results
        """
        endpoint = f"/search/{index}"
        params = {
            'q': query,
            'page': page,
            'pageSize': page_size
        }
        return self._make_request('GET', endpoint, params=params)
    
    # Stats endpoint
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics on the ISBNdb database
        
        Returns:
            dict: Database statistics
        """
        endpoint = "/stats"
        return self._make_request('GET', endpoint)
    
    # Utility methods
    def validate_isbn(self, isbn: str) -> bool:
        """
        Validate ISBN format (basic validation)
        
        Args:
            isbn (str): ISBN to validate
            
        Returns:
            bool: True if ISBN format is valid
        """
        # Remove hyphens and spaces
        clean_isbn = ''.join(c for c in isbn if c.isdigit() or c.upper() == 'X')
        
        # Check length
        if len(clean_isbn) not in [10, 13]:
            return False
        
        # Basic format check
        if len(clean_isbn) == 10:
            # ISBN-10: 9 digits + check digit (can be X)
            return clean_isbn[:-1].isdigit() and (clean_isbn[-1].isdigit() or clean_isbn[-1].upper() == 'X')
        else:
            # ISBN-13: all digits
            return clean_isbn.isdigit()
    
    def format_isbn(self, isbn: str) -> str:
        """
        Format ISBN by removing spaces and hyphens
        
        Args:
            isbn (str): ISBN to format
            
        Returns:
            str: Formatted ISBN
        """
        return ''.join(c for c in isbn if c.isdigit() or c.upper() == 'X')
    
    def get_multiple_books(self, isbn_list: List[str]) -> List[Dict[str, Any]]:
        """
        Get details for multiple books by ISBN
        
        Args:
            isbn_list (list): List of ISBNs
            
        Returns:
            list: List of book details
        """
        results = []
        for isbn in isbn_list:
            try:
                book_data = self.get_book_details(isbn)
                results.append({
                    'isbn': isbn,
                    'success': True,
                    'data': book_data
                })
            except ISBNdbAPIError as e:
                results.append({
                    'isbn': isbn,
                    'success': False,
                    'error': str(e)
                })
        return results
    
    def advanced_book_search(self, title: str = None, author: str = None, 
                           publisher: str = None, subject: str = None,
                           year: str = None, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        Perform advanced book search using multiple criteria
        
        Args:
            title (str, optional): Book title
            author (str, optional): Author name
            publisher (str, optional): Publisher name
            subject (str, optional): Subject/category
            year (str, optional): Publication year
            page (int): Page number (default: 1)
            page_size (int): Number of results per page (default: 20)
            
        Returns:
            dict: Search results
        """
        search_criteria = {
            'page': page,
            'pageSize': page_size
        }
        
        if title:
            search_criteria['title'] = title
        if author:
            search_criteria['author'] = author
        if publisher:
            search_criteria['publisher'] = publisher
        if subject:
            search_criteria['subject'] = subject
        if year:
            search_criteria['year'] = year
        
        return self.search_books_post(search_criteria)


# Example usage and testing functions
def example_usage():
    """
    Example usage of the ISBNdb API client
    """
    # Initialize the API client
    api_key = "YOUR_API_KEY_HERE"  # Replace with your actual API key
    client = ISBNdbAPI(api_key, SubscriptionPlan.BASIC)
    
    try:
        # Get book details by ISBN
        print("Getting book details for ISBN 9780134093413...")
        book = client.get_book_details("9780134093413")
        print(f"Book title: {book.get('title', 'Not found')}")
        
        # Search for books
        print("\nSearching for Python programming books...")
        search_results = client.search_books_get("python programming")
        print(f"Found {len(search_results.get('books', []))} books")
        
        # Get database statistics
        print("\nGetting database statistics...")
        stats = client.get_database_stats()
        print(f"Database stats: {stats}")
        
        # Advanced search
        print("\nPerforming advanced book search...")
        advanced_results = client.advanced_book_search(
            title="python",
            author="lutz",
            page=1,
            page_size=5
        )
        print(f"Advanced search results: {len(advanced_results.get('books', []))} books")
        
    except ISBNdbAPIError as e:
        print(f"API Error: {e.message}")
        if e.status_code:
            print(f"Status Code: {e.status_code}")


if __name__ == "__main__":
    # Run example usage (commented out to prevent accidental API calls)
    # example_usage()
    print("ISBNdb API Client class loaded successfully!")
    print("To use this class, initialize it with your API key:")
    print("client = ISBNdbAPI('YOUR_API_KEY', SubscriptionPlan.BASIC)")
