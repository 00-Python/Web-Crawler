import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re

# initialize the set of links (unique links)
internal_urls = set()
external_urls = set()

def is_valid(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def classify(url, main_url):
    base_domain = main_url.replace("https://", "").replace("http://", "")
    tld = re.search(r"\.[a-zA-Z]{2,}$", base_domain).group()
    base_domain = base_domain.replace(tld, "")
    if base_domain in url:
        internal_urls.add(url)
    else:
        external_urls.add(url)

def crawl(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for a_tag in soup.findAll("a"):
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue
        href = urljoin(url, href)
        parsed_href = urlparse(href)
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if not is_valid(href):
            continue
        classify(href, url)

def crawl_and_save(base_url):
    clean_url = base_url.replace("https://", "").replace("http://", "")
    crawl(base_url)
    if len(internal_urls) != 0:
        with open(f"internal_{clean_url}.txt", "w") as file:
            for url in internal_urls:
                file.write(url + "\n")
    
    if len(external_urls) != 0:
        with open(f"external_{clean_url}.txt", "w") as file:
            for url in external_urls:
                file.write(url + "\n")
    


# replace with the url you want to crawl
crawl_and_save("https://facebook.com")
print("Total Internal links:", len(internal_urls))
print("Total External links:", len(external_urls))
