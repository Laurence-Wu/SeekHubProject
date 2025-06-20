#!/usr/bin/env python3
"""
Category Scraper for Z-Library

This script accesses the Z-Library categories page, extracts all categories,
and performs year traversal searches for each category, storing the results
in the downloads folder.
"""

import os
import sys
import time
import json
import logging
import hashlib
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# Import our existing modules
from zlibraryCrowler.config import (
    ZLIBRARY_BASE_URL, EMAIL, PASSWORD, BROWSER_TIMEOUT, USE_HEADLESS_BROWSER,
    CHROME_OPTIONS, get_cookies_filepath, create_output_directories,
    update_preferred_year, update_book_search_name, PREFERRED_YEAR,
    OUTPUT_FOLDERS, MAX_RETRIES, RETRY_DELAY, COOKIES_FILE
)
from zlibraryCrowler.login import perform_login, handle_login_session_loss, verify_login_status
from zlibraryCrowler.getCookies import get_cookies_from_selenium

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Categories page URL
CATEGORIES_URL = "https://zh.z-lib.fm/categories"

# Configuration for category processing behavior
SKIP_FULLY_PROCESSED_CATEGORIES = True  # Set to False to re-process all categories
SHOW_DETAILED_CATEGORY_STATUS = True    # Set to False to reduce log verbosity

def extract_categories(driver, wait):
    """
    Extract all categories from the Z-Library categories page.
    
    Args:
        driver: The Selenium WebDriver instance
        wait: The Selenium WebDriverWait instance
    
    Returns:
        list: List of dictionaries containing category information
    """
    categories = []
    
    try:
        logger.info(f"Navigating to categories page: {CATEGORIES_URL}")
        driver.get(CATEGORIES_URL)
        time.sleep(3)  # Allow page to load
        
        # Verify we're still logged in
        if not verify_login_status(driver, timeout=5):
            logger.error("Not logged in on categories page!")
            return categories
        
        logger.info("Successfully accessed categories page while logged in")
        
        # Wait for categories to load
        try:
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, 'subcategory-name'))
            )
        except TimeoutException:
            logger.error("Timeout waiting for categories to load")
            return categories
        
        # Get page source and parse with BeautifulSoup
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find all category elements
        category_elements = soup.find_all('li', class_='subcategory-name')
        
        logger.info(f"Found {len(category_elements)} categories")
        
        for element in category_elements:
            try:
                # Extract category information
                data_name = element.get('data-name', '')
                data_type = element.get('data-type', '')
                
                # Find the link within the element
                link_element = element.find('a')
                if link_element:
                    href = link_element.get('href', '')
                    category_text = link_element.get_text(strip=True)
                    
                    # Extract category name and book count
                    category_name = category_text.split('(')[0].strip() if '(' in category_text else category_text
                    book_count = category_text.split('(')[1].split(')')[0] if '(' in category_text and ')' in category_text else '0'
                    
                    category_info = {
                        'data_name': data_name,
                        'data_type': data_type,
                        'name': category_name,
                        'book_count': book_count,
                        'href': href,
                        'full_url': f"{ZLIBRARY_BASE_URL}{href}" if href else None
                    }
                    
                    categories.append(category_info)
                    logger.info(f"Extracted category: {category_name} ({book_count} books)")
                
            except Exception as e:
                logger.warning(f"Error extracting category info from element: {e}")
                continue
        
        logger.info(f"Successfully extracted {len(categories)} categories")
        return categories
        
    except Exception as e:
        logger.error(f"Error extracting categories: {e}")
        return categories


