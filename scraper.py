# scraper.py
import requests
import time
import random
import threading
import concurrent.futures
from bs4 import BeautifulSoup


class ScraperError(Exception):
    pass


HEADERS = {
    # Enhanced headers to avoid bot detection
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "Referer": "https://www.google.com/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

# Multiple user agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
]


# Supported e-commerce websites:
# - Amazon (amazon.in)
# - Flipkart
# - Myntra
#
# Note: Websites frequently change their HTML structure, so these scrapers
# are best-effort implementations and may need updates over time.


def create_realistic_session(url: str):
    """Create a requests session with realistic browser-like behavior."""
    session = requests.Session()

    if "amazon" in url.lower():
        # Set realistic cookies that look like a real browsing session
        session.cookies.set("session-id", f"{random.randint(100, 999)}-{'-'.join(str(random.randint(1000, 9999)) for _ in range(4))}", domain=".amazon.in")
        session.cookies.set("session-id-time", str(int(time.time())), domain=".amazon.in")

        # Add common browser cookies
        session.cookies.set("ubid-main", f"{random.randint(100, 999)}-{'-'.join(str(random.randint(1000, 9999)) for _ in range(3))}", domain=".amazon.in")
        session.cookies.set("lc-main", "en_IN", domain=".amazon.in")
    elif "flipkart" in url.lower():
        # Set some cookies for flipkart
        session.cookies.set("fk_affiliate", "", domain=".flipkart.com")
        session.cookies.set("AMCVS_17EB401053DAF4840A490D4C%40AdobeOrg", "1", domain=".flipkart.com")
        session.cookies.set("AMCV_17EB401053DAF4840A490D4C%40AdobeOrg", "179643557%7CMCIDTS%7C19917%7CMCMID%7C1234567890%7CMCAAMLH-1234567890%7C9%7CMCAAMB-1234567890%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1234567890s%7CNONE%7CMCAID%7CNONE", domain=".flipkart.com")

    # Set up session with proper SSL verification and redirects
    session.max_redirects = 5
    session.verify = True

    return session


def simulate_human_behavior():
    """Add random delays and mouse movements to simulate human behavior."""
    # Random delay between actions (like a human reading/thinking)
    time.sleep(random.uniform(1, 3))

    # Simulate mouse movement (though this doesn't affect HTTP requests)
    # In a real browser, this would happen naturally


def fetch_html(url: str) -> str:
    """Download HTML of the given product URL with advanced anti-bot measures."""
    # Create a session for persistent cookies and connection reuse
    session = create_realistic_session(url)

    # Add random delay to look more human-like (reduced for speed)
    base_delay = random.uniform(1, 3)  # Reduced from 2-8 to 1-3 seconds
    # Add extra delay during business hours (reduced)
    current_hour = time.localtime().tm_hour
    if 9 <= current_hour <= 17:  # Business hours
        base_delay *= 1.2  # Reduced from 1.5x to 1.2x
    time.sleep(base_delay)

    max_retries = 5  # Increased retries
    for attempt in range(max_retries):
        try:
            # Rotate user agents
            request_headers = HEADERS.copy()
            request_headers["User-Agent"] = random.choice(USER_AGENTS)

            # Add more realistic browser headers
            request_headers.update({
                "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-ch-viewport-width": "1920",
                "sec-ch-viewport-height": "1080",
                "sec-ch-device-memory": "8",
                "sec-ch-dpr": "1",
                "sec-ch-prefers-color-scheme": "light",
                "sec-ch-prefers-reduced-motion": "no-preference",
                "sec-ch-ua-arch": '"x86"',
                "sec-ch-ua-bitness": '"64"',
                "sec-ch-ua-full-version": '"131.0.6778.86"',
                "sec-ch-ua-full-version-list": '"Google Chrome";v="131.0.6778.86", "Chromium";v="131.0.6778.86", "Not_A Brand";v="24.0.0.0"',
                "sec-ch-ua-model": '""',
                "sec-ch-ua-platform-version": '"15.0.0"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "dnt": "1",
                "accept-encoding": "gzip, deflate, br",
                "cache-control": "max-age=0"
            })

            # Add some randomization to make requests look different
            request_headers["Accept-Language"] = random.choice([
                "en-US,en;q=0.9",
                "en-US,en;q=0.9,hi;q=0.8",
                "en-GB,en;q=0.9"
            ])

            # Add a realistic referer for search requests
            if "search" in url.lower() or "q=" in url:
                request_headers["Referer"] = "https://www.google.com/"
            else:
                request_headers["Referer"] = random.choice([
                    "https://www.google.com/",
                    "https://www.bing.com/",
                    "",
                ])

            resp = session.get(url, headers=request_headers, timeout=30)

            if resp.status_code == 200:
                return resp.text or ''
            elif resp.status_code == 403:
                # 403 Forbidden - site is blocking us
                if attempt < max_retries - 1:
                    # Wait longer and try again with different user agent (reduced for speed)
                    wait_time = random.uniform(5, 10) * (attempt + 1)  # Reduced from 10-20 to 5-10 seconds
                    print(f"403 blocked, retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue
                raise ScraperError(f"Access forbidden (403) - site is blocking automated requests after {max_retries} attempts.")
            elif resp.status_code == 429:  # Too many requests
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # Reduced from 10 to 5 seconds
                    print(f"Rate limited (429), waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                raise ScraperError("Rate limited - too many requests")
            elif resp.status_code >= 500:  # Server errors
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))  # Reduced from 5 to 2 seconds
                    continue
            else:
                raise ScraperError(f"Failed to fetch page (status {resp.status_code})")

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))  # Reduced from 3 to 1.5 seconds
                continue
            raise ScraperError(f"Network error: Connection timed out after {max_retries} attempts")
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))  # Reduced from 2 to 1 seconds
                continue
            raise ScraperError(f"Network error: Connection failed after {max_retries} attempts")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            raise ScraperError(f"Network error: {e}")


