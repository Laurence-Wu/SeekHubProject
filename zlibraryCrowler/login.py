import os
import pickle
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from .config import ZLIBRARY_BASE_URL, MAX_RETRIES, RETRY_DELAY, SELECTORS

# Configure logging for login operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_login_status(driver, timeout=5):
    """
    Verify if the user is currently logged in by checking for logout link.
    
    Args:
        driver: The Selenium WebDriver instance.
        timeout (int): Timeout for waiting for logout link.
    
    Returns:
        bool: True if logged in, False otherwise.
    """
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, SELECTORS['logout_link']))
        )
        return True
    except TimeoutException:
        return False
    except Exception as e:
        logger.warning(f"Unexpected error while verifying login status: {e}")
        return False


def save_cookies_safely(driver, cookies_file, max_attempts=3):
    """
    Safely save cookies with multiple attempts and error handling.
    
    Args:
        driver: The Selenium WebDriver instance.
        cookies_file (str): Path to save cookies.
        max_attempts (int): Maximum number of save attempts.
    
    Returns:
        bool: True if cookies were saved successfully, False otherwise.
    """
    for attempt in range(max_attempts):
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(cookies_file), exist_ok=True)
            
            # Save cookies
            with open(cookies_file, 'wb') as f:
                pickle.dump(driver.get_cookies(), f)
            
            # Verify the file was created and is not empty
            if os.path.exists(cookies_file) and os.path.getsize(cookies_file) > 0:
                logger.info(f"Cookies saved successfully to {cookies_file}")
                return True
            else:
                raise Exception("Cookie file is empty or wasn't created")
                
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} to save cookies failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(1)  # Brief delay before retry
            else:
                logger.error(f"Failed to save cookies after {max_attempts} attempts")
    
    return False


def load_cookies_safely(driver, cookies_file):
    """
    Safely load cookies with error handling.
    
    Args:
        driver: The Selenium WebDriver instance.
        cookies_file (str): Path to cookies file.
    
    Returns:
        bool: True if cookies were loaded successfully, False otherwise.
    """
    try:
        if not os.path.exists(cookies_file):
            logger.info("No cookies file found")
            return False
        
        # Check if file is not empty
        if os.path.getsize(cookies_file) == 0:
            logger.warning("Cookies file is empty, removing it")
            os.remove(cookies_file)
            return False
        
        # Load and apply cookies
        with open(cookies_file, 'rb') as f:
            cookies = pickle.load(f)
        
        if not cookies:
            logger.warning("No cookies found in file")
            return False
        
        # Add cookies to driver
        for cookie in cookies:
            try:
                # Ensure cookie is properly formatted
                if 'name' in cookie and 'value' in cookie:
                    driver.add_cookie(cookie)
            except Exception as cookie_error:
                logger.warning(f"Failed to add cookie {cookie.get('name', 'unknown')}: {cookie_error}")
        
        logger.info(f"Successfully loaded {len(cookies)} cookies")
        return True
        
    except (pickle.UnpicklingError, EOFError) as e:
        logger.warning(f"Corrupted cookies file: {e}. Removing file.")
        try:
            os.remove(cookies_file)
        except:
            pass
        return False
    except Exception as e:
        logger.error(f"Error loading cookies: {e}")
        return False


def attempt_manual_login(driver, wait, email, password, max_attempts=3):
    """
    Attempt manual login with retry mechanism.
    
    Args:
        driver: The Selenium WebDriver instance.
        wait: The Selenium WebDriverWait instance.
        email (str): User email.
        password (str): User password.
        max_attempts (int): Maximum login attempts.
    
    Returns:
        bool: True if login successful, False otherwise.
    """
    for attempt in range(max_attempts):
        try:
            logger.info(f"Manual login attempt {attempt + 1}/{max_attempts}")
            
            # Navigate to login page
            driver.get(f'{ZLIBRARY_BASE_URL}/login')
            
            # Wait for page to load and check for different possible states
            try:
                # Check if we're already logged in (redirect happened)
                if verify_login_status(driver, timeout=3):
                    logger.info("Already logged in after navigating to login page")
                    return True
            except:
                pass
            
            # Wait for login form elements
            try:
                email_input = wait.until(EC.element_to_be_clickable((By.NAME, 'email')))
            except TimeoutException:
                # Try alternative selectors
                try:
                    email_input = wait.until(EC.element_to_be_clickable((By.ID, 'email')))
                except TimeoutException:
                    logger.error("Could not find email input field")
                    continue
            
            try:
                password_input = driver.find_element(By.NAME, 'password')
            except NoSuchElementException:
                try:
                    password_input = driver.find_element(By.ID, 'password')
                except NoSuchElementException:
                    logger.error("Could not find password input field")
                    continue
            
            # Clear and fill form fields
            email_input.clear()
            time.sleep(0.5)  # Brief delay to ensure field is cleared
            email_input.send_keys(email)
            
            password_input.clear()
            time.sleep(0.5)
            password_input.send_keys(password)
            
            # Find and click login button with multiple selector strategies
            login_button = None
            button_selectors = [
                '//button[@type="submit" and contains(text(), "登录")]',
                '//button[@type="submit"]',
                '//input[@type="submit"]',
                '//button[contains(@class, "login")]',
                '//button[contains(@class, "submit")]'
            ]
            
            for selector in button_selectors:
                try:
                    login_button = driver.find_element(By.XPATH, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not login_button:
                logger.error("Could not find login button")
                continue
            
            # Click login button
            login_button.click()
            
            # Wait for login to complete with extended timeout
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, SELECTORS['logout_link']))
                )
                logger.info("Manual login successful!")
                return True
                
            except TimeoutException:
                # Check for error messages or other indicators
                try:
                    error_elements = driver.find_elements(By.CLASS_NAME, 'error')
                    if error_elements:
                        error_text = error_elements[0].text
                        logger.warning(f"Login error message: {error_text}")
                except:
                    pass
                
                logger.warning(f"Login attempt {attempt + 1} timed out")
                
        except WebDriverException as e:
            logger.error(f"WebDriver error during login attempt {attempt + 1}: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error during login attempt {attempt + 1}: {e}")
        
        # Wait before retry (except on last attempt)
        if attempt < max_attempts - 1:
            logger.info(f"Waiting {RETRY_DELAY} seconds before retry...")
            time.sleep(RETRY_DELAY)
    
    logger.error(f"Manual login failed after {max_attempts} attempts")
    return False


