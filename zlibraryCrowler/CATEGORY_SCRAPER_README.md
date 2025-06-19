# Category Scraper Usage Guide

## Overview
The `scrape_category.py` script automatically scrapes all categories from Z-Library's categories page (https://zh.z-lib.fm/categories) and performs year traversal searches for each category from 2000 to 2025.

## Features
- Automatically extracts all available categories from Z-Library
- Performs year traversal (2000-2025) for each category
- Uses stored cookies for authentication
- Saves category information to JSON files
- Stores all search results in the downloads folder
- Robust error handling and retry mechanisms
- Detailed logging and progress tracking

## Prerequisites
1. Make sure you have a `.env` file with your Z-Library credentials:
   ```
   EMAIL=your_email@example.com
   PASSWORD=your_password
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have logged in at least once to store cookies (run any other script first)

## Usage

### Run the Category Scraper
```bash
cd zlibraryCrowler
python scrape_category.py
```

### What the Script Does
1. **Login**: Uses stored cookies to authenticate with Z-Library
2. **Extract Categories**: Scrapes all categories from the categories page
3. **Save Category Info**: Stores category information in `output/downloads/zlibrary_categories_[timestamp].json`
4. **Year Traversal**: For each category:
   - Updates the book search name to the category name
   - Runs year traversal from 2000 to 2025
   - Calls the existing `unprocessesd_json_generator.py` for each year
   - Stores results in the `output/json/` folder

### Output Files
- **Category List**: `output/downloads/zlibrary_categories_[timestamp].json`
- **Search Results**: Multiple JSON files in `output/json/` folder, named according to the pattern:
  `zlibrary_crawler_[category_name]_[language]_[file_types]_[year]_[hash]_books.json`

### Configuration
The script uses the same configuration as other scripts in the project:
- Language: Set in `config.py` (default: "chinese")
- File Types: Set in `config.py` (default: ["EPUB", "PDF"])
- Max Pages: Set in `config.py` (default: 3000)

### Logging
The script provides detailed logging including:
- Category extraction progress
- Year traversal progress for each category
- Success/failure statistics
- Processing times
- Error messages with context

### Error Handling
- Automatic retry mechanisms for failed requests
- Session recovery if login is lost
- Graceful handling of interrupted searches
- Statistics tracking for successful/failed operations

## Example Output Structure
```
output/
├── downloads/
│   └── zlibrary_categories_1640995200.json
└── json/
    ├── zlibrary_crawler_Architecture_chinese_EPUB_PDF_2000_a1b2c3d4_books.json
    ├── zlibrary_crawler_Architecture_chinese_EPUB_PDF_2001_a1b2c3d4_books.json
    ├── zlibrary_crawler_Biology_chinese_EPUB_PDF_2000_e5f6g7h8_books.json
    └── ...
```

## Interrupting the Script
- Press `Ctrl+C` to safely interrupt the script
- The script will attempt to restore original configuration settings
- Already processed data will be preserved

## Troubleshooting
1. **Login Issues**: Ensure your `.env` file has correct credentials
2. **Timeout Errors**: The script uses generous timeouts, but slow networks may require adjustment
3. **Category Extraction Fails**: Check that you're logged in and the categories page is accessible
4. **Year Traversal Fails**: Individual year failures are logged but don't stop the overall process

## Performance Notes
- Processing all categories with full year traversal can take several hours
- Each category processes 26 years (2000-2025)
- Network speed and Z-Library's response time affect performance
- Consider running during off-peak hours for better performance
