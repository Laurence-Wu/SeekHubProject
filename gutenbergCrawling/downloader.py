import os
import threading
import requests
from pymongo import MongoClient, errors
from urllib.parse import urlparse
import re
import time

import config

# Ensure download directory exists
if not os.path.exists(config.DOWNLOAD_DIR):
    os.makedirs(config.DOWNLOAD_DIR)

def get_db_client():
    try:
        client = MongoClient(config.MONGO_URI, username=config.MONGO_USERNAME, password=config.MONGO_PASSWORD)
        client.admin.command('ping')
        print("MongoDB connection successful for downloader.")
        return client[config.MONGO_DATABASE]
    except errors.ConnectionFailure as e:
        print(f"MongoDB connection failed for downloader: {e}")
        return None
    except errors.OperationFailure as e:
        print(f"MongoDB authentication/operation failed for downloader: {e}. Trying connection without explicit auth.")
        try:
            client = MongoClient(config.MONGO_URI)
            client.admin.command('ping')
            print("MongoDB connection successful for downloader (without explicit auth).")
            return client[config.MONGO_DATABASE]
        except Exception as e_no_auth:
            print(f"MongoDB connection failed for downloader (without explicit auth either): {e_no_auth}")
            return None

def sanitize_filename(filename):
    filename = re.sub(r'[<>:"/\\|?*-]', '_', filename)
    filename = re.sub(r'[\s_]+', '_', filename)
    return filename[:200]

def get_file_extension_from_url(url, content_type=None, download_format_preference=None):
    if download_format_preference == "text_utf8": return ".txt"
    if download_format_preference == "epub": return ".epub"
    if download_format_preference == "mobi": return ".mobi"
    if download_format_preference == "html": return ".html"

    if content_type:
        if 'text/plain' in content_type: return '.txt'
        if 'application/epub+zip' in content_type: return '.epub'
        if 'application/x-mobipocket-ebook' in content_type: return '.mobi'
        if 'text/html' in content_type: return '.html'

    path = urlparse(url).path
    _, ext = os.path.splitext(path)
    
    if 'txt.utf-8' in url.lower() or '/0' in url: return '.txt' # /0 often for .txt in Gutenberg
    if '.epub' in url.lower(): return '.epub'
    if '.mobi' in url.lower(): return '.mobi'
    if '.html' in url.lower() or '.htm' in url.lower(): return '.html'
    
    return ext if ext else '.dat'

def download_single_book_from_pair(pair_doc_id, book_details, lang_prefix, db_pairs_collection):
    title = book_details.get(f"{lang_prefix}_book_title", "Unknown_Title")
    gutenberg_id = book_details.get(f"{lang_prefix}_gutenberg_id", "Unknown_ID")
    downloads_dict = book_details.get(f"{lang_prefix}_downloads", {})

    download_url = None
    chosen_format_key = None

    # Prioritize formats
    format_priority = [
        ("text_utf8", "text_utf8"), 
        ("epub", "epub_no_images"), ("epub", "epub_with_images"), ("epub", "epub"), # General epub if specific not found
        ("mobi", "mobi_no_images"), ("mobi", "mobi_with_images"), ("mobi", "mobi"),   # General mobi
        ("html", "html")
    ]

    for generic_fmt, specific_key in format_priority:
        if specific_key in downloads_dict:
            download_url = downloads_dict[specific_key]
            chosen_format_key = generic_fmt # Store the generic format type
            break
    
    if not download_url:
        print(f"No suitable download URL for {lang_prefix.upper()} book '{title}' (ID: {gutenberg_id}).")
        db_pairs_collection.update_one(
            {"_id": pair_doc_id},
            {"$set": {f"{lang_prefix}_download_status": "no_url"}}
        )
        return

    # Construct filename: ID_LANG_Title.ext
    lang_tag = "ENG" if lang_prefix == "eng" else "ZHO" if lang_prefix == "zh" else lang_prefix.upper()
    base_filename = sanitize_filename(f"{gutenberg_id}_{lang_tag}_{title}")
    
    status_field_prefix = f"{lang_prefix}_download" # e.g. eng_download_status

    try:
        print(f"Thread {threading.get_ident()}: Downloading {lang_tag} book '{title}' (ID: {gutenberg_id}) from {download_url}")
        response = requests.get(download_url, timeout=90, stream=True) # Increased timeout
        response.raise_for_status()

        content_type = response.headers.get('Content-Type')
        file_ext = get_file_extension_from_url(download_url, content_type, chosen_format_key)
        
        filepath = os.path.join(config.DOWNLOAD_DIR, f"{base_filename}{file_ext}")

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Thread {threading.get_ident()}: Successfully downloaded '{filepath}'")
        db_pairs_collection.update_one(
            {"_id": pair_doc_id},
            {"$set": {
                f"{status_field_prefix}_status": "downloaded", 
                f"{status_field_prefix}_filepath": filepath,
                f"{status_field_prefix}_format": chosen_format_key
            }}
        )
    except requests.exceptions.RequestException as e:
        print(f"Thread {threading.get_ident()}: Error downloading {lang_tag} book '{title}': {e}")
        db_pairs_collection.update_one(
            {"_id": pair_doc_id},
            {"$set": {f"{status_field_prefix}_status": "error", f"{status_field_prefix}_error": str(e)}}
        )
    except Exception as e:
        print(f"Thread {threading.get_ident()}: Unexpected error for {lang_tag} book '{title}': {e}")
        db_pairs_collection.update_one(
            {"_id": pair_doc_id},
            {"$set": {f"{status_field_prefix}_status": "error_unexpected", f"{status_field_prefix}_error": str(e)}}
        )

