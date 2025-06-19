import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient, errors
from urllib.parse import quote_plus # For encoding author names in URLs

import config

def get_db_client():
    try:
        client = MongoClient(config.MONGO_URI, username=config.MONGO_USERNAME, password=config.MONGO_PASSWORD)
        client.admin.command('ping')
        print("MongoDB connection successful.")
        return client[config.MONGO_DATABASE]
    except errors.ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
        return None
    except errors.OperationFailure as e:
        print(f"MongoDB authentication/operation failed: {e}. Trying connection without explicit auth...")
        try:
            client = MongoClient(config.MONGO_URI)
            client.admin.command('ping')
            print("MongoDB connection successful (without explicit auth).")
            return client[config.MONGO_DATABASE]
        except Exception as e_no_auth:
            print(f"MongoDB connection failed (without explicit auth either): {e_no_auth}")
            return None

def init_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36")

    if config.CHROME_DRIVER_PATH:
        service = Service(executable_path=config.CHROME_DRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error initializing WebDriver: {e}")
            return None
    return driver

def get_book_details(book_url, driver, language_hint=None):
    print(f"Fetching details for: {book_url}")
    driver.get(book_url)
    time.sleep(2) 

    details = {"url": book_url, "title": "", "author": "", "language": "", "downloads": {}, "gutenberg_id": ""}
    
    try:
        details["title"] = driver.find_element(By.CSS_SELECTOR, "div#content h1").text.strip()
    except NoSuchElementException:
        print(f"Could not find title for {book_url}")

    try:
        author_elements = driver.find_elements(By.CSS_SELECTOR, "p[itemprop='creator'] a")
        if author_elements:
            details["author"] = ", ".join(sorted(list(set(elem.text.strip() for elem in author_elements if elem.text.strip())))) # Unique, sorted authors
        else:
            bibrec_author = driver.find_elements(By.XPATH, "//th[text()='Author']/following-sibling::td")
            if bibrec_author:
                details["author"] = bibrec_author[0].text.strip()
    except NoSuchElementException:
        print(f"Could not find author for {book_url}")

    try:
        lang_element = driver.find_element(By.XPATH, "//tr[th[contains(text(),'Language')]]/td")
        details["language"] = lang_element.text.strip()
    except NoSuchElementException:
        if language_hint: # If language is passed as a hint (e.g. from search query)
            details["language"] = language_hint
        else:
            print(f"Could not find language for {book_url}")
    
    match = re.search(r'/ebooks/(\d+)', book_url)
    if match:
        details["gutenberg_id"] = match.group(1)

    try:
        download_table = driver.find_element(By.CSS_SELECTOR, "table.files")
        links = download_table.find_elements(By.CSS_SELECTOR, "a.link")
        for link_elem in links:
            href = link_elem.get_attribute("href")
            text = link_elem.text.lower()
            if not href: continue
            if not href.startswith("http"):
                href = config.GUTENBERG_BASE_URL + href

            if "plain text" in text and "utf-8" in text:
                details["downloads"]["text_utf8"] = href
            elif "epub (no images)" in text:
                details["downloads"]["epub_no_images"] = href
            elif "epub (with images)" in text:
                details["downloads"]["epub_with_images"] = href
            elif "kindle (no images)" in text: # Mobi is often Kindle
                details["downloads"]["mobi_no_images"] = href
            elif "kindle (with images)" in text:
                details["downloads"]["mobi_with_images"] = href
            elif "read this book online (html)" in text:
                details["downloads"]["html"] = href
        
        # Prioritize specific epub/mobi if general ones are also there
        if "epub_with_images" in details["downloads"] and "epub_no_images" not in details["downloads"]:
            details["downloads"]["epub"] = details["downloads"]["epub_with_images"]
        elif "epub_no_images" in details["downloads"]:
             details["downloads"]["epub"] = details["downloads"]["epub_no_images"]
        
        if "mobi_with_images" in details["downloads"] and "mobi_no_images" not in details["downloads"]:
            details["downloads"]["mobi"] = details["downloads"]["mobi_with_images"]
        elif "mobi_no_images" in details["downloads"]:
            details["downloads"]["mobi"] = details["downloads"]["mobi_no_images"]

    except NoSuchElementException:
        print(f"Could not find download links table for {book_url}")
    
    non_book_keywords = ["index", "journal", "magazine", "papers", "proceedings", "bulletin", "report", "gazette", "notes and queries", "periodical"]
    title_lower = details["title"].lower()
    if any(keyword in title_lower for keyword in non_book_keywords):
        print(f"Skipping '{details['title']}' as it appears to be a non-book item based on title.")
        return None
    try:
        loc_class_element = driver.find_element(By.XPATH, "//tr[th[contains(text(),'LoC Class')]]/td")
        if any(keyword in loc_class_element.text.lower() for keyword in non_book_keywords):
            print(f"Skipping '{details['title']}' due to LoC Class: {loc_class_element.text}")
            return None
    except NoSuchElementException:
        pass # No LoC class, proceed

    if not details["downloads"]:
        print(f"No suitable download links found for '{details['title']}'. Skipping.")
        return None
        
    return details

def save_book_to_db(book_data, db, language_code_crawled):
    if not book_data or not book_data.get("gutenberg_id"):
        return False
    collection = db[config.MONGO_COLLECTION]
    book_data["language_code_crawled"] = language_code_crawled
    try:
        update_filter = {"gutenberg_id": book_data["gutenberg_id"]}
        # Add language_code_crawled to $addToSet to track all languages it was found under
        update_operation = {
            "$set": book_data,
            "$addToSet": {"all_language_codes_crawled": language_code_crawled}
        }
        result = collection.update_one(update_filter, update_operation, upsert=True)
        if result.upserted_id or result.modified_count:
            print(f"Saved/Updated book: {book_data.get('title', 'N/A')} (ID: {book_data['gutenberg_id']})")
            return True
        elif result.matched_count:
            print(f"Book already exists and data is consistent: {book_data.get('title', 'N/A')} (ID: {book_data['gutenberg_id']})")
            return True # Considered success as it's there
    except errors.PyMongoError as e:
        print(f"MongoDB error saving book {book_data.get('title', 'N/A')}: {e}")
    return False

def search_books_by_author_and_language(author_name, language_code, driver, db):
    """Searches for books by a given author in a specific language."""
    books_found = []
    # Gutenberg search URL: https://www.gutenberg.org/ebooks/search/?query=AUTHOR&submit_search=Search&languages[]=LANG_CODE
    # The query parameter for author seems to be just the author's name.
    # The languages[] parameter is how they specify language.
    # Example: query=Mark+Twain&languages[]=en
    
    # Simpler search: query=AUTHORNAME language:LANGCODE
    # Let's try the structured search first.
    # The search URL from config is: "https://www.gutenberg.org/ebooks/search/?query=&submit_search=Search&languages={lang}"
    # We need to modify this to include author.
    # A more direct way: https://www.gutenberg.org/ebooks/search/?query=Dickens&languages=en
    
    encoded_author = quote_plus(author_name)
    search_url = f"https://www.gutenberg.org/ebooks/search/?query={encoded_author}&languages={language_code}"
    
    print(f"Searching for author '{author_name}' in language '{language_code}' at {search_url}")
    driver.get(search_url)
    time.sleep(3)

    # Limit to first page of results for an author to keep it focused
    book_elements = driver.find_elements(By.CSS_SELECTOR, "li.booklink")
    if not book_elements:
        print(f"No books found for author '{author_name}' in language '{language_code}'.")
        return books_found

    book_page_urls = []
    for book_elem in book_elements:
        try:
            ebook_link_tag = book_elem.find_element(By.CSS_SELECTOR, "a.link")
            book_url_path = ebook_link_tag.get_attribute("href")
            if book_url_path and book_url_path.startswith(config.GUTENBERG_BASE_URL + "/ebooks/"):
                book_page_urls.append(book_url_path)
        except NoSuchElementException:
            continue
    
    for book_url in book_page_urls:
        # Check if book already processed to avoid re-crawling
        gid_match = re.search(r'/ebooks/(\d+)', book_url)
        gid = gid_match.group(1) if gid_match else None

        if gid and db[config.MONGO_COLLECTION].count_documents({"gutenberg_id": gid, "language_code_crawled": language_code}) > 0:
            # Fetch from DB if already crawled under this language
            book_data = db[config.MONGO_COLLECTION].find_one({"gutenberg_id": gid})
            if book_data: # Ensure it was actually found
                 print(f"Book ID {gid} by '{author_name}' in '{language_code}' already in DB. Using existing data.")
                 books_found.append(book_data)
                 continue # Continue to next book_url
            # If not found in DB (should not happen if count_documents > 0), proceed to fetch
        
        # If not in DB or GID couldn't be extracted for check, fetch details
        book_details = get_book_details(book_url, driver, language_hint=language_code) # Pass language_code as hint
        if book_details:
            # Ensure the fetched book's language matches the target language, or is very generic
            # Gutenberg's language metadata can sometimes be broad.
            # The search itself should filter by language, but double check.
            fetched_lang_lower = book_details.get("language", "").lower()
            target_lang_name_lower = "" # Get full name for comparison e.g. "english" for "en"
            if language_code == "en": target_lang_name_lower = "english"
            elif language_code == "zh": target_lang_name_lower = "chinese"

            if target_lang_name_lower in fetched_lang_lower or not fetched_lang_lower : # Accept if matches or if language field is empty (rely on search)
                save_book_to_db(book_details, db, language_code)
                books_found.append(book_details)
            else:
                print(f"Skipping book '{book_details.get('title')}' - language '{fetched_lang_lower}' does not match target '{target_lang_name_lower}'.")
        time.sleep(1)
    return books_found


def crawl_books_for_authors(language_code, driver, db, max_pages_to_scan_for_authors):
    """Crawls books in a language, extracts authors, and stores books."""
    collection = db[config.MONGO_COLLECTION]
    search_url = config.GUTENBERG_SEARCH_URL.format(lang=language_code)
    print(f"Scanning for authors in language: {language_code} at {search_url}")
    driver.get(search_url)
    
    authors_found = set()
    books_processed_this_run = []
    
    page_num = 1
    while page_num <= max_pages_to_scan_for_authors:
        print(f"Scanning page {page_num} for authors in {language_code}...")
        time.sleep(3)

        book_elements = driver.find_elements(By.CSS_SELECTOR, "li.booklink")
        if not book_elements:
            print("No more books found on this page.")
            break
        
        book_page_urls = []
        for book_elem in book_elements:
            try:
                ebook_link_tag = book_elem.find_element(By.CSS_SELECTOR, "a.link")
                book_url_path = ebook_link_tag.get_attribute("href")
                if book_url_path and book_url_path.startswith(config.GUTENBERG_BASE_URL + "/ebooks/"):
                    book_page_urls.append(book_url_path)
            except NoSuchElementException:
                continue
        
        for book_url in book_page_urls:
            gid_match = re.search(r'/ebooks/(\d+)', book_url)
            gid = gid_match.group(1) if gid_match else None

            # Check if book already processed to avoid re-crawling for details if only author needed
            if gid and collection.count_documents({"gutenberg_id": gid, "language_code_crawled": language_code}) > 0:
                book_data = collection.find_one({"gutenberg_id": gid})
                if book_data and book_data.get("author"):
                    authors_found.add(book_data["author"])
                    books_processed_this_run.append(book_data) # Add to list of books from this language
                continue 
            
            book_data = get_book_details(book_url, driver, language_hint=language_code)
            if book_data:
                if save_book_to_db(book_data, db, language_code):
                    books_processed_this_run.append(book_data)
                    if book_data.get("author"):
                        authors_found.add(book_data["author"])
            time.sleep(1)

        try:
            next_page_link = driver.find_element(By.CSS_SELECTOR, "a[title='Go to next page']")
            if next_page_link.is_displayed() and next_page_link.is_enabled():
                driver.execute_script("arguments[0].click();", next_page_link)
                page_num += 1
            else:
                break
        except (NoSuchElementException, TimeoutException):
            print("No 'next page' link found or timeout.")
            break
            
    return list(authors_found), books_processed_this_run


def find_translation_pairs(driver, db):
    pairs_collection = db[config.MONGO_PAIRS_COLLECTION]
    found_pairs_count = pairs_collection.count_documents({})
    
    # Step 1: Get a list of authors from English books
    print("Step 1: Finding authors from English books...")
    # We limit the number of pages to scan for English authors to keep this manageable
    english_authors, english_books_scanned = crawl_books_for_authors("en", driver, db, config.MAX_ENGLISH_SEARCH_PAGES_FOR_PAIRS)
    if not english_authors:
        print("No English authors found. Cannot proceed to find pairs.")
        return
    print(f"Found {len(english_authors)} unique English authors from {len(english_books_scanned)} books scanned.")

    # Step 2: For each English author, search for their books in Chinese
    print("\nStep 2: Searching for Chinese translations by these authors...")
    for author_name in english_authors:
        if not author_name: continue # Skip if author name is empty

        if found_pairs_count >= config.MAX_TRANSLATION_PAIRS:
            print(f"Reached maximum of {config.MAX_TRANSLATION_PAIRS} translation pairs. Stopping search.")
            break

        print(f"Searching for Chinese books by author: {author_name}")
        chinese_books_by_author = search_books_by_author_and_language(author_name, "zh", driver, db)

        if chinese_books_by_author:
            # We have potential translations. Find the original English books by this author from our scanned list.
            original_english_books = [b for b in english_books_scanned if b.get("author") == author_name]

            for eng_book in original_english_books:
                if found_pairs_count >= config.MAX_TRANSLATION_PAIRS: break
                for zh_book in chinese_books_by_author:
                    if found_pairs_count >= config.MAX_TRANSLATION_PAIRS: break
                    
                    # Basic check: ensure they are not the exact same book ID (unlikely across languages but good check)
                    if eng_book["gutenberg_id"] == zh_book["gutenberg_id"]:
                        continue

                    # Check if this pair (by IDs) already exists
                    if pairs_collection.count_documents({
                        "eng_gutenberg_id": eng_book["gutenberg_id"],
                        "zh_gutenberg_id": zh_book["gutenberg_id"]
                    }) > 0:
                        print(f"Pair Eng:{eng_book['gutenberg_id']}/Zh:{zh_book['gutenberg_id']} already exists.")
                        continue
                    
                    pair_data = {
                        "author": author_name,
                        "eng_book_title": eng_book.get("title"),
                        "eng_gutenberg_id": eng_book["gutenberg_id"],
                        "eng_book_url": eng_book.get("url"),
                        "eng_downloads": eng_book.get("downloads"),
                        "zh_book_title": zh_book.get("title"),
                        "zh_gutenberg_id": zh_book["gutenberg_id"],
                        "zh_book_url": zh_book.get("url"),
                        "zh_downloads": zh_book.get("downloads"),
                        "found_at": time.time()
                    }
                    try:
                        pairs_collection.insert_one(pair_data)
                        print(f"Found and saved translation pair: Eng='{eng_book.get('title')}' (ID:{eng_book.get('gutenberg_id')}) <-> Zh='{zh_book.get('title')}' (ID:{zh_book.get('gutenberg_id')}) by {author_name}")
                        found_pairs_count += 1
                    except errors.PyMongoError as e:
                        print(f"MongoDB error saving pair: {e}")
        if found_pairs_count >= config.MAX_TRANSLATION_PAIRS: break
        time.sleep(2) # Politeness delay between authors

    print(f"\nFinished searching for translation pairs. Found {pairs_collection.count_documents({})} pairs in total.")


# --- Original Crawling Functionality (can be run independently) ---
def crawl_language_general(language_code, driver, db, max_pages_general_crawl):
    collection = db[config.MONGO_COLLECTION]
    search_url = config.GUTENBERG_SEARCH_URL.format(lang=language_code)
    print(f"Starting general crawl for language: {language_code} at {search_url}")
    driver.get(search_url)
    
    page_num = 1
    while page_num <= max_pages_general_crawl: # Use a specific limit for general crawl
        print(f"Processing page {page_num} for language {language_code} (General Crawl)...")
        time.sleep(3) 

        book_elements = driver.find_elements(By.CSS_SELECTOR, "li.booklink")
        if not book_elements:
            print("No more books found on this page or page structure changed.")
            break
        
        book_page_urls = []
        for book_elem in book_elements:
            try:
                ebook_link_tag = book_elem.find_element(By.CSS_SELECTOR, "a.link")
                book_url_path = ebook_link_tag.get_attribute("href")
                if book_url_path and book_url_path.startswith(config.GUTENBERG_BASE_URL + "/ebooks/"):
                    book_page_urls.append(book_url_path)
            except NoSuchElementException:
                continue
        
        for book_url in book_page_urls:
            book_data = get_book_details(book_url, driver, language_hint=language_code)
            if book_data:
                save_book_to_db(book_data, db, language_code)
            time.sleep(1)

        try:
            next_page_link = driver.find_element(By.CSS_SELECTOR, "a[title='Go to next page']")
            if next_page_link.is_displayed() and next_page_link.is_enabled():
                driver.execute_script("arguments[0].click();", next_page_link)
                page_num += 1
            else:
                break
        except (NoSuchElementException, TimeoutException):
            print("No 'next page' link found or timeout (General Crawl).")
            break
            
    print(f"Finished general crawling for language: {language_code}")

def main_general_crawl():
    db = get_db_client()
    if not db: return
    driver = init_driver()
    if not driver: return

    # Example: Crawl first 2 pages for each target language in general mode
    MAX_PAGES_GENERAL = 2 
    try:
        for lang_code in config.TARGET_LANGUAGES:
            crawl_language_general(lang_code, driver, db, MAX_PAGES_GENERAL)
    finally:
        if driver: driver.quit()
        if db.client: db.client.close()

def main_find_pairs():
    db = get_db_client()
    if not db: return
    driver = init_driver()
    if not driver: return
    try:
        find_translation_pairs(driver, db)
    finally:
        if driver: driver.quit()
        if db.client: db.client.close()

if __name__ == "__main__":
    # Choose which main function to run:
    # main_general_crawl() 
    main_find_pairs() # Defaulting to the new pair finding logic
    # To run general crawl: comment out main_find_pairs() and uncomment main_general_crawl()