def test_scraper_bypass():
    """Test if our anti-bot measures work against blocking sites."""
    test_urls = [
        ("Flipkart", "https://www.flipkart.com/search?q=iPhone+15"),
        ("Amazon", "https://www.amazon.in/s?k=iPhone+15")
    ]

    print("Testing scraper effectiveness...")
    for site_name, url in test_urls:
        try:
            html = fetch_html(url)
            if "403" in html or "blocked" in html.lower() or "access denied" in html.lower():
                print(f"❌ {site_name}: Still blocked")
            elif len(html) < 1000:  # Suspiciously short response
                print(f"⚠️  {site_name}: Got response but seems suspicious (length: {len(html)})")
            else:
                print(f"✅ {site_name}: Working (response length: {len(html)})")
        except ScraperError as e:
            print(f"❌ {site_name}: {e}")
        except Exception as e:
            print(f"❌ {site_name}: Unexpected error - {e}")

        # Small delay between tests
        import time
        time.sleep(2)


def extract_price_number(text: str) -> float:
    """
    Clean a price string like '₹ 13,999.00' -> 13999.00
    """
    cleaned = ""
    for ch in text:
        if ch.isdigit() or ch == ".":
            cleaned += ch

    if not cleaned:
        raise ScraperError(f"Could not parse price from: {text!r}")

    return float(cleaned)


def get_price_amazon(url: str) -> float:
    """
    Extract price from an Amazon / Amazon.in product page.
    NOTE: Amazon HTML can change any time, this is a best-effort demo.
    """
    html = fetch_html(url)
    if not html:
        raise ScraperError("No HTML content received from Amazon")
    soup = BeautifulSoup(html, "html.parser")

    # Try multiple common selectors used by Amazon
    selectors = [
        "#corePriceDisplay_desktop_feature_div .a-price-whole",
        "#corePrice_feature_div .a-price .a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        ".a-price .a-offscreen",
        ".a-price-whole",
        ".a-color-price",
        "#price_inside_buybox",
        ".a-price span[aria-hidden='true']",
    ]

    for sel in selectors:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            text = el.get_text(strip=True)
            return extract_price_number(text)

    # Try to find any element containing ₹ followed by numbers
    import re
    price_pattern = r'₹\s*[\d,]+\.?\d*'
    all_text = soup.get_text()
    matches = re.findall(price_pattern, all_text)
    if matches:
        # Take the first price found
        return extract_price_number(matches[0])

    raise ScraperError("Could not find price on Amazon page")


def get_price_flipkart(url: str) -> float:
    """
    Extract price from a Flipkart product page.
    NOTE: Flipkart often changes CSS classes, so we try multiple known patterns.
    """
    html = fetch_html(url)
    if not html:
        raise ScraperError("No HTML content received from Flipkart")
    soup = BeautifulSoup(html, "html.parser")

    # Try multiple possible price locations (detail page & offers)
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
        if el and el.get_text(strip=True):
            text = el.get_text(strip=True)
            return extract_price_number(text)

    # If still not found, try any element that looks like a ₹ price
    # as a last fallback (for new layouts)
    possible_prices = soup.find_all(string=lambda s: s and "₹" in s and len(s.strip()) < 20)  # avoid long texts
    for txt in possible_prices:
        # Skip if it contains words like "off", "cashback", etc.
        if any(word in txt.lower() for word in ['off', 'cashback', 'fee', 'up to']):
            continue
        try:
            return extract_price_number(txt)
        except ScraperError:
            continue

