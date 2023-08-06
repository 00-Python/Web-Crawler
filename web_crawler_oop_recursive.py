import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re
import os
import logging

class Crawler:
    def __init__(self, base_url):
        self.internal_urls = set()
        self.external_urls = set()
        self.base_url = base_url
        self.clean_url = urlparse(base_url).netloc
        self.session = requests.Session()

    def is_valid(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def verify_word_in_url(self, word, url):
        domain = urlparse(url).netloc
        return word in domain
    
    def classify(self, url):
        base_domain = self.clean_url
        if self.verify_word_in_url(base_domain, url):
            self.internal_urls.add(url)
        else:
            self.external_urls.add(url)

    def crawl(self, url):
        try:
            response = self.session.get(url)
        except requests.RequestException:
            logging.error(f"Failed to get {url}")
            return
        if url.endswith('.xml'):
            soup = BeautifulSoup(response.content, 'lxml-xml')
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                continue
            href = urljoin(url, href)
            if not self.is_valid(href):
                continue
            self.classify(href)

    def crawl_all(self):
        self.crawl(self.base_url)
        for link in list(self.internal_urls):
            if link not in self.external_urls:
                self.crawl(link)

    def save(self):
        save_url = self.clean_url.replace("/", "-")
        if len(self.internal_urls) != 0:
            with open(f"internal_{save_url}.txt", "w") as file:
                for url in self.internal_urls:
                    file.write(url + "\n")
        
        if len(self.external_urls) != 0:
            with open(f"external_{save_url}.txt", "w") as file:
                for url in self.external_urls:
                    file.write(url + "\n")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    crawler = Crawler("https://example.com/")
    crawler.crawl_all()
    crawler.save()
    logging.info("Total Internal links: %s", len(crawler.internal_urls))
    logging.info("Total External links: %s", len(crawler.external_urls))
