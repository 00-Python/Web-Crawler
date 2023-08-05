import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re

class Crawler:
    def __init__(self, base_url):
        self.internal_urls = set()
        self.external_urls = set()
        self.base_url = base_url
        self.clean_url = base_url.replace("https://", "").replace("http://", "")

    def is_valid(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def verify_word_in_url(self, word, url):
        pattern = r"(https?://)(\w+\.)+\w+(/\S*)?"
        match = re.search(pattern, url)
        if match:
            url_without_protocol = match.group(0)[len(match.group(1)):]
            domain = url_without_protocol.split('/')[0]
            return word in domain
        return False
    
    def classify(self, url):
        base_domain = self.base_url.replace("https://", "").replace("http://", "")
        tld = re.search(r"\.[a-zA-Z]{2,}$", base_domain).group()
        base_domain = base_domain.replace(tld, "")
        if self.verify_word_in_url(base_domain, url):
            self.internal_urls.add(url)
        else:
            self.external_urls.add(url)

    def crawl(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            if href == "" or href is None:
                continue
            href = urljoin(url, href)
            parsed_href = urlparse(href)
            href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            if not self.is_valid(href):
                continue
            self.classify(href)

    def crawl_all(self):
        self.crawl(self.base_url)
        for link in list(self.internal_urls):
            self.crawl(link)

    def save(self):
        if len(self.internal_urls) != 0:
            with open(f"internal_{self.clean_url}.txt", "w") as file:
                for url in self.internal_urls:
                    file.write(url + "\n")
        
        if len(self.external_urls) != 0:
            with open(f"external_{self.clean_url}.txt", "w") as file:
                for url in self.external_urls:
                    file.write(url + "\n")

crawler = Crawler("https://thehybridathlete.com")
crawler.crawl_all()
crawler.save()
print("Total Internal links:", len(crawler.internal_urls))
print("Total External links:", len(crawler.external_urls))
