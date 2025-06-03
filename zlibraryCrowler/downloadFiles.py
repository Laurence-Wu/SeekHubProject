import json
import os
import asyncio
import aiohttp
import aiofiles
import pickle
import random
import subprocess
from .config import ZLIBRARY_BASE_URL


class ZLibraryDownloader:
    """Simplified Z-Library downloader with proxy pool support structure."""
    
    def __init__(self, cookies_file="zlibrary_cookies.pkl", proxy_pool=None):
        self.cookies_file = cookies_file
        self.proxy_pool = proxy_pool  # Future proxy pool implementation
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
    
    @staticmethod
    def sanitize_filename(filename):
        """Make filename safe for filesystem."""
        replacements = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in replacements:
            filename = filename.replace(char, '_')
        return filename
    
    def _load_cookies(self):
        """Load and format cookies from pickle file."""
        if not os.path.exists(self.cookies_file):
            return {}
        
        try:
            with open(self.cookies_file, 'rb') as f:
                cookies_data = pickle.load(f)
                
            # Convert various cookie formats to dict
            if isinstance(cookies_data, dict):
                return cookies_data
            
            formatted_cookies = {}
            for cookie in cookies_data:
                if hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                    formatted_cookies[cookie.name] = cookie.value
                elif isinstance(cookie, dict) and 'name' in cookie:
                    formatted_cookies[cookie['name']] = cookie['value']
                elif isinstance(cookie, tuple) and len(cookie) == 2:
                    formatted_cookies[cookie[0]] = cookie[1]
            
            print(f"Loaded {len(formatted_cookies)} cookies")
            return formatted_cookies
            
        except Exception as e:
            print(f"Error loading cookies: {e}")
            return {}
    
    def _get_headers(self, user_agent=None):
        """Generate request headers with optional proxy support."""
        return {
            'User-Agent': user_agent or self.user_agents[0],
            'Accept': 'application/octet-stream,text/html,application/xhtml+xml,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': f'{ZLIBRARY_BASE_URL}/',
            'Cache-Control': 'no-cache',
            'DNT': '1',
        }
    
    def _get_connector(self, proxy=None):
        """Get aiohttp connector with optional proxy support."""
        # Future proxy implementation: connector = aiohttp.ProxyConnector.from_url(proxy)
        return aiohttp.TCPConnector(
            limit=1, limit_per_host=1, ssl=False, 
            enable_cleanup_closed=True, force_close=True
        )

    
    async def _download_file(self, session, url, output_path, user_agent=None, max_retries=3):
        """Download a single file with retry logic."""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = random.uniform(2.0, 5.0)
                    print(f"Retrying {url} (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                
                headers = self._get_headers(user_agent)
                async with session.get(url, headers=headers, allow_redirects=True, ssl=False) as resp:
                    if resp.status != 200:
                        continue
                    
                    content = await resp.read()
                    
                    # Validate content (avoid HTML error pages)
                    if b'<html' in content[:100].lower() or len(content) < 1024:
                        if b'<html' in content[:100].lower():
                            print(f"Error: Got HTML instead of file for {url}")
                            if attempt < max_retries - 1:
                                continue
                            return False
                    
                    # Write file
                    async with aiofiles.open(output_path, 'wb') as f:
                        await f.write(content)
                    
                    print(f"Downloaded: {output_path} ({len(content)} bytes)")
                    return True
                    
            except Exception as e:
                print(f"Download error for {url} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    continue
        
        return False
    
    async def _validate_and_refresh_session(self, session):
        """Validate session and regenerate cookies if needed."""
        try:
            test_url = f"{ZLIBRARY_BASE_URL}/profile"
            async with session.get(test_url, headers=self._get_headers()) as resp:
                if resp.status == 200:
                    content = await resp.text()
                    if "profile" in content.lower() and "login" not in resp.url.path.lower():
                        return True
        except Exception as e:
            print(f"Session validation error: {e}")
        
        # Try to regenerate cookies
        print("Regenerating cookies...")
        try:
            result = subprocess.run(['python', 'getCookies.py'], capture_output=True, text=True, cwd='.')
            if result.returncode == 0:
                cookies = self._load_cookies()
                session.cookie_jar.clear()
                session.cookie_jar.update_cookies(cookies)
                return True
        except Exception as e:
            print(f"Cookie regeneration failed: {e}")
        
        return False

    
    async def download_books(self, json_file, output_dir):
        """Main download function with simplified architecture."""
        # Load book data
        with open(json_file, 'r', encoding='utf-8') as f:
            books = json.load(f)
        os.makedirs(output_dir, exist_ok=True)
        
        # Load cookies and setup session
        cookies = self._load_cookies()
        if not cookies:
            print("Warning: No cookies found. Authentication may fail.")
        
        # Get proxy if available (future implementation)
        current_proxy = self.proxy_pool.get_proxy() if self.proxy_pool else None
        connector = self._get_connector(current_proxy)
        timeout = aiohttp.ClientTimeout(total=180, connect=45)
        
        successful_downloads = 0
        total_downloads = 0
        
        async with aiohttp.ClientSession(
            cookies=cookies, connector=connector, timeout=timeout
        ) as session:
            # Validate session
            if not await self._validate_and_refresh_session(session):
                print("Authentication failed. Please check cookies manually.")
                return
            
            # Download files
            for i, book in enumerate(books):
                title = book.get('title', 'unknown')
                links = book.get('download_links', [])
                
                for j, link in enumerate(links):
                    url = link.get('download_url')
                    ext = link.get('format', 'bin').lower()
                    if not url:
                        continue
                    
                    total_downloads += 1
                    filename = self.sanitize_filename(f"{title}.{ext}")
                    output_path = os.path.join(output_dir, filename)
                    
                    # Skip if file exists
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                        print(f"Already exists: {output_path}")
                        successful_downloads += 1
                        continue
                    
                    # Download with rotation
                    user_agent = self.user_agents[(i + j) % len(self.user_agents)]
                    try:
                        if await self._download_file(session, url, output_path, user_agent):
                            successful_downloads += 1
                        
                        # Add delay between downloads
                        await asyncio.sleep(random.uniform(1.0, 3.0))
                        
                    except Exception as e:
                        print(f"Exception during download of {url}: {e}")
                        continue
            
            print(f"\nDownload Summary: {successful_downloads}/{total_downloads} files downloaded successfully")


# Convenience function for backward compatibility
async def download_books(json_file, output_dir):
    """Backward compatibility wrapper."""
    downloader = ZLibraryDownloader()
    await downloader.download_books(json_file, output_dir)

