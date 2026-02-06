#!/usr/bin/env python3
"""
Test script to validate all scraper functions with sample URLs.
"""

from scraper import (
    get_price_amazon,
    get_price_flipkart,
    get_price_myntra,
    ScraperError
)

# Sample URLs for testing (these are real product URLs)
test_urls = {
    "amazon": "https://www.amazon.in/OnePlus-Infinite-Snapdragon-Personalised-Game-Changing/dp/B0FTRMJNPX",
    "flipkart": "https://www.flipkart.com/oneplus-nord-ce-3-lite-5g-chromatic-gray-256-gb/p/itm2cd5a4e659035",
    "myntra": "https://www.myntra.com/shirts/roadster/roadster-men-black--white-slim-fit-checked-casual-shirt/1135318/buy"
}

def test_scraper(name, func, url):
    """Test a single scraper function."""
    try:
        price = func(url)
        print(f"✅ {name}: ₹{price}")
        return True
    except ScraperError as e:
        print(f"❌ {name}: {e}")
        return False
    except Exception as e:
        print(f"❌ {name}: Unexpected error - {e}")
        return False

def main():
    """Test all scrapers."""
    print("Testing all scrapers...\n")

    results = {}
    for name, url in test_urls.items():
        func_name = f"get_price_{name.lower()}"
        func = globals().get(func_name)
        if func:
            results[name] = test_scraper(name, func, url)
        else:
            print(f"❌ {name}: Function {func_name} not found")

    print("\n" + "="*50)
    print("SUMMARY:")
    working = sum(results.values())
    total = len(results)
    print(f"Working: {working}/{total}")

    if working < total:
        print("\nFailed scrapers:")
        for name, success in results.items():
            if not success:
                print(f"  - {name}")

if __name__ == "__main__":
    main()