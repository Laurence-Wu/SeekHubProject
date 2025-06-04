# Z-Library Crawler Project

A comprehensive Python-based web scraping tool for searching, extracting, and downloading books from Z-Library (zh.z-lib.fm). This project provides automated book discovery, metadata extraction, download link generation, and file management capabilities.

## 🚀 Overview

This project is designed to automate the process of searching for books on Z-Library, extracting detailed metadata, generating download links, and organizing the results. It features advanced filtering capabilities, year-based traversal, book name matching algorithms, and comprehensive configuration options.

## ✨ Key Features

### 🔍 **Advanced Search & Filtering**
- **Multi-criteria Search**: Search by book name, author, language, file type, publication year, and content type
- **Fuzzy Match Control**: Option to include or exclude fuzzy search matches
- **File Type Filtering**: Support for EPUB, PDF, MOBI, AZW3, TXT, FB2, RTF formats
- **Language Preferences**: Target specific languages (e.g., Chinese, English)
- **Publication Year Filtering**: Search within specific year ranges
- **Content Type Selection**: Filter between books and articles

### 📊 **Data Extraction & Management**
- **Comprehensive Metadata**: Extract title, author, language, file size, format, and URLs
- **JSON Output**: Structured data storage with configurable file naming
- **Batch Processing**: Handle multiple search queries and pagination
- **Download Link Generation**: Both synchronous and asynchronous methods
- **Session Management**: Persistent login and cookie handling

### 🤖 **Automation Features**
- **Year Traversal**: Automatically search across multiple years (2000-2025)
- **Selenium WebDriver**: Headless browser automation with Chrome
- **Rate Limiting**: Configurable delays to avoid detection
- **Retry Logic**: Automatic retry on failed requests
- **Progress Tracking**: Detailed logging and statistics

### 📚 **Book Name Matching**
- **RapidFuzz Integration**: Advanced fuzzy string matching
- **Name Extraction**: Extract book names from output JSON files
- **Similarity Scoring**: Intelligent book name comparison
- **Duplicate Detection**: Identify similar or duplicate entries

## 📁 Project Structure

```
SeekHubProject/
├── README.md                           # This file
├── requirements.txt                    # Python dependencies
├── .gitignore                         # Git ignore patterns
├── traversal_year.py                  # Year-based search automation
├── unprocessesd_json_generator.py     # Raw search data generator
├── download_json_generator.py         # Download link generator
├── processesd_json_generator.py       # Processed data generator
├── OS_function_tests.py              # System function tests
├── output/                           # Generated output files
│   ├── json/                        # Search result JSON files
│   ├── auth/                        # Authentication data (cookies)
│   └── downloads/                   # Downloaded book files
└── zlibraryCrowler/                  # Main crawler package
    ├── __init__.py
    ├── main.py                      # Basic web driver setup
    ├── config.py                    # Comprehensive configuration
    ├── .env.example                 # Environment variables template
    ├── login.py                     # Authentication management
    ├── search.py                    # Search functionality
    ├── getSearchDownloadLinks.py    # Download link extraction
    ├── downloadFiles.py             # File download management
    ├── getCookies.py                # Cookie handling
    ├── textProcess.py               # Text processing utilities
    └── bookNameMatching/            # Book matching algorithms
        ├── ExtractNamesFromOutputJson.py  # Name extraction
        └── rapidFuzzMatching.py           # Fuzzy matching
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Chrome browser (for Selenium WebDriver)
- Z-Library account credentials

### 1. Clone the Repository
```bash
git clone <repository-url>
cd SeekHubProject
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
# Copy the environment template
cp zlibraryCrowler/.env.example zlibraryCrowler/.env

# Edit the .env file with your credentials
EMAIL=your_email@example.com
PASSWORD=your_password
```

### 4. Configure Search Parameters
Edit `zlibraryCrowler/config.py` to set your preferences:

```python
# Basic search configuration
BOOK_NAME_TO_SEARCH = "Python Programming"
PREFERRED_LANGUAGE = "english"
PREFERRED_FILE_TYPES = ["PDF", "EPUB"]
PREFERRED_YEAR = 2020
MAX_PAGES_TO_SCRAPE = 5

# Advanced options
INCLUDE_FUZZY_MATCHES = False
USE_HEADLESS_BROWSER = True
MAX_CONCURRENT_REQUESTS = 3
```

## 🚀 Usage

### Basic Search
```bash
# Generate unprocessed search results
python unprocessesd_json_generator.py

# Extract download links
python download_json_generator.py

# Process and clean data
python processesd_json_generator.py
```

### Year Traversal (Automated)
```bash
# Search across all years from 2000-2025
python traversal_year.py
```

### Book Name Matching
```bash
# Extract book names from JSON files
python zlibraryCrowler/bookNameMatching/ExtractNamesFromOutputJson.py