def get_price_myntra(url: str) -> float:
    """
    Extract price from a Myntra product page.
    """
    html = fetch_html(url)
    if not html:
        raise ScraperError("No HTML content received from Myntra")
    soup = BeautifulSoup(html, "html.parser")

    # Try common Myntra price selectors (updated for current layout)
    selectors = [
        "span.pdp-price",  # Main price
        "span.pdp-mrp",    # MRP if discounted
        "div.price-container span",  # Alternative
        ".price-heading",  # New price class
        ".pdp-price",      # Price container
        "[data-price]",    # Data attribute
        ".price",          # Generic price
    ]

    for sel in selectors:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            text = el.get_text(strip=True)
            return extract_price_number(text)

    # Try to find any element containing ₹ followed by numbers
    import re
    price_pattern = r'₹\s*[\d,]+\.?\d*'
    all_text = soup.get_text()
    matches = re.findall(price_pattern, all_text)
    if matches:
        # Take the first price found (usually the main price)
        return extract_price_number(matches[0])

    raise ScraperError("Could not find price on Myntra page")


def search_single_store(store_name, search_url_template, product_name, exclude_store):
    """Search for a product on a single store - used for parallel processing."""
    if exclude_store == store_name:
        return None
        
    try:
        search_url = search_url_template.format(product_name.replace(' ', '+'))
        print(f"Searching {store_name} for: {product_name}")
        
        # Get search results
        html = fetch_html(search_url)
        if not html:
            raise ScraperError(f"No HTML content received from {store_name}")
        soup = BeautifulSoup(html, "html.parser")
        
        product_url = None
        product_name_found = None
        product_price = None
        
        if store_name == "amazon":
            # Find first product link
            link_elem = soup.select_one("a.a-link-normal.s-no-outline")
            if link_elem and link_elem.get("href"):
                product_url = "https://www.amazon.in" + link_elem["href"]
                # Try to get name and price
                title_elem = link_elem.select_one("h2.a-size-mini")
                if title_elem:
                    product_name_found = title_elem.get_text(strip=True)
                price_elem = link_elem.select_one(".a-price-whole")
                if price_elem:
                    price_text = price_elem.get_text(strip=True).replace(',', '')
                    try:
                        product_price = float(price_text)
                    except ValueError:
                        pass
                        
        elif store_name == "flipkart":
            # Find first product
            product_elem = soup.select_one("a[href*='/p/']")
            if product_elem:
                href = product_elem.get("href")
                if href.startswith('/'):
                    product_url = "https://www.flipkart.com" + href
                else:
                    product_url = href
                    
                # Try to get name and price
                name_elem = product_elem.select_one("div.RG5Slk")
                if name_elem:
                    product_name_found = name_elem.get_text(strip=True)
                # Find price element containing ₹ symbol
                price_elems = product_elem.select("div.HZ0E6r.Rm9_cy")
                for price_elem in price_elems:
                    price_text = price_elem.get_text(strip=True)
                    if '₹' in price_text:
                        price_text = price_text.replace('₹', '').replace(',', '')
                        try:
                            product_price = float(price_text)
                            break
                        except ValueError:
                            pass
        
        if product_url:
            print(f"Found product on {store_name}: {product_url}")
            return {
                "name": product_name_found or f"{product_name} ({store_name.title()})",
                "store": store_name,
                "url": product_url,
                "estimated_price": product_price
            }
        else:
            print(f"No product found on {store_name}")
            return None
            
    except ScraperError as e:
        if "403" in str(e) or "forbidden" in str(e).lower():
            print(f"Skipping {store_name} - site is blocking requests")
        else:
            print(f"Error searching {store_name}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error searching {store_name}: {e}")
        return None


