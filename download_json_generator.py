from zlibraryCrowler.downloadFiles import download_books
from zlibraryCrowler.config import *
import os
import json
import asyncio


# Generate file names using config variables
json_file = get_short_output_filename("downloadLinks")
output_dir = DOWNLOADS_DIR.rstrip('/')  # Remove trailing slash if present

def find_valid_json_file():
    """Find a valid JSON file with download links"""
    # List of potential file patterns to check, in order of preference
    candidates = [
        get_short_output_filename("downloadLinks"),  # Standard pattern
        get_output_filename("downloadLinks"),  # Alternative pattern
    ]
    
    # Check for files in the output directory
    json_dir = OUTPUT_DIR
    if os.path.exists(json_dir):
        # Add any files ending with '_downloadLinks.json' from the directory
        dir_files = [f for f in os.listdir(json_dir) if f.endswith('_downloadLinks.json')]
        for file in dir_files:
            full_path = os.path.join(json_dir, file)
            if full_path not in candidates:
                candidates.append(full_path)
    # Check each candidate file
    for candidate in candidates:
        if os.path.exists(candidate):
            try:
                # Verify the file has valid content
                with open(candidate, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        print(f"✅ Found valid JSON file: {candidate}")
                        return candidate
                    else:
                        print(f"⚠️ File exists but is empty: {candidate}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ File exists but has issues: {candidate} - {e}")
    return None

# Check if JSON file exists before proceeding
json_file = find_valid_json_file()

# Scan output directory to see what files already exist
print(f"📁 Scanning output directory: {output_dir}")
if os.path.exists(output_dir):
    existing_files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
    print(f"Found {len(existing_files)} existing files in output directory")
else:
    print("Output directory does not exist, will be created during download")
    existing_files = []

# Load JSON file to check how many downloads are expected
try:
    with open(json_file, 'r', encoding='utf-8') as f:
        books_data = json.load(f)
    
    total_expected_downloads = 0
    for book in books_data:
        download_links = book.get('download_links', [])
        total_expected_downloads += len(download_links)
    
    print(f"📊 Download Summary:")
    print(f"  - Expected downloads: {total_expected_downloads}")
    print(f"  - Existing files: {len(existing_files)}")
    print(f"  - Potentially remaining: {max(0, total_expected_downloads - len(existing_files))}")
    
    
except Exception as e:
    print(f"❌ Error reading JSON file: {e}")
    exit(1)

# First, let's check one of the existing files to see what we actually downloaded
# Use config variables to construct the expected file path
book_title = BOOK_NAME_TO_SEARCH.replace(' ', '_').title()
file_extension = '_'.join(PREFERRED_FILE_TYPES) if PREFERRED_FILE_TYPES else "EPUB"
existing_file = f"{output_dir}/{book_title}.{file_extension}"

if os.path.exists(existing_file):
    print(f"✅ Checking existing file: {existing_file}")
else:
    print(f"📄 Expected file not found: {existing_file}")

print(f"📂 Using JSON file: {json_file}")
print(f"📁 Output directory: {output_dir}")
print(f"🚀 Starting download process...")

asyncio.run(download_books(json_file, output_dir))


# Remove the book file after download completion
books_json_to_remove = get_short_output_filename()
if os.path.exists(books_json_to_remove):
    try:
        os.remove(books_json_to_remove)
        print(f"🗑️ Removed file: {books_json_to_remove}")
    except Exception as e:
        print(f"❌ Error removing file {books_json_to_remove}: {e}")
else:
    print(f"📄 File not found to remove: {books_json_to_remove}")
