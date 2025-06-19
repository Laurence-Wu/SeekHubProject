#!/usr/bin/env python3
"""
Setup script for the Gutenberg crawler project.
This script sets up the environment and tests basic functionality.
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Set up the Python virtual environment and install dependencies"""
    print("Setting up environment...")
    
    # Create virtual environment if it doesn't exist
    venv_path = Path("venv")
    if not venv_path.exists():
        print("Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    
    # Install requirements
    pip_path = venv_path / "bin" / "pip" if os.name != "nt" else venv_path / "Scripts" / "pip"
    print("Installing requirements...")
    subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
    
    print("✓ Environment setup complete")

def test_imports():
    """Test that all required imports work"""
    print("Testing imports...")
    try:
        import selenium
        import pymongo
        import requests
        import bs4
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_webdriver():
    """Test that WebDriver works"""
    print("Testing WebDriver...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.gutenberg.org")
        title = driver.title
        driver.quit()
        
        if "Project Gutenberg" in title:
            print("✓ WebDriver test successful")
            return True
        else:
            print("✗ WebDriver test failed - unexpected title")
            return False
            
    except Exception as e:
        print(f"✗ WebDriver test failed: {e}")
        print("Note: Chrome and ChromeDriver must be installed for Selenium to work")
        return False

def main():
    print("Gutenberg Crawler Setup")
    print("=" * 30)
    
    # Setup environment
    setup_environment()
    
    # Test imports
    if not test_imports():
        print("Setup failed - please check dependencies")
        return 1
    
    # Test WebDriver
    if not test_webdriver():
        print("WebDriver test failed - crawler may not work properly")
        print("Please ensure Chrome and ChromeDriver are installed")
    
    print("\nSetup complete!")
    print("You can now run the crawler with: python main.py")
    print("Or test individual components:")
    print("  python crawler.py")
    print("  python downloader.py")
    print("  python test_crawler.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