def run_year_traversal_for_category(category_info, start_year=2000, end_year=2025):
    """
    Run year traversal for a specific category by updating the book search name
    and running the traversal script.
    
    Args:
        category_info (dict): Category information dictionary
        start_year (int): Starting year for traversal
        end_year (int): Ending year for traversal
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        category_name = category_info['name']
        logger.info(f"Starting year traversal for category: {category_name}")
        
        # Check if category has already been processed
        logger.info(f"Checking if category '{category_name}' has already been processed...")
        processing_status = check_category_already_processed(category_name, start_year, end_year)
        
        if processing_status['fully_processed']:
            logger.info(f"✅ Category '{category_name}' has already been fully processed!")
            logger.info(f"   Found {len(processing_status['existing_files'])} existing files")
            logger.info(f"   All years ({start_year}-{end_year}) have been processed")
            return True
        
        # If partially processed, only process missing years
        years_to_process = processing_status['missing_years']
        if len(years_to_process) < (end_year - start_year + 1):
            logger.info(f"📋 Category '{category_name}' is partially processed")
            logger.info(f"   Already processed years: {processing_status['processed_years']}")
            logger.info(f"   Will process {len(years_to_process)} missing years: {years_to_process}")
        else:
            logger.info(f"🆕 Category '{category_name}' is new - will process all {len(years_to_process)} years")
        
        # Update the book search name to the category name
        logger.info(f"Updating book search name to: {category_name}")
        if not update_book_search_name(category_name):
            logger.error(f"Failed to update book search name to {category_name}")
            return False
        
        # Store the original year to restore later
        original_year = PREFERRED_YEAR
        
        # Statistics tracking
        successful_years = []
        failed_years = []
        total_start_time = time.time()
        
        if years_to_process:
            logger.info(f"Starting year traversal for {len(years_to_process)} years: {years_to_process} for category: {category_name}")
        else:
            logger.info(f"No years to process for category: {category_name}")
            return True
        
        # Loop through only the missing years
        for year in years_to_process:
            logger.info(f"Processing year {year} for category: {category_name} ({years_to_process.index(year) + 1}/{len(years_to_process)})")
            
            year_start_time = time.time()
            
            # Update the preferred year in config
            logger.info(f"Updating preferred year to {year}...")
            update_success = update_preferred_year(year)
            
            if not update_success:
                logger.error(f"Failed to update preferred year to {year}")
                failed_years.append(year)
                continue
            
            logger.info(f"Successfully updated preferred year to {year}")
            
            # Run the unprocessed JSON generator
            logger.info(f"Running unprocessed JSON generator for year {year} and category {category_name}...")
            generator_success = run_unprocessed_json_generator()
            
            year_end_time = time.time()
            year_duration = year_end_time - year_start_time
            
            if generator_success:
                logger.info(f"Successfully completed processing for year {year} and category {category_name}")
                logger.info(f"Year {year} processing time: {year_duration:.2f} seconds")
                successful_years.append(year)
            else:
                logger.error(f"Failed to process year {year} for category {category_name}")
                failed_years.append(year)
            
            # Add a small delay between years
            logger.info("Waiting 3 seconds before next year...")
            time.sleep(3)
        
        # Restore original year
        logger.info(f"Restoring original preferred year to {original_year}...")
        restore_success = update_preferred_year(original_year)
        if restore_success:
            logger.info(f"Successfully restored preferred year to {original_year}")
        else:
            logger.error(f"Failed to restore preferred year to {original_year}")
        
        # Print statistics for this category
        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        
        # Calculate comprehensive statistics
        total_years_range = end_year - start_year + 1
        skipped_years = len(processing_status['processed_years'])
        processed_now = len(successful_years)
        failed_now = len(failed_years)
        
        logger.info(f"Category '{category_name}' traversal completed")
        logger.info(f"📊 PROCESSING SUMMARY:")
        logger.info(f"   • Total year range: {start_year}-{end_year} ({total_years_range} years)")
        logger.info(f"   • Previously processed: {skipped_years} years")
        logger.info(f"   • Processed now: {processed_now} years")
        logger.info(f"   • Failed now: {failed_now} years")
        logger.info(f"   • Total coverage: {skipped_years + processed_now}/{total_years_range} years ({((skipped_years + processed_now)/total_years_range)*100:.1f}%)")
        logger.info(f"   • Processing time: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
        
        if processing_status['processed_years']:
            logger.info(f"📋 Previously processed years: {processing_status['processed_years']}")
        
        if successful_years:
            logger.info(f"✅ Successfully processed years: {successful_years}")
        
        if failed_years:
            logger.info(f"❌ Failed years: {failed_years}")
        
        return len(failed_years) == 0  # Return True if no failures
        
    except Exception as e:
        logger.error(f"Error during year traversal for category '{category_info.get('name', 'Unknown')}': {e}")
        return False


def run_unprocessed_json_generator():
    """
    Run the unprocessed JSON generator script.
    
    Returns:
        bool: True if the script ran successfully, False otherwise
    """
    try:
        # Get the path to the unprocessed JSON generator
        script_path = os.path.join(os.path.dirname(__file__), 'unprocessesd_json_generator.py')
        
        # Set up environment to include current directory in Python path
        env = os.environ.copy()
        current_dir = os.path.dirname(__file__)
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{current_dir}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = current_dir
        
        # Run the script using Python with proper environment
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=True, 
                              text=True, 
                              timeout=1500,  # 25 minute timeout
                              env=env,
                              cwd=current_dir)
        
        # Print output for debugging
        if result.stdout:
            logger.info(f"Generator STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Generator STDERR:\n{result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        logger.error("JSON generator script timed out after 25 minutes")
        return False
    except Exception as e:
        logger.error(f"Error running unprocessed JSON generator: {e}")
        return False


def save_categories_info(categories, output_dir=None):
    """
    Save categories information to a JSON file.
    
    Args:
        categories (list): List of category dictionaries
        output_dir (str): Output directory (defaults to downloads folder)
    
    Returns:
        str: Path to saved file, or None if failed
    """
    try:
        if output_dir is None:
            output_dir = OUTPUT_FOLDERS['downloads']
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = int(time.time())
        filename = f"zlibrary_categories_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Save categories to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Saved {len(categories)} categories to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error saving categories info: {e}")
        return None


def check_category_already_processed(category_name, start_year=2000, end_year=2025):
    """
    Check if a category has already been processed by looking for existing JSON files
    in the output/json folder.
    
    Args:
        category_name (str): Name of the category to check
        start_year (int): Starting year to check
        end_year (int): Ending year to check
    
    Returns:
        dict: Dictionary with processing status information
            - 'fully_processed': bool - True if all years are processed
            - 'processed_years': list - Years that have been processed
            - 'missing_years': list - Years that haven't been processed
            - 'existing_files': list - List of existing JSON files for this category
    """
    try:
        json_dir = OUTPUT_FOLDERS['json']
        
        # Ensure the path is absolute
        if not os.path.isabs(json_dir):
            json_dir = os.path.join(os.path.dirname(__file__), json_dir)
        
        # Create directory if it doesn't exist
        os.makedirs(json_dir, exist_ok=True)
        
        # Get all JSON files in the directory
        if not os.path.exists(json_dir):
            logger.warning(f"JSON directory does not exist: {json_dir}")
            return {
                'fully_processed': False,
                'processed_years': [],
                'missing_years': list(range(start_year, end_year + 1)),
                'existing_files': []
            }
        
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
        
        # Clean category name for filename matching (same as in config.py)
        import re
        clean_category_name = re.sub(r'[<>:"|?*/\\]', '_', category_name)
        
        # Find files that match this category
        existing_files = []
        processed_years = []
        
        for file in json_files:
            # Check if the file contains the category name
            # The filename pattern is: zlibrary_crawler_{category_name}_{language}_{year}_{hash}_books.json
            if clean_category_name.lower() in file.lower() and '_books.json' in file:
                existing_files.append(file)
                
                # Try to extract year from filename
                try:
                    # Look for year pattern (4 digits) in the filename
                    year_matches = re.findall(r'_(\d{4})_', file)
                    for year_str in year_matches:
                        year = int(year_str)
                        if start_year <= year <= end_year:
                            processed_years.append(year)
                            break
                except (ValueError, IndexError):
                    continue
        
        # Remove duplicates and sort
        processed_years = sorted(list(set(processed_years)))
        missing_years = [year for year in range(start_year, end_year + 1) if year not in processed_years]
        
        fully_processed = len(missing_years) == 0
        
        if SHOW_DETAILED_CATEGORY_STATUS:
            logger.info(f"Category '{category_name}' processing status:")
            logger.info(f"  - Processed years: {len(processed_years)}/{end_year - start_year + 1}")
            logger.info(f"  - Existing files: {len(existing_files)}")
            logger.info(f"  - Fully processed: {fully_processed}")
            
            if processed_years:
                logger.info(f"  - Years with data: {processed_years}")
            if missing_years:
                logger.info(f"  - Missing years: {missing_years[:10]}{'...' if len(missing_years) > 10 else ''}")
        else:
            # Just log a summary line
            status_emoji = "✅" if fully_processed else "📋" if processed_years else "🆕"
            logger.info(f"{status_emoji} {category_name}: {len(processed_years)}/{end_year - start_year + 1} years processed")
        
        return {
            'fully_processed': fully_processed,
            'processed_years': processed_years,
            'missing_years': missing_years,
            'existing_files': existing_files
        }
        
    except Exception as e:
        logger.error(f"Error checking category processing status for '{category_name}': {e}")
        return {
            'fully_processed': False,
            'processed_years': [],
            'missing_years': list(range(start_year, end_year + 1)),
            'existing_files': []
        }


def analyze_all_categories_status(categories, start_year=2000, end_year=2025):
    """
    Analyze the processing status of all categories and provide a summary.
    
    Args:
        categories (list): List of category dictionaries
        start_year (int): Starting year to check
        end_year (int): Ending year to check
    
    Returns:
        dict: Summary statistics of all categories
    """
    try:
        logger.info(f"\n{'='*80}")
        logger.info("ANALYZING CATEGORY PROCESSING STATUS")
        logger.info(f"{'='*80}")
        
        fully_processed = []
        partially_processed = []
        not_processed = []
        
        total_years_range = end_year - start_year + 1
        total_possible_files = len(categories) * total_years_range
        total_existing_files = 0
        
        for category in categories:
            category_name = category['name']
            status = check_category_already_processed(category_name, start_year, end_year)
            
            if status['fully_processed']:
                fully_processed.append({
                    'name': category_name,
                    'status': status
                })
            elif status['processed_years']:
                partially_processed.append({
                    'name': category_name,
                    'status': status
                })
            else:
                not_processed.append({
                    'name': category_name,
                    'status': status
                })
            
            total_existing_files += len(status['existing_files'])
        
        # Print summary
        logger.info(f"📊 CATEGORY PROCESSING SUMMARY:")
        logger.info(f"   • Total categories: {len(categories)}")
        logger.info(f"   • Fully processed: {len(fully_processed)} ({len(fully_processed)/len(categories)*100:.1f}%)")
        logger.info(f"   • Partially processed: {len(partially_processed)} ({len(partially_processed)/len(categories)*100:.1f}%)")
        logger.info(f"   • Not processed: {len(not_processed)} ({len(not_processed)/len(categories)*100:.1f}%)")
        logger.info(f"   • Year range: {start_year}-{end_year} ({total_years_range} years per category)")
        logger.info(f"   • Total existing files: {total_existing_files}")
        logger.info(f"   • Overall completion: {total_existing_files}/{total_possible_files} files ({total_existing_files/total_possible_files*100:.1f}%)")
        
        if fully_processed:
            logger.info(f"\n✅ FULLY PROCESSED CATEGORIES ({len(fully_processed)}):")
            for item in fully_processed[:5]:  # Show first 5
                logger.info(f"   • {item['name']} ({len(item['status']['existing_files'])} files)")
            if len(fully_processed) > 5:
                logger.info(f"   ... and {len(fully_processed) - 5} more")
        
        if partially_processed:
            logger.info(f"\n📋 PARTIALLY PROCESSED CATEGORIES ({len(partially_processed)}):")
            for item in partially_processed[:5]:  # Show first 5
                years_done = len(item['status']['processed_years'])
                years_missing = len(item['status']['missing_years'])
                logger.info(f"   • {item['name']}: {years_done}/{total_years_range} years ({years_done/(years_done+years_missing)*100:.0f}%)")
            if len(partially_processed) > 5:
                logger.info(f"   ... and {len(partially_processed) - 5} more")
        
        if not_processed:
            logger.info(f"\n🆕 NOT PROCESSED CATEGORIES ({len(not_processed)}):")
            for item in not_processed[:10]:  # Show first 10
                logger.info(f"   • {item['name']}")
            if len(not_processed) > 10:
                logger.info(f"   ... and {len(not_processed) - 10} more")
        
        logger.info(f"{'='*80}")
        
        return {
            'fully_processed': fully_processed,
            'partially_processed': partially_processed,
            'not_processed': not_processed,
            'total_existing_files': total_existing_files,
            'total_possible_files': total_possible_files,
            'completion_percentage': total_existing_files/total_possible_files*100
        }
        
    except Exception as e:
        logger.error(f"Error analyzing categories status: {e}")
        return {
            'fully_processed': [],
            'partially_processed': [],
            'not_processed': categories,
            'total_existing_files': 0,
            'total_possible_files': len(categories) * (end_year - start_year + 1),
            'completion_percentage': 0
        }


def main():
    """
    Main function to scrape categories and perform year traversal for each.
    """
    print("="*80)
    print("Z-LIBRARY CATEGORY SCRAPER WITH YEAR TRAVERSAL")
    print("="*80)
    
    # Create output directories
    create_output_directories()
    
    # Store original book search name to restore later
    original_book_name = None
    
    driver = None
    try:
        # Setup driver
        logger.info("Setting up WebDriver...")
        chrome_options = Options()
        
        if USE_HEADLESS_BROWSER:
            chrome_options.add_argument('--headless')
        
        # Add all Chrome options from config
        for option in CHROME_OPTIONS:
            chrome_options.add_argument(option)
            
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, BROWSER_TIMEOUT)
        
        if not driver:
            logger.error("Failed to setup WebDriver")
            return False
        
        # Login with stored credentials
        logger.info("Attempting to login...")
        cookies_file = get_cookies_filepath()
        
        if not perform_login(driver, wait, cookies_file, EMAIL, PASSWORD):
            logger.error("Failed to login")
            return False
        
        logger.info("Successfully logged in!")
        
        # Extract categories
        logger.info("Extracting categories from Z-Library...")
        categories = extract_categories(driver, wait)
        
        if not categories:
            logger.error("No categories found or failed to extract categories")
            return False
        
        logger.info(f"Found {len(categories)} categories to process")
        
        # Save categories information
        categories_file = save_categories_info(categories)
        if categories_file:
            logger.info(f"Categories information saved to: {categories_file}")
        
        # Analyze current processing status of all categories
        analysis = analyze_all_categories_status(categories)
        
        # Process each category with year traversal
        successful_categories = []
        failed_categories = []
        total_start_time = time.time()
        
        for i, category in enumerate(categories, 1):
            category_name = category['name']
            logger.info(f"\n{'='*80}")
            logger.info(f"PROCESSING CATEGORY {i}/{len(categories)}: {category_name}")
            logger.info(f"Category info: {category}")
            logger.info(f"{'='*80}")
            
            category_start_time = time.time()
            
            # Run year traversal for this category
            success = run_year_traversal_for_category(category)
            
            category_end_time = time.time()
            category_duration = category_end_time - category_start_time
            
            if success:
                logger.info(f"✅ Successfully completed category: {category_name}")
                logger.info(f"⏱️  Category processing time: {category_duration:.2f} seconds ({category_duration/60:.1f} minutes)")
                successful_categories.append(category_name)
            else:
                logger.error(f"❌ Failed to process category: {category_name}")
                failed_categories.append(category_name)
            
            # Add delay between categories
            if i < len(categories):  # Don't wait after the last category
                logger.info("⏸️  Waiting 10 seconds before next category...")
                time.sleep(10)
        
        # Restore original book search name
        if original_book_name is not None:
            logger.info(f"Restoring original book search name to: {original_book_name}")
            update_book_search_name(original_book_name)
        else:
            logger.info("Setting book search name back to None")
            update_book_search_name(None)
        
        # Print final statistics
        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        
        print(f"\n{'='*80}")
        print("CATEGORY SCRAPING COMPLETED")
        print(f"{'='*80}")
        print(f"📊 FINAL STATISTICS:")
        print(f"   • Total categories processed: {len(successful_categories) + len(failed_categories)}")
        print(f"   • Successful categories: {len(successful_categories)}")
        print(f"   • Failed categories: {len(failed_categories)}")
        print(f"   • Success rate: {len(successful_categories)/(len(successful_categories) + len(failed_categories))*100:.1f}%")
        print(f"   • Total processing time: {total_duration:.2f} seconds ({total_duration/60:.1f} minutes)")
        print(f"   • Average time per category: {total_duration/(len(successful_categories) + len(failed_categories)):.2f} seconds")
        
        if successful_categories:
            print(f"\n✅ SUCCESSFUL CATEGORIES:")
            for cat in successful_categories:
                print(f"   • {cat}")
        
        if failed_categories:
            print(f"\n❌ FAILED CATEGORIES:")
            for cat in failed_categories:
                print(f"   • {cat}")
        
        print(f"\n🏁 Category scraping completed!")
        print(f"{'='*80}")
        
        # Analyze overall status of all categories
        analyze_all_categories_status(categories, start_year=2000, end_year=2025)
        
        return len(failed_categories) == 0
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Script interrupted by user (Ctrl+C)")
        return False
    except Exception as e:
        logger.error(f"Critical error in main function: {e}")
        return False
    finally:
        # Clean up
        if driver:
            try:
                driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception:
                pass


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error occurred: {e}")
        sys.exit(1)
