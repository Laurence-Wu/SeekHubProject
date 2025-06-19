# Z-Library Booklist Scraper

This script scrapes booklists from Z-Library (https://zh.z-lib.fm/booklists) and extracts all books from each booklist along with their download links.

## Features

- **Booklist Discovery**: Automatically finds all booklists on the Z-Library booklists page
- **Complete Book Extraction**: Scrapes all books from each booklist (handles pagination)
- **Metadata Collection**: Extracts book metadata including title, author, file type, file size, etc.
- **Download Links**: Optionally extracts download links for each book
- **JSON Output**: Saves each booklist as a separate JSON file in the `output/json` folder

## Files

- `zlibrary_booklist_scraper.py` - Main scraper script
- `test_booklist_scraper.py` - Test script to verify functionality
- `booklist_scraper.py` - Alternative implementation (more detailed)

## Prerequisites

1. **Environment Setup**: Make sure you have a `.env` file with your Z-Library credentials:
   ```
   EMAIL=your_zlibrary_email@example.com
   PASSWORD=your_zlibrary_password
   ```

2. **Dependencies**: Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Chrome Driver**: Make sure Chrome is installed (Selenium will handle the driver automatically)

## Usage

### Quick Test (Recommended First)

Test the scraper functionality before running a full scrape:

```bash
python test_booklist_scraper.py
```

This will:
- Test login functionality
- Scrape the booklists page to find available booklists
- Test scraping one booklist completely
- Verify JSON output functionality

### Full Scraping

Run the complete scraper:

```bash
python zlibrary_booklist_scraper.py
```

By default, this will:
- Scrape the first 3 booklists (configurable)
- Extract all books from each booklist
- Get download links for each book
- Save each booklist as a separate JSON file

### Configuration

You can modify the scraping behavior by editing the `main()` function in `zlibrary_booklist_scraper.py`:

```python
scraper.run_full_scraping(
    max_booklists=3,        # Number of booklists to scrape (None = all)
    extract_download_links=True  # Whether to get download links
)
```

## Output Structure

Each booklist is saved as a JSON file in `output/json/` with the following structure:

```json
{
  "booklist_metadata": {
    "title": "101 books",
    "url": "https://zh.z-lib.fm/booklist/27086/cc3f23/101-books.html",
    "booklist_id": "27086",
    "creator": {
      "name": "sigh",
      "id": "9709971",
      "profile_url": "https://zh.z-lib.fm/profile/9709971/b36150"
    },
    "stats": {
      "book_count": "53",
      "views": "124k",
      "comments": "39"
    },
    "label": "Editor's Choice",
    "preview_books": [...]
  },
  "scraping_info": {
    "scraped_at": "2025-06-18T10:30:00",
    "total_books_found": 53,
    "scraper_version": "1.0",
    "source_url": "https://zh.z-lib.fm/booklist/27086/cc3f23/101-books.html"
  },
  "books": [
    {
      "id": "2316106",
      "title": "Astronomy 101",
      "author": "Carolyn Collins Petersen",
      "language": "english",
      "file_type": "PDF",
      "file_size": "10.2 MB",
      "year": "2013",
      "book_page_url": "https://zh.z-lib.fm/book/2316106/d5e171/astronomy-101.html",
      "download_url": "https://...",
      "download_links": [...]
    }
  ]
}
```

## How It Works

1. **Login**: Authenticates with Z-Library using credentials from `.env`

2. **Booklist Discovery**: 
   - Navigates to `https://zh.z-lib.fm/booklists`
   - Parses all booklist content divs (like the example you provided)
   - Extracts metadata: title, creator, stats, preview books

3. **Individual Booklist Scraping**:
   - Visits each booklist URL
   - Handles pagination to get all books
   - Extracts book information from each page

4. **Download Link Extraction**:
   - Uses the existing `process_books_selenium_fallback` function
   - Gets actual download URLs for each book

5. **JSON Output**:
   - Saves each booklist as a separate timestamped JSON file
   - Includes both metadata and complete book data

## Customization

### Targeting Specific Booklist Types

The scraper finds all booklists, but you can filter by labels:

```python
# In the scraping loop, add filtering logic
if booklist_metadata.get('label') == "Editor's Choice":
    # Only scrape Editor's Choice booklists
    ...
```

### Limiting Books per Booklist

To limit the number of books scraped from each booklist, modify the pagination logic in `scrape_individual_booklist()`.

### Different Output Formats

The `save_booklist_to_json()` method can be modified to output in different formats (CSV, XML, etc.).

## Error Handling

The scraper includes robust error handling:
- Automatic retry on connection failures  
- Graceful handling of missing elements
- Detailed logging of progress and errors
- Session management and re-login if needed

## Performance Considerations

- **Rate Limiting**: Built-in delays between requests to avoid overwhelming the server
- **Headless Browser**: Runs in headless mode by default for better performance
- **Concurrent Processing**: Download link extraction can be configured for concurrent requests

## Troubleshooting

### Common Issues

1. **Login Failed**: Check your `.env` file credentials
2. **No Booklists Found**: The page structure might have changed
3. **Timeout Errors**: Increase `BROWSER_TIMEOUT` in config.py
4. **Memory Issues**: Reduce `max_booklists` parameter for large-scale scraping

### Debug Mode

Set `USE_HEADLESS_BROWSER = False` in `config.py` to see the browser in action and debug issues.

## Legal and Ethical Considerations

- Respect the website's terms of service
- Use reasonable delays between requests
- Don't overload the server with too many concurrent requests
- Consider the impact of large-scale scraping on the service

## Support

For issues or questions, check:
1. The test script output for diagnostic information
2. Browser console for JavaScript errors (when not in headless mode)
3. The existing Z-Library crawler configuration in `zlibraryCrowler/config.py`
