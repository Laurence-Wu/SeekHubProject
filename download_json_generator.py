from zlibraryCrowler.downloadFiles import download_books
from zlibraryCrowler.config import *
import os
import json
import asyncio


def find_all_json_files():
    """Find all valid JSON files with download links in the json directory"""
    json_files = []
    json_dir = OUTPUT_DIR
    
    if not os.path.exists(json_dir):
        print(f"❌ JSON directory does not exist: {json_dir}")
        return []
    
    # Get all JSON files from the directory
    all_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
    
    for filename in all_files:
        file_path = os.path.join(json_dir, filename)
        try:
            # Verify the file has valid content and download links
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    # Check if any book has download links
                    has_download_links = any(
                        book.get('download_links') and len(book.get('download_links', [])) > 0
                        for book in data
                    )
                    if has_download_links:
                        json_files.append(file_path)
                        print(f"✅ Found valid JSON file with download links: {filename}")
                    else:
                        print(f"⚠️ No download links found in: {filename} (skipping)")
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Invalid JSON file: {filename} - {e}")
    
    return json_files


async def process_json_file(json_file, output_dir):
    """Process a single JSON file and download books"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            books_data = json.load(f)
        
        total_expected_downloads = sum(
            len(book.get('download_links', [])) for book in books_data
        )
        
        print(f"📂 Processing: {os.path.basename(json_file)}")
        print(f"📊 Expected downloads: {total_expected_downloads}")
        
        # Download books from this JSON file
        await download_books(json_file, output_dir)
        
        # Remove the JSON file after successful download
        try:
            os.remove(json_file)
            print(f"🗑️ Removed: {os.path.basename(json_file)}")
        except Exception as e:
            print(f"❌ Error removing {json_file}: {e}")
            
    except Exception as e:
        print(f"❌ Error processing {json_file}: {e}")


async def main():
    """Main function to process all JSON files"""
    output_dir = DOWNLOADS_DIR.rstrip('/')
    
    # Find all JSON files with download links
    json_files = find_all_json_files()
    
    if not json_files:
        print("❌ No valid JSON files found with download links")
        return
    
    print(f"🚀 Found {len(json_files)} JSON files to process")
    
    # Process each JSON file
    for i, json_file in enumerate(json_files, 1):
        print(f"\n--- Processing file {i}/{len(json_files)} ---")
        await process_json_file(json_file, output_dir)
    
    print(f"\n✅ Completed processing all {len(json_files)} JSON files")


if __name__ == "__main__":
    asyncio.run(main())
