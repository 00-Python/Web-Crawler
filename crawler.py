import concurrent.futures
import logging
import requests
import sqlite3
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re
import os
import time
import argparse
import queue
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver

# Updated to include logging configurations for better readability and tracing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Database:
    def __init__(self, db_name="crawler_data.db"):
        self.db_name = db_name
        self.lock = threading.Lock()
        # Initialize the SQLite database with the necessary tables
        with self.get_connection() as conn:
            self.create_tables(conn)

    def get_connection(self):
        """Establish a new SQLite connection."""
        return sqlite3.connect(self.db_name)

    def create_tables(self, conn):
        """Create necessary tables for storing URL and page data."""
        conn.execute('''
            CREATE TABLE IF NOT EXISTS url_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                classification TEXT,
                status_code INTEGER,
                timestamp TEXT,
                error TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS page_content (
                url TEXT PRIMARY KEY,
                main_text TEXT,
                title TEXT,
                meta_description TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS link_structure (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_url TEXT,
                child_url TEXT,
                classification TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS headers_info (
                url TEXT,
                header_key TEXT,
                header_value TEXT,
                PRIMARY KEY (url, header_key)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS image_info (
                url TEXT,
                image_url TEXT,
                alt_text TEXT,
                PRIMARY KEY (url, image_url)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS media_info (
                url TEXT,
                media_url TEXT,
                media_type TEXT,
                PRIMARY KEY (url, media_url)
            )
        ''')
        conn.commit()

    def execute_query(self, query, params):
        """Execute a query with parameters using a thread-safe connection."""
        with self.get_connection() as conn:
            with self.lock:
                conn.execute(query, params)
                conn.commit()

    def insert_url_info(self, url, classification, status_code, error=None):
        query = '''
            INSERT OR IGNORE INTO url_info (url, classification, status_code, timestamp, error)
            VALUES (?, ?, ?, datetime('now'), ?)
        '''
        try:
            self.execute_query(query, (url, classification, status_code, error))
        except sqlite3.Error as e:
            logging.error(f"Database error on URL insertion: {e}")

    def insert_page_content(self, url, title, meta_description, main_text):
        query = '''
            INSERT OR REPLACE INTO page_content (url, title, meta_description, main_text)
            VALUES (?, ?, ?, ?)
        '''
        try:
            self.execute_query(query, (url, title, meta_description, main_text))
        except sqlite3.Error as e:
            logging.error(f"Database error on page content insertion: {e}")

    def insert_link_structure(self, parent_url, child_url, classification):
        query = '''
            INSERT INTO link_structure (parent_url, child_url, classification)
            VALUES (?, ?, ?)
        '''
        try:
            self.execute_query(query, (parent_url, child_url, classification))
        except sqlite3.Error as e:
            logging.error(f"Database error on link structure insertion: {e}")

    def insert_headers_info(self, url, headers):
        query = '''
            INSERT OR REPLACE INTO headers_info (url, header_key, header_value)
            VALUES (?, ?, ?)
        '''
        try:
            for key, value in headers.items():
                self.execute_query(query, (url, key, value))
        except sqlite3.Error as e:
            logging.error(f"Database error on headers info insertion: {e}")

    def insert_image_info(self, url, images):
        query = '''
            INSERT OR REPLACE INTO image_info (url, image_url, alt_text)
            VALUES (?, ?, ?)
        '''
        try:
            for img_url, alt_text in images:
                self.execute_query(query, (url, img_url, alt_text))
        except sqlite3.Error as e:
            logging.error(f"Database error on image info insertion: {e}")

    def insert_media_info(self, url, media_urls, media_type):
        query = '''
            INSERT OR REPLACE INTO media_info (url, media_url, media_type)
            VALUES (?, ?, ?)
        '''
        try:
            for media_url in media_urls:
                self.execute_query(query, (url, media_url, media_type))
        except sqlite3.Error as e:
            logging.error(f"Database error on media info insertion: {e}")


