# Web Crawler

This script is a comprehensive web crawler written in Python. It utilizes the BeautifulSoup library for parsing HTML and XML pages, and the requests library for sending HTTP requests. It also leverages a SQLite database to store and manage the crawler's data efficiently.

## Features

- Crawls internal and external URLs found on a webpage.
- Classifies URLs as either internal (belonging to the same domain) or external (belonging to a different domain).
- Stores URL information, page content, and link structure in a SQLite database.
- Extracts and stores the title, meta description, and main text of crawled pages.
- Handles exceptions for request errors and invalid URLs.
- Rate limits crawling requests to avoid flooding websites with excessive requests.
- Uses multithreading to potentially increase the crawling efficiency.
- Allows command-line configuration for base URL, maximum crawling depth, and rate-limit between requests.

## Usage

To use this script, ensure Python is installed on your system along with the following required libraries: BeautifulSoup, requests, and sqlite3 (available by default in Python). You can install external packages with pip:

```sh
pip install beautifulsoup4 requests
```

Once the necessary libraries are installed, you can run the script using the following command:

```
python crawler.py <base_url> --max_depth <max_depth> --rate_limit <rate_limit>
```

### Command-Line Arguments

- `base_url`: The URL from which the crawler should start.
- `--max_depth`: Maximum depth for recursive crawling. Defaults to 3 if not specified.
- `--rate_limit`: Time delay between requests in seconds. Defaults to 1.0 if not specified.

### Example

To crawl "https://example.org" up to a depth of 5 and with a 2-second delay between requests, use:

```
python crawler.py https://example.org --max_depth 5 --rate_limit 2
```

## Data Storage

All URL information, page content, and link structures are stored in the `crawler_data.db` SQLite database for easy access and management. The database consists of three tables:

- `url_info`: Stores URLs, their classifications, HTTP status codes, timestamps, and any error messages.
- `page_content`: Stores the URLs, main text, titles, and meta descriptions of the pages.
- `link_structure`: Stores relationships between parent and child URLs.

## Logging

The script utilizes the logging library to log the crawling process. By default, logging is set to the INFO level. This includes informational messages and error messages during crawling. You can adjust the logging level by modifying the `logging.basicConfig` call at the start of the script.

## Contributors

You can modify or update the script according to your needs. Contributions are always welcome!
