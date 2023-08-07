# Web Crawler

This script is a simple web crawler written in Python. It uses the BeautifulSoup library to parse HTML and XML pages, and the requests library to send HTTP requests.

## Features

- Crawls all internal and external URLs found on a webpage.
- Classifies URLs as either internal (belonging to the same domain) or external (belonging to a different domain).
- Saves all found internal and external URLs to separate text files.
- Handles exceptions for invalid URLs and request errors.

## Usage

To use this script, you need to have Python installed on your system along with the BeautifulSoup and requests libraries. If you don't have these libraries installed, you can install them using pip:

```
pip install beautifulsoup4 requests
```

Once you have the necessary libraries installed, you can run the script with the following command:

```
python crawler.py
```

By default, the script will crawl the "https://example.org" website. If you want to crawl a different website, you need to modify the base_url parameter in the Crawler class instantiation at the bottom of the script.

The script will save all found internal and external URLs to separate text files named "internal_[domain].txt" and "external_[domain].txt", where [domain] is the domain of the base URL.

## Logging

The script uses the logging library to log information about the crawling process. By default, the logging level is set to INFO, which means that the script will output informational messages (such as the total number of internal and external links found) as well as any error messages. If you want to change the logging level, you can modify the logging.basicConfig call at the bottom of the script.
