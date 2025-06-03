from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from config import ZLIBRARY_BASE_URL

# Set up Chrome options (headless if you don't want the browser to pop up)
chrome_options = Options()
chrome_options.add_argument('--headless')  # comment out if you want to see the browser
chrome_options.add_argument('--disable-gpu')

# Initialize the driver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Open the webpage
    driver.get(ZLIBRARY_BASE_URL)
    # Optionally, wait a few seconds for JavaScript content to load
    time.sleep(3)
    # Get page source
    page = driver.page_source
finally:
    driver.quit()

# Now 'page' contains the full HTML of the page
print(page[:1000])  # Print the first 1000 characters as a sample
