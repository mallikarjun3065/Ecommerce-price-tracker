from scraper import fetch_html
from bs4 import BeautifulSoup
url = 'https://www.flipkart.com/oneplus-nord-ce-3-lite-5g-chromatic-gray-256-gb/p/itm2cd5a4e659035'
html = fetch_html(url)
if not html:
    raise ValueError("No HTML content received")
soup = BeautifulSoup(html, 'html.parser')
selectors = [
    "div._30jeq3._16Jk6d",  # classic product price
    "div._19_Y9G._8XxizX",  # "Special Price" block
    "div._19_Y9G._1PLdiu",  # "Selling Price" block
    "div._30jeq3",  # general price class
    "span._30jeq3",  # price span
    "div.Nx9bqj",  # newer price class
]
for sel in selectors:
    el = soup.select_one(sel)
    if el:
        text = el.get_text(strip=True)
        print(f'{sel}: {text}')
        if '₹' in text:
            print('*** This is the correct price ***')
        break  # Stop at first match