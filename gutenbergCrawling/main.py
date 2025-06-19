#!/usr/bin/env python3
"""
Main runner for the Gutenberg crawler and downloader system.
This script orchestrates the entire process of crawling Project Gutenberg
for English and Chinese books, finding translation pairs, and downloading them.
"""

import sys
import os
import time
import argparse
from pymongo import MongoClient

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from crawler import main_general_crawl, main_find_pairs
from downloader import main_download_pairs, main_general_download

def check_mongodb_connection():
    """Check if MongoDB is accessible"""
    try:
        
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("✓ MongoDB connection successful")
        client.close()
        return True
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        print("Please ensure MongoDB is running on localhost:27017")
        return False

def setup_directories():
    """Create necessary directories"""
    if not os.path.exists(config.DOWNLOAD_DIR):
        os.makedirs(config.DOWNLOAD_DIR)
        print(f"✓ Created download directory: {config.DOWNLOAD_DIR}")
    else:
        print(f"✓ Download directory exists: {config.DOWNLOAD_DIR}")

def run_crawler(mode="pairs"):
    """Run the crawler"""
    print(f"\n{'='*50}")
    print(f"RUNNING CRAWLER (mode: {mode})")
    print(f"{'='*50}")
    
    if mode == "pairs":
        main_find_pairs()
    else:
        main_general_crawl()
    
    print("Crawler completed.")

def run_downloader(mode="pairs"):
    """Run the downloader"""
    print(f"\n{'='*50}")
    print(f"RUNNING DOWNLOADER (mode: {mode})")
    print(f"{'='*50}")
    
    if mode == "pairs":
        main_download_pairs()
    else:
        main_general_download()
    
    print("Downloader completed.")

def show_stats():
    """Show database statistics"""
    try:
        client = MongoClient(config.MONGO_URI)
        db = client[config.MONGO_DATABASE]
        
        books_count = db[config.MONGO_COLLECTION].count_documents({})
        pairs_count = db[config.MONGO_PAIRS_COLLECTION].count_documents({})
        downloaded_pairs = db[config.MONGO_PAIRS_COLLECTION].count_documents({
            "eng_download_status": "downloaded",
            "zh_download_status": "downloaded"
        })
        
        print(f"\n{'='*50}")
        print("DATABASE STATISTICS")
        print(f"{'='*50}")
        print(f"Total books in database: {books_count}")
        print(f"Translation pairs found: {pairs_count}")
        print(f"Fully downloaded pairs: {downloaded_pairs}")
        
        client.close()
    except Exception as e:
        print(f"Error getting stats: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gutenberg Crawler and Downloader")
    parser.add_argument("--mode", choices=["crawler", "downloader", "full", "stats"], 
                       default="full", help="Operation mode")
    parser.add_argument("--type", choices=["pairs", "general"], 
                       default="pairs", help="Crawling type")
    
    args = parser.parse_args()
    
    print("Project Gutenberg Crawler and Downloader")
    print("=" * 50)
    
    # Check prerequisites
    if not check_mongodb_connection():
        return 1
    
    setup_directories()
    
    if args.mode == "stats":
        show_stats()
        return 0
    
    try:
        if args.mode in ["crawler", "full"]:
            run_crawler(args.type)
            time.sleep(2)  # Brief pause between operations
        
        if args.mode in ["downloader", "full"]:
            run_downloader(args.type)
        
        show_stats()
        
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
        return 1
    except Exception as e:
        print(f"Error during execution: {e}")
        return 1
    
    print("\nAll operations completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
