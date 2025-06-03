import os
import pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .config import ZLIBRARY_BASE_URL

def perform_login(driver, wait, cookies_file, email, password):
    """
    Handles the login process for Z-Library, using cookies if available,
    otherwise performing a manual login.

    Args:
        driver: The Selenium WebDriver instance.
        wait: The Selenium WebDriverWait instance.
        cookies_file (str): Path to the cookies file.
        email (str): The user's email for login.
        password (str): The user's password for login.

    Returns:
        bool: True if login was successful, False otherwise.
    """
    login_successful = False

    # Try to load cookies if they exist
    if os.path.exists(cookies_file):
        try:
            # First visit the domain (required before adding cookies)
            driver.get(ZLIBRARY_BASE_URL)
            
            # Load cookies
            cookies = pickle.load(open(cookies_file, 'rb'))
            for cookie in cookies:
                driver.add_cookie(cookie)
            
            # Refresh page to apply cookies
            driver.refresh()
            
            # Check if we're logged in
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "logout")]'))
                )
                login_successful = True
                print("Login successful from saved cookies!")
            except:
                print("Saved cookies expired or invalid, proceeding with manual login.")
                login_successful = False
        except Exception as e:
            print(f"Error loading cookies: {e}")
            login_successful = False

    # If not logged in with cookies, try manual login
    if not login_successful:
        try:
            driver.get(f'{ZLIBRARY_BASE_URL}/login')

            # Wait for the login form
            email_input = wait.until(EC.presence_of_element_located((By.NAME, 'email')))
            password_input = driver.find_element(By.NAME, 'password')

            # Fill and submit the login form
            email_input.clear()
            email_input.send_keys(email)
            password_input.clear()
            password_input.send_keys(password)
            login_button = driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "登录")]')
            login_button.click()

            # Wait until the logout link appears
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "logout")]'))
            )
            login_successful = True
            print("Login successful!")
            
            # Save cookies for future use
            pickle.dump(driver.get_cookies(), open(cookies_file, 'wb'))
            
        except Exception as e:
            login_successful = False
            print(f"Error during manual login: {e}")
            # It's possible the login was successful but an error occurred after,
            # e.g., saving cookies. Double check if still logged in.
            try:
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.XPATH, '//a[contains(@href, "logout")]'))
                )
                login_successful = True # If logout link is found, login was successful
                if not os.path.exists(cookies_file): # If cookies were not saved due to error
                     pickle.dump(driver.get_cookies(), open(cookies_file, 'wb'))
            except:
                 login_successful = False


    return login_successful
