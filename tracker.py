from db import get_all_products, add_price
from scraper import get_price, ScraperError


def run_price_check():
    products = get_all_products()
    if not products:
        print("No products found. Add products first from the web app.")
        return

    for p in products:
        product_id = p["id"]
        name = p["name"]
        store = p["store"]
        url = p["url"]
        target_price = p["target_price"]

        print(f"\nChecking: {name} [{store}]")
        print(f"URL: {url}")

        try:
            current_price = get_price(url, store)   # <--- REAL PRICE HERE
            print(f"Current price: {current_price}")
            add_price(product_id, current_price)

            # Convert target_price to float for comparison
            if target_price is not None and str(target_price).strip():
                try:
                    target_price_float = float(target_price)
                    if current_price <= target_price_float:
                        print("⚠ ALERT: Price dropped below target price!")
                        print(f"   Target Price : {target_price_float}")
                        print(f"   Current Price: {current_price}")
                except (ValueError, TypeError):
                    print(f"Warning: Invalid target price '{target_price}' for {name}")

        except ScraperError as e:
            print(f"Error for {name}: {e}")
        except Exception as e:
            print(f"Unexpected error for {name}: {e}")
        
        # Add delay between requests to avoid overwhelming servers
        import time
        time.sleep(2)


if __name__ == "__main__":
    run_price_check()
