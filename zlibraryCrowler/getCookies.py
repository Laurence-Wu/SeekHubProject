
"""
Cookie management utilities for Z-Library authentication.

This module provides functions to extract and manage cookies from Selenium
WebDriver sessions for use with aiohttp requests.
"""

from typing import Dict, Optional
import pickle
import os


def get_cookies_from_selenium(driver) -> Dict[str, str]:
    """
    Extract cookies from Selenium driver for use with aiohttp.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        Dictionary of cookies with name-value pairs
    """
    cookies = {}
    try:
        selenium_cookies = driver.get_cookies()
        for cookie in selenium_cookies:
            cookies[cookie['name']] = cookie['value']
        print(f"Extracted {len(cookies)} cookies from Selenium session")
    except Exception as e:
        print(f"Error extracting cookies: {e}")
    
    return cookies


def save_cookies_to_file(cookies: Dict[str, str], file_path: str) -> bool:
    """
    Save cookies dictionary to a pickle file.
    
    Args:
        cookies: Dictionary of cookies
        file_path: Path to save the cookies file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(cookies, f)
        print(f"Cookies saved to {file_path}")
        return True
    except Exception as e:
        print(f"Error saving cookies to {file_path}: {e}")
        return False


def load_cookies_from_file(file_path: str) -> Optional[Dict[str, str]]:
    """
    Load cookies dictionary from a pickle file.
    
    Args:
        file_path: Path to the cookies file
        
    Returns:
        Dictionary of cookies or None if failed
    """
    try:
        if not os.path.exists(file_path):
            print(f"Cookies file not found: {file_path}")
            return None
            
        with open(file_path, 'rb') as f:
            cookies = pickle.load(f)
        print(f"Cookies loaded from {file_path}")
        return cookies
    except Exception as e:
        print(f"Error loading cookies from {file_path}: {e}")
        return None


def get_cookies_for_aiohttp(driver, cookies_file_path: str = None) -> Dict[str, str]:
    """
    Get cookies for aiohttp requests, trying file first, then Selenium.
    
    Args:
        driver: Selenium WebDriver instance
        cookies_file_path: Optional path to cookies file
        
    Returns:
        Dictionary of cookies
    """
    cookies = {}
    
    # Try loading from file first if path provided
    if cookies_file_path:
        file_cookies = load_cookies_from_file(cookies_file_path)
        if file_cookies:
            cookies.update(file_cookies)
    
    # If no cookies from file or file not provided, extract from Selenium
    if not cookies and driver:
        cookies = get_cookies_from_selenium(driver)
        
        # Save to file for future use if path provided
        if cookies and cookies_file_path:
            save_cookies_to_file(cookies, cookies_file_path)
    
    return cookies


def validate_cookies(cookies: Dict[str, str]) -> bool:
    """
    Validate that cookies contain necessary authentication information.
    
    Args:
        cookies: Dictionary of cookies
        
    Returns:
        True if cookies appear valid, False otherwise
    """
    if not cookies:
        return False
    
    # Check for common Z-Library authentication cookies
    required_cookies = ['session', 'auth', 'user']  # Adjust based on actual Z-Library cookies
    
    # For now, just check if we have any cookies
    # You can customize this based on specific Z-Library cookie requirements
    return len(cookies) > 0


def format_cookies_for_requests(cookies: Dict[str, str]) -> str:
    """
    Format cookies dictionary as a cookie string for HTTP requests.
    
    Args:
        cookies: Dictionary of cookies
        
    Returns:
        Cookie string in format "name1=value1; name2=value2"
    """
    if not cookies:
        return ""
    
    return "; ".join([f"{name}={value}" for name, value in cookies.items()])


def main():
    """
    Example usage of cookie management functions.
    """
    print("Cookie management utilities for Z-Library")
    print("This module is meant to be imported, not run directly.")


if __name__ == "__main__":
    main()