# Perform fuzzy matching
python zlibraryCrowler/bookNameMatching/rapidFuzzMatching.py
```

## ⚙️ Configuration Options

### Search Parameters
| Parameter | Description | Options |
|-----------|-------------|---------|
| `BOOK_NAME_TO_SEARCH` | Target book name | String or None |
| `PREFERRED_LANGUAGE` | Language filter | "chinese", "english", etc. |
| `PREFERRED_FILE_TYPES` | File format filters | ["EPUB", "PDF", "MOBI", "AZW3", "TXT", "FB2", "RTF"] |
| `PREFERRED_YEAR` | Publication year | Integer (0 to ignore) |
| `PREFERRED_CONTENT_TYPES` | Content type filter | ["book", "article"] |
| `PREFERRED_ORDER` | Result ordering | "popular", "bestmatch", "newest", "oldest" |
| `MAX_PAGES_TO_SCRAPE` | Maximum pages to process | Integer |
| `INCLUDE_FUZZY_MATCHES` | Include fuzzy matches | Boolean |

### Performance Settings
| Parameter | Description | Default |
|-----------|-------------|---------|
| `USE_HEADLESS_BROWSER` | Run browser in background | True |
| `MAX_CONCURRENT_REQUESTS` | Async request limit | 3 |
| `REQUEST_DELAY` | Delay between requests (seconds) | 1 |
| `MAX_RETRIES` | Maximum retry attempts | 5 |
| `BROWSER_TIMEOUT` | WebDriver timeout (seconds) | 10 |

### Output Configuration
| Parameter | Description | Default |
|-----------|-------------|---------|
| `OUTPUT_FOLDERS['json']` | JSON output directory | `./output/json/` |
| `OUTPUT_FOLDERS['auth']` | Authentication data directory | `./output/auth/` |
| `OUTPUT_FOLDERS['downloads']` | Downloaded files directory | `./output/downloads/` |
| `PROCESS_NAME` | File naming prefix | "zlibrary_crawler" |

## 📊 Output Files

### JSON Structure
```json
{
  "id": "book_unique_id",
  "title": "Book Title",
  "author": "Author Name",
  "language": "english",
  "file_type": "PDF",
  "file_size": "2.5 MB",
  "book_page_url": "https://zh.z-lib.fm/book/...",
  "download_url": "https://zh.z-lib.fm/dl/...",
  "download_links": [...]
}
```

### File Naming Convention
- **Search Results**: `{process_name}_{book_name}_{language}_{file_types}_{year}_{hash}_books.json`
- **Download Links**: `{process_name}_{book_name}_{language}_{file_types}_{year}_{hash}_download_links.json`
- **Downloaded Files**: `{process_name}_{original_filename}.{extension}`

## 🔧 Advanced Features

### Async Download Link Extraction
The project supports both synchronous (Selenium) and asynchronous (aiohttp) methods for extracting download links:

```python
# Enable async extraction in config.py
USE_ASYNC_EXTRACTION = True
MAX_CONCURRENT_REQUESTS = 3
```

### Rate Limiting & Bot Detection Avoidance
- Configurable delays between requests
- Browser automation controls
- User-agent rotation
- Session persistence

### Error Handling & Logging
- Comprehensive error logging
- Retry mechanisms
- Progress tracking
- Statistics reporting

### Book Name Matching Algorithms
- **RapidFuzz**: Advanced fuzzy string matching
- **Similarity Scoring**: Intelligent comparison metrics
- **Batch Processing**: Handle multiple book comparisons

## 🛡️ Security & Best Practices

### Authentication
- Store credentials in `.env` file (never commit to version control)
- Session cookies are automatically managed and persisted
- Login status verification on each page navigation

### Rate Limiting
```python
# Recommended settings to avoid being blocked
REQUEST_DELAY = 1          # 1 second between requests
PAGE_LOAD_DELAY = 2        # 2 seconds after page loads
MAX_CONCURRENT_REQUESTS = 3 # Maximum simultaneous requests
```

### Legal Considerations
- This tool is for educational and research purposes
- Respect Z-Library's terms of service
- Use reasonable request rates to avoid server overload
- Ensure you have proper rights to download content

## 🚨 Troubleshooting

### Common Issues

#### 1. Login Failures
```python
# Check credentials in .env file
EMAIL=your_correct_email@domain.com
PASSWORD=your_correct_password

# Verify Z-Library website availability
ZLIBRARY_BASE_URL = "https://zh.z-lib.fm"
```

#### 2. WebDriver Issues
```bash
# Update Chrome WebDriver
pip install --upgrade webdriver-manager

# Verify Chrome browser installation
google-chrome --version  # Linux
# or check Chrome installation on Windows/Mac
```

#### 3. Rate Limiting
```python
# Increase delays in config.py
REQUEST_DELAY = 2
PAGE_LOAD_DELAY = 3
MAX_CONCURRENT_REQUESTS = 2
```

#### 4. Memory Issues with Large Datasets
```python
# Reduce concurrent operations
MAX_CONCURRENT_REQUESTS = 1
MAX_PAGES_TO_SCRAPE = 3

# Process in smaller batches
# Use year traversal for systematic processing
```

## 📈 Performance Optimization

### For Large-Scale Operations
1. **Use Year Traversal**: Process data year by year to manage memory
2. **Enable Async Processing**: Use `USE_ASYNC_EXTRACTION = True`
3. **Optimize Concurrency**: Balance `MAX_CONCURRENT_REQUESTS` vs. rate limits
4. **Monitor Output Sizes**: Large JSON files may need processing in chunks

### Memory Management
```python
# Recommended settings for large datasets
MAX_PAGES_TO_SCRAPE = 5     # Limit pages per search
MAX_CONCURRENT_REQUESTS = 2  # Reduce concurrent operations
USE_HEADLESS_BROWSER = True  # Save memory
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is for educational and research purposes. Please ensure compliance with Z-Library's terms of service and applicable copyright laws.

## 🆘 Support

For issues, questions, or contributions:
1. Check the troubleshooting section above
2. Review the configuration options
3. Create an issue with detailed error logs
4. Include your environment details (Python version, OS, etc.)

---

**⚠️ Disclaimer**: This tool is intended for educational and research purposes. Users are responsible for ensuring compliance with all applicable laws and terms of service. The developers are not responsible for any misuse of this software.