class Crawler:
    def __init__(self, base_url, max_depth, rate_limit, db, chrome_driver_path=None):
        self.internal_urls = set()
        self.external_urls = set()
        self.checked_urls = set()
        self.failed_urls = set()  # New set to track failed URLs
        self.base_url = base_url
        self.clean_url = urlparse(base_url).netloc
        self.session = requests.Session()
        self.max_depth = max_depth
        self.rate_limit = rate_limit
        self.db = db
        self.url_queue = queue.PriorityQueue()
        self.driver = self.init_selenium(chrome_driver_path)

    def init_selenium(self, chrome_driver_path):
        """Initialize the Selenium WebDriver."""
        if not chrome_driver_path:
            return None
        options = Options()
        options.add_argument('--headless')  # Ensures the browser runs invisibly
        return webdriver.Chrome(service=Service(chrome_driver_path), options=options)

    def is_valid(self, url):
        """Check if a URL is valid."""
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def verify_word_in_url(self, word, url):
        """Verify a word's presence in the URL's domain."""
        domain = urlparse(url).netloc
        return word in domain

    def classify(self, url):
        """Classify if a URL is internal or external."""
        if self.verify_word_in_url(self.clean_url, url):
            self.internal_urls.add(url)
            return 'internal'
        else:
            self.external_urls.add(url)
            return 'external'

    def extract_content(self, soup):
        """Extract content from a BeautifulSoup object."""
        title = soup.title.string if soup.title else ''
        meta_desc = soup.find("meta", attrs={"name": "description"})
        meta_desc_content = meta_desc["content"] if meta_desc else ''
        main_text = " ".join([p.get_text() for p in soup.find_all('p')])
        return title, meta_desc_content, main_text

    def extract_images(self, soup):
        """Extract image URLs and alt text from a BeautifulSoup object."""
        images = []
        for img_tag in soup.find_all('img'):
            img_url = img_tag.get('src')
            alt_text = img_tag.get('alt', '')
            if img_url:
                images.append((urljoin(self.base_url, img_url), alt_text))
        return images

    def extract_media(self, soup):
        """Extract media URLs such as videos from a BeautifulSoup object."""
        media_urls = []
        for video_tag in soup.find_all('video'):
            src_url = video_tag.get('src')
            if src_url:
                media_urls.append(urljoin(self.base_url, src_url))
        return media_urls

    def handle_js_content(self, url):
        """Handle pages requiring JavaScript using Selenium."""
        if not self.driver:
            return None
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        except Exception as e:
            logging.error(f"Error accessing JS rendered content: {e}")
        return None

    def crawl(self, url, depth):
        """Crawl a URL recursively to a specified depth."""
        if depth > self.max_depth or url in self.checked_urls:
            return
        self.checked_urls.add(url)

        try:
            soup = self.handle_js_content(url)
            if soup is None:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')

            self.db.insert_url_info(url, self.classify(url), response.status_code)
            title, meta_description, main_text = self.extract_content(soup)
            self.db.insert_page_content(url, title, meta_description, main_text)

            headers = dict(response.headers)
            self.db.insert_headers_info(url, headers)
            images = self.extract_images(soup)
            self.db.insert_image_info(url, images)
            media_urls = self.extract_media(soup)
            self.db.insert_media_info(url, media_urls, 'video')

            for a_tag in soup.findAll("a"):
                href = a_tag.attrs.get("href")
                if not href:
                    continue

                href = urljoin(url, href)
                if not self.is_valid(href) or href in self.checked_urls:
                    continue

                classification = self.classify(href)
                self.db.insert_link_structure(url, href, classification)
                if classification == 'internal':
                    self.url_queue.put((-depth-1, href))  # Use negative depth for priority

        except requests.RequestException as e:
            logging.error(f"Failed to get {url}: {e}")
            self.db.insert_url_info(url, '', '', str(e))
            self.failed_urls.add(url)  # Track failed URL

    def start_crawling(self):
        """Initiate the crawling process with multithreading support."""
        self.url_queue.put((0, self.base_url))
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            while not self.url_queue.empty():
                priority, current_url = self.url_queue.get()
                if current_url not in self.checked_urls:
                    future = executor.submit(self.crawl, current_url, -priority)
                    time.sleep(self.rate_limit)  # Implement rate limiting

        if self.driver:
            self.driver.quit()
        logging.info("Crawling completed.")

def configure_arguments():
    parser = argparse.ArgumentParser(description='Enhanced Web Crawler')
    parser.add_argument('base_url', type=str, help='Base URL to start crawling from')
    parser.add_argument('--max_depth', type=int, default=3, help='Maximum depth for recursive crawling')
    parser.add_argument('--rate_limit', type=float, default=1.0, help='Delay between requests in seconds')
    parser.add_argument('--db_name', type=str, default="crawler_data.db", help='SQLite database file name')
    parser.add_argument('--chrome_driver_path', type=str, help='Path to the ChromeDriver executable')
    return parser.parse_args()

if __name__ == '__main__':
    args = configure_arguments()

    db = Database(db_name=args.db_name)
    crawler = Crawler(args.base_url, args.max_depth, args.rate_limit, db, args.chrome_driver_path)
    crawler.start_crawling()