def download_book_pair(pair_document, db_pairs_collection):
    """Downloads both English and Chinese books for a given pair document."""
    eng_status = pair_document.get("eng_download_status")
    zh_status = pair_document.get("zh_download_status")

    threads = []
    if not eng_status or eng_status not in ["downloaded", "no_url"]:
        print(f"Attempting download for English book of pair ID: {pair_document['_id']}")
        eng_thread = threading.Thread(target=download_single_book_from_pair, args=(pair_document["_id"], pair_document, "eng", db_pairs_collection))
        threads.append(eng_thread)
        eng_thread.start()
    else:
        print(f"English book for pair ID {pair_document['_id']} already processed (status: {eng_status}).")

    if not zh_status or zh_status not in ["downloaded", "no_url"]:
        print(f"Attempting download for Chinese book of pair ID: {pair_document['_id']}")
        zh_thread = threading.Thread(target=download_single_book_from_pair, args=(pair_document["_id"], pair_document, "zh", db_pairs_collection))
        threads.append(zh_thread)
        zh_thread.start()
    else:
        print(f"Chinese book for pair ID {pair_document['_id']} already processed (status: {zh_status}).")
    
    for t in threads:
        t.join() # Wait for both (or one if other is processed) downloads for this pair to finish

def main_download_pairs():
    db = get_db_client()
    if not db:
        print("Exiting downloader due to MongoDB connection failure.")
        return

    pairs_collection = db[config.MONGO_PAIRS_COLLECTION]
    
    # Query for pairs that need downloading (either Eng or Zh not downloaded successfully)
    # Limit to MAX_TRANSLATION_PAIRS as defined in config, effectively processing the first N pairs found by crawler.
    query = {
        "$or": [
            {"eng_download_status": {"$exists": False}},
            {"eng_download_status": {"$nin": ["downloaded", "no_url"]}},
            {"zh_download_status": {"$exists": False}},
            {"zh_download_status": {"$nin": ["downloaded", "no_url"]}}
        ]
    }
    
    # Fetch up to MAX_TRANSLATION_PAIRS that need processing.
    # The crawler aims to find this many; downloader will try to download them.
    pairs_to_download = list(pairs_collection.find(query).limit(config.MAX_TRANSLATION_PAIRS))
    
    if not pairs_to_download:
        print("No new translation pairs found to download, or all targeted pairs are processed.")
        # Check if we already have enough fully downloaded pairs
        fully_downloaded_pairs = pairs_collection.count_documents({
            "eng_download_status": "downloaded",
            "zh_download_status": "downloaded"
        })
        print(f"Currently {fully_downloaded_pairs} pairs fully downloaded.")
        if fully_downloaded_pairs >= config.MAX_TRANSLATION_PAIRS:
            print(f"Target of {config.MAX_TRANSLATION_PAIRS} fully downloaded pairs met or exceeded.")
        return
        
    print(f"Found {len(pairs_to_download)} translation pairs to process for download.")

    active_threads = []
    for pair_doc in pairs_to_download:
        # Manage overall thread count for pairs
        # Each pair might spawn 1 or 2 book download threads.
        # We use MAX_DOWNLOAD_THREADS for book downloads, so manage pair processing sequentially for simplicity here.
        # A more complex setup could use a semaphore for book download threads across all pairs.
        
        # For simplicity, process one pair at a time, allowing its internal threads to run.
        print(f"\nProcessing pair ID: {pair_doc['_id']} by Author: {pair_doc.get('author')}")
        download_book_pair(pair_doc, pairs_collection)
        time.sleep(1) # Small delay between processing pairs

    print("All targeted translation pair download tasks initiated.")
    if db.client:
        print("Closing MongoDB connection for downloader.")
        db.client.close()