def perform_login(driver, wait, cookies_file, email, password, max_retries=None):
    """
    Enhanced login function with comprehensive error handling and retry mechanisms.

    Args:
        driver: The Selenium WebDriver instance.
        wait: The Selenium WebDriverWait instance.
        cookies_file (str): Path to the cookies file.
        email (str): The user's email for login.
        password (str): The user's password for login.
        max_retries (int): Maximum number of overall retry attempts.

    Returns:
        bool: True if login was successful, False otherwise.
    """
    if max_retries is None:
        max_retries = MAX_RETRIES
    
    logger.info("Starting login process...")
    
    # Validate inputs
    if not email or not password:
        logger.error("Email or password not provided")
        return False
    
    for overall_attempt in range(max_retries):
        try:
            logger.info(f"Overall login attempt {overall_attempt + 1}/{max_retries}")
            
            # Step 1: Try to load and use existing cookies
            cookies_loaded = False
            if os.path.exists(cookies_file):
                try:
                    # Navigate to base URL first
                    driver.get(ZLIBRARY_BASE_URL)
                    time.sleep(2)  # Allow page to load
                    
                    # Load cookies
                    if load_cookies_safely(driver, cookies_file):
                        # Refresh page to apply cookies
                        driver.refresh()
                        time.sleep(3)  # Allow page to load with cookies
                        
                        # Verify login status
                        if verify_login_status(driver, timeout=8):
                            logger.info("Login successful using saved cookies!")
                            return True
                        else:
                            logger.info("Cookies loaded but login verification failed")
                    
                except Exception as e:
                    logger.warning(f"Error during cookie-based login: {e}")
            
            # Step 2: Attempt manual login if cookies failed
            logger.info("Attempting manual login...")
            if attempt_manual_login(driver, wait, email, password):
                # Save cookies after successful login
                if save_cookies_safely(driver, cookies_file):
                    logger.info("Cookies saved for future use")
                else:
                    logger.warning("Login successful but cookies could not be saved")
                return True
            
        except WebDriverException as e:
            logger.error(f"WebDriver error in overall attempt {overall_attempt + 1}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in overall attempt {overall_attempt + 1}: {e}")
        
        # Wait before overall retry (except on last attempt)
        if overall_attempt < max_retries - 1:
            logger.info(f"Waiting {RETRY_DELAY * 2} seconds before next overall attempt...")
            time.sleep(RETRY_DELAY * 2)
    
    logger.error(f"Login failed after {max_retries} overall attempts")
    return False


def handle_login_session_loss(driver, wait, cookies_file, email, password):
    """
    Handle login session loss during operations with automatic re-login.
    
    Args:
        driver: The Selenium WebDriver instance.
        wait: The Selenium WebDriverWait instance.
        cookies_file (str): Path to cookies file.
        email (str): User email.
        password (str): User password.
    
    Returns:
        bool: True if re-login successful, False otherwise.
    """
    logger.warning("Login session appears to be lost. Attempting re-login...")
    
    # Remove old cookies file as it's likely invalid
    try:
        if os.path.exists(cookies_file):
            os.remove(cookies_file)
            logger.info("Removed invalid cookies file")
    except Exception as e:
        logger.warning(f"Could not remove old cookies file: {e}")
    
    # Attempt fresh login
    return perform_login(driver, wait, cookies_file, email, password, max_retries=2)