def search_similar_products(product_name, exclude_store=None, fast_mode=True):
    """
    Search for similar products across different stores based on product name.
    Returns actual product URLs with prices, not search URLs.
    
    Note: Only supported stores that are currently accessible are searched.
    
    Args:
        product_name: Name of the product to search for
        exclude_store: Store to exclude from search (optional)
        fast_mode: If True, uses parallel processing for faster results
    """
    base_name = product_name.lower().strip()
    
    # Define stores to search
    stores = [
        ("amazon", "https://www.amazon.in/s?k={}&ref=sr_pg_1"),
        ("flipkart", "https://www.flipkart.com/search?q={}&page=1")
    ]
    
    if fast_mode:
        # Parallel processing for speed
        similar_products = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all store searches concurrently
            future_to_store = {
                executor.submit(search_single_store, store_name, search_url_template, product_name, exclude_store): store_name
                for store_name, search_url_template in stores
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_store):
                result = future.result()
                if result:
                    similar_products.append(result)
                    
        return similar_products
    else:
        # Original sequential processing (slower but more reliable for debugging)
        similar_products = []
        
        for store_name, search_url_template in stores:
            if exclude_store == store_name:
                continue
                
            try:
                search_url = search_url_template.format(product_name.replace(' ', '+'))
                print(f"Searching {store_name} for: {product_name}")
                
                # Get search results
                html = fetch_html(search_url)
                if not html:
                    raise ScraperError(f"No HTML content received from {store_name}")
                soup = BeautifulSoup(html, "html.parser")
                
                product_url = None
                product_name_found = None
                product_price = None
                
                if store_name == "amazon":
                    # Find first product link
                    link_elem = soup.select_one("a.a-link-normal.s-no-outline")
                    if link_elem and link_elem.get("href"):
                        product_url = "https://www.amazon.in" + link_elem["href"]
                        # Try to get name and price
                        title_elem = link_elem.select_one("h2.a-size-mini")
                        if title_elem:
                            product_name_found = title_elem.get_text(strip=True)
                        price_elem = link_elem.select_one(".a-price-whole")
                        if price_elem:
                            price_text = price_elem.get_text(strip=True).replace(',', '')
                            try:
                                product_price = float(price_text)
                            except ValueError:
                                pass
                                
                elif store_name == "flipkart":
                    # Find first product
                    product_elem = soup.select_one("a[href*='/p/']")
                    if product_elem:
                        href = product_elem.get("href")
                        if href.startswith('/'):
                            product_url = "https://www.flipkart.com" + href
                        else:
                            product_url = href
                            
                        # Try to get name and price
                        name_elem = product_elem.select_one("div.RG5Slk")
                        if name_elem:
                            product_name_found = name_elem.get_text(strip=True)
                        # Find price element containing ₹ symbol
                        price_elems = product_elem.select("div.HZ0E6r.Rm9_cy")
                        for price_elem in price_elems:
                            price_text = price_elem.get_text(strip=True)
                            if '₹' in price_text:
                                price_text = price_text.replace('₹', '').replace(',', '')
                                try:
                                    product_price = float(price_text)
                                    break
                                except ValueError:
                                    pass
                                
                if product_url:
                    similar_products.append({
                        "name": product_name_found or f"{product_name} ({store_name.title()})",
                        "store": store_name,
                        "url": product_url,
                        "estimated_price": product_price
                    })
                    print(f"Found product on {store_name}: {product_url}")
                else:
                    print(f"No product found on {store_name}")
                    
            except ScraperError as e:
                if "403" in str(e) or "forbidden" in str(e).lower():
                    print(f"Skipping {store_name} - site is blocking requests")
                else:
                    print(f"Error searching {store_name}: {e}")
            except Exception as e:
                print(f"Unexpected error searching {store_name}: {e}")
        
        return similar_products


def get_price(url: str, store: str) -> float:
    """
    Main function used by tracker.py.
    store field should be something like: 'amazon', 'flipkart', 'myntra'
    """
    s = (store or "").lower()

    if "amazon" in s:
        return get_price_amazon(url)
    elif "flipkart" in s:
        return get_price_flipkart(url)
    elif "myntra" in s:
        return get_price_myntra(url)
    else:
        # You can add more store-specific parsers here
        raise ScraperError(f"Store '{store}' is not supported yet in scraper. Supported stores: Amazon, Flipkart, Myntra")


def detect_store(url: str) -> str:
    """Detect store from URL."""
    url_lower = url.lower()
    if "amazon" in url_lower:
        return "amazon"
    elif "flipkart" in url_lower:
        return "flipkart"
    elif "myntra" in url_lower:
        return "myntra"
    else:
        raise ScraperError("Unsupported store URL")


def get_product_details(url: str) -> dict:
    """
    Extract product name and price from URL.
    Returns dict with 'name', 'price', 'store'
    """
    store = detect_store(url)
    price = get_price(url, store)
    
    # Now extract name - need to modify each get_price function to also return name
    # For now, let's add name extraction to each function
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    
    name = None
    if store == "amazon":
        selectors = ["#productTitle", ".a-size-large.product-title-word-break"]
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                name = el.get_text(strip=True)
                break
    elif store == "flipkart":
        el = soup.select_one("h1 span")
        if el:
            name = el.get_text(strip=True)
    elif store == "myntra":
        el = soup.select_one("h1.pdp-title")
        if el:
            name = el.get_text(strip=True)
    elif store == "ajio":
        el = soup.select_one("h1.prod-name")
        if el:
            name = el.get_text(strip=True)
    elif store == "croma":
        el = soup.select_one("h1.product-title")
        if el:
            name = el.get_text(strip=True)
    elif store == "tatacliq":
        el = soup.select_one("h1.product-name")
        if el:
            name = el.get_text(strip=True)
    elif store == "reliancedigital":
        el = soup.select_one("h1.product-title")
        if el:
            name = el.get_text(strip=True)
    
    if not name:
        name = "Unknown Product"
    
    return {
        "name": name,
        "price": price,
        "store": store,
        "url": url
    }