# --- Original downloader for general books collection (can be kept for other uses) ---
def download_book_general(book_record, db_collection):
    title = book_record.get("title", "Unknown_Title")
    gutenberg_id = book_record.get("gutenberg_id", "Unknown_ID")
    lang_crawled = book_record.get("language_code_crawled", "unk_lang")
    
    download_url, preferred_format = None, None
    downloads = book_record.get("downloads", {})
    format_priority = ["text_utf8", "epub", "mobi", "html"] # Simplified from pair downloader
    for fmt_key in format_priority:
        if fmt_key in downloads:
            download_url = downloads[fmt_key]
            preferred_format = fmt_key
            break

    if not download_url:
        print(f"No suitable download URL for '{title}' (ID: {gutenberg_id}). Skipping.")
        db_collection.update_one({"_id": book_record["_id"]}, {"$set": {"download_status": "no_url"}})
        return

    base_filename = sanitize_filename(f"{gutenberg_id}_{lang_crawled}_{title}")
    try:
        response = requests.get(download_url, timeout=60, stream=True)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type')
        file_ext = get_file_extension_from_url(download_url, content_type, preferred_format)
        filepath = os.path.join(config.DOWNLOAD_DIR, f"{base_filename}{file_ext}")

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Thread {threading.get_ident()}: Successfully downloaded '{filepath}' (General)")
        db_collection.update_one(
            {"_id": book_record["_id"]},
            {"$set": {"download_status": "downloaded", "filepath": filepath, "format_downloaded": preferred_format}}
        )
    except Exception as e:
        print(f"Thread {threading.get_ident()}: Error downloading '{title}' (ID: {gutenberg_id}) (General): {e}")
        db_collection.update_one(
            {"_id": book_record["_id"]},
            {"$set": {"download_status": "error", "download_error": str(e)}}
        )

def main_general_download():
    db = get_db_client()
    if not db: return
    collection = db[config.MONGO_COLLECTION]
    query = {
        "language_code_crawled": {"$in": config.TARGET_LANGUAGES},
        "downloads": {"$exists": True, "$ne": {}},
        "$or": [{"download_status": {"$exists": False}}, {"download_status": {"$nin": ["downloaded", "no_url"]}}]
    }
    books_to_download = list(collection.find(query).limit(50)) # Limit for general downloads
    
    if not books_to_download:
        print("No general books found to download.")
        return
    print(f"Found {len(books_to_download)} general books to attempt downloading.")

    threads = []
    for book in books_to_download:
        while len(threads) >= config.MAX_DOWNLOAD_THREADS:
            time.sleep(0.5)
            threads = [t for t in threads if t.is_alive()]
        thread = threading.Thread(target=download_book_general, args=(book, collection))
        threads.append(thread)
        thread.start()
    for t in threads: t.join()
    print("All general download tasks completed.")
    if db.client: db.client.close()

if __name__ == "__main__":
    # Default to downloading translation pairs
    main_download_pairs()
    # To run general downloader:
    # main_general_download()
