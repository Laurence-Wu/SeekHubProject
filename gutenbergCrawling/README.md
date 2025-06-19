# Project Gutenberg Crawler

A comprehensive framework for crawling Project Gutenberg (https://www.gutenberg.org/) to collect English and Chinese books, find translation pairs, and download them using multi-threading.

## Features

- **Web Scraping**: Uses Selenium to crawl Project Gutenberg's website
- **Language Filtering**: Focuses on English and Chinese books
- **Translation Pairs**: Finds books by the same author in both languages
- **Multi-threading**: Parallel downloads for efficiency
- **MongoDB Storage**: Stores book metadata and download links
- **Content Filtering**: Excludes magazines, papers, and other non-book content
- **Robust Error Handling**: Handles network issues and website changes

## Prerequisites

- Python 3.8+
- MongoDB running on localhost:27017
- Chrome browser and ChromeDriver
- Virtual environment (recommended)

## Installation

1. **Clone/Setup the project:**
   ```bash
   cd gutenbergCrawling
   ```

2. **Run the setup script:**
   ```bash
   python setup.py
   ```

3. **Or manually set up:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.py` to customize settings:

```python
# MongoDB settings
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DATABASE = "gutenberg"
MONGO_PASSWORD = "123456.a"  # As requested

# Crawling limits
MAX_TRANSLATION_PAIRS = 10
MAX_ENGLISH_SEARCH_PAGES_FOR_PAIRS = 10

# Download settings
MAX_DOWNLOAD_THREADS = 5
DOWNLOAD_DIR = "downloaded_books"
```

## Usage

### Quick Start
```bash
# Run the complete pipeline (crawl + download)
python main.py

# Show database statistics
python main.py --mode stats
```

### Individual Components

**Crawler only:**
```bash
python main.py --mode crawler
# or directly:
python crawler.py
```

**Downloader only:**
```bash
python main.py --mode downloader
# or directly:
python downloader.py
```

**Test the crawler:**
```bash
python test_crawler.py
```

### Command Line Options

```bash
python main.py --help

Options:
  --mode {crawler,downloader,full,stats}  Operation mode (default: full)
  --type {pairs,general}                  Crawling type (default: pairs)
```

## How It Works

### 1. Crawler (`crawler.py`)
- Searches Project Gutenberg for English books
- Extracts author information from each book
- For each English author, searches for Chinese books by the same author
- Creates translation pairs and stores them in MongoDB
- Filters out non-book content (magazines, papers, etc.)

### 2. Downloader (`downloader.py`)
- Queries MongoDB for translation pairs
- Downloads books in multiple formats (TXT, EPUB, MOBI, HTML)
- Uses multi-threading for parallel downloads
- Organizes files by language and ID: `{ID}_{LANG}_{Title}.{ext}`

### 3. Database Structure

**Books Collection:**
```javascript
{
  "title": "Book Title",
  "author": "Author Name",
  "language": "English",
  "gutenberg_id": "12345",
  "downloads": {
    "text_utf8": "download_url",
    "epub": "download_url",
    "mobi": "download_url"
  },
  "language_code_crawled": "en"
}
```

**Translation Pairs Collection:**
```javascript
{
  "author": "Author Name",
  "eng_book_title": "English Title",
  "eng_gutenberg_id": "12345",
  "eng_downloads": {...},
  "zh_book_title": "Chinese Title", 
  "zh_gutenberg_id": "67890",
  "zh_downloads": {...},
  "eng_download_status": "downloaded",
  "zh_download_status": "downloaded"
}
```

## File Structure

```
gutenbergCrawling/
├── config.py          # Configuration settings
├── crawler.py         # Web scraping logic
├── downloader.py      # Download management
├── main.py           # Main orchestrator
├── setup.py          # Environment setup
├── test_crawler.py   # Testing utilities
├── requirements.txt  # Python dependencies
├── .gitignore       # Git ignore rules
└── downloaded_books/ # Downloaded files (created automatically)
```

## Error Handling

The system includes robust error handling for:
- Network timeouts and connection issues
- MongoDB connection failures
- WebDriver crashes
- File system errors
- Website structure changes

## Monitoring

The system provides detailed logging:
- Progress updates for each operation
- Error messages with context
- Database statistics
- Download status tracking

## Customization

### Adding New Languages
1. Update `TARGET_LANGUAGES` in `config.py`
2. Add language detection logic in `get_book_details()`
3. Update filename generation in downloader

### Changing Search Criteria
- Modify `non_book_keywords` in `get_book_details()`
- Adjust author matching logic in `find_translation_pairs()`
- Update download format priorities

### Performance Tuning
- Adjust `MAX_DOWNLOAD_THREADS` for download speed
- Modify `MAX_TRANSLATION_PAIRS` for dataset size
- Change page limits for broader/narrower searches

## Troubleshooting

**MongoDB Connection Issues:**
- Ensure MongoDB is running: `brew services start mongodb-community`
- Check connection string in config.py

**WebDriver Issues:**
- Install Chrome and ChromeDriver
- Update ChromeDriver to match Chrome version
- Check PATH configuration

**Download Failures:**
- Check internet connection
- Verify Project Gutenberg accessibility
- Increase timeout values in config

## License

This project is for educational purposes. Please respect Project Gutenberg's terms of service and implement appropriate rate limiting.
