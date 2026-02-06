from flask import Flask, render_template, request, redirect, url_for,flash
from db import init_db, get_all_products, add_product, get_product, get_price_history, update_product, delete_product_db, get_product_comparison, get_all_comparison_groups, update_product_group
from scraper import search_similar_products
from tracker import run_price_check
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime
import time
import threading

# Global flag for background price checking
price_check_running = False
price_check_thread = None

def background_price_checker():
    """Background thread that periodically checks prices."""
    global price_check_running
    while price_check_running:
        try:
            print("Running automatic price check...")
            run_price_check()
            print("Automatic price check completed.")
        except Exception as e:
            print(f"Error in automatic price check: {e}")
        
        # Wait 10 minutes before next check
        time.sleep(600)  # 10 minutes

def start_background_price_checker():
    """Start the background price checking thread."""
    global price_check_running, price_check_thread
    if not price_check_running:
        price_check_running = True
        price_check_thread = threading.Thread(target=background_price_checker, daemon=True)
        price_check_thread.start()
        print("Background price checker started.")

def stop_background_price_checker():
    """Stop the background price checking thread."""
    global price_check_running, price_check_thread
    price_check_running = False
    if price_check_thread:
        price_check_thread.join(timeout=1)
        print("Background price checker stopped.")

app = Flask(__name__)
app.secret_key="smart-price-tracker-secret"
init_db()  # ensure database exists

# Start background price checker
start_background_price_checker()

# Simple cache for price history charts
chart_cache = {}
CACHE_TIMEOUT = 300  # 5 minutes


def create_price_history_chart(history, product_id):
    if not history or len(history) < 2:
        return None

    # Check cache first
    cache_key = f"chart_{product_id}"
    current_time = time.time()

    if cache_key in chart_cache:
        cached_time, cached_chart = chart_cache[cache_key]
        if current_time - cached_time < CACHE_TIMEOUT:
            return cached_chart

    # Filter history to only include price changes
    filtered_history = []
    if history:
        filtered_history.append(history[0])  # Always include first price
        for row in history[1:]:
            if row["price"] != filtered_history[-1]["price"]:
                filtered_history.append(row)

    if len(filtered_history) < 2:
        # If no changes, show all history
        filtered_history = history

    dates = [datetime.fromisoformat(row["checked_at"]) for row in filtered_history]
    prices = [row["price"] for row in filtered_history]

    # Use a modern style
    plt.style.use('seaborn-v0_8')
    fig, ax = plt.subplots(figsize=(10, 5), facecolor='#f8f9fa')
    
    # Create gradient background
    ax.set_facecolor('#ffffff')
    
    # Plot the line with better styling
    line = ax.plot(dates, prices, 
                   marker="o", 
                   markersize=6, 
                   linewidth=2.5,
                   color='#2196F3',
                   markerfacecolor='#1976D2',
                   markeredgecolor='white',
                   markeredgewidth=1.5,
                   alpha=0.9)
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Style the axes
    ax.set_xlabel("Date & Time", fontsize=11, fontweight='medium', color='#424242')
    ax.set_ylabel("Price (₹)", fontsize=11, fontweight='medium', color='#424242')
    ax.set_title("Price History & Trends", fontsize=14, fontweight='bold', color='#1976D2', pad=20)
    
    # Format the x-axis dates
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    
    # Style tick labels
    ax.tick_params(axis='both', which='major', labelsize=9, colors='#666666')
    
    # Add subtle border
    for spine in ax.spines.values():
        spine.set_edgecolor('#e0e0e0')
        spine.set_linewidth(0.8)
    
    # Format price labels with currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'₹{x:,.0f}'))
    
    # Tight layout and save
    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100, facecolor='#f8f9fa')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)

    # Cache the result
    chart_cache[cache_key] = (current_time, img_base64)

    return img_base64


def auto_compare_product(product_id, product_name, exclude_store):
    """Automatically add similar products from other stores for comparison."""
    try:
        # Check if current product already has a group_id
        from db import get_product
        current_product = get_product(product_id)
        group_id = current_product['group_id']
        
        # If no group_id, generate one based on product name
        if not group_id:
            import hashlib
            group_id = hashlib.md5(product_name.lower().strip().encode()).hexdigest()[:8]
            # Add current product to group
            update_product_group(product_id, group_id)
        
        # Find similar products
        from scraper import search_similar_products
        similar_products = search_similar_products(product_name, exclude_store=exclude_store)
        
        added_count = 0
        for sim_product in similar_products:
            try:
                # Check if this product already exists (avoid duplicates)
                from db import get_all_products
                existing_products = get_all_products()
                existing_urls = [p['url'] for p in existing_products]
                
                if sim_product['url'] in existing_urls:
                    print(f"Product from {sim_product['store']} already exists, skipping")
                    continue
                
                # Add the similar product to database
                new_product_id = add_product(
                    name=sim_product['name'],
                    store=sim_product['store'], 
                    url=sim_product['url']
                )
                update_product_group(new_product_id, group_id)
                
                # Try to add initial price if we have it
                if sim_product.get('estimated_price'):
                    add_price(new_product_id, sim_product['estimated_price'])
                
                added_count += 1
                print(f"Added similar product: {sim_product['name']} from {sim_product['store']}")
            except Exception as e:
                print(f"Error adding similar product from {sim_product['store']}: {e}")
        
        if added_count > 0:
            print(f"Auto-added {added_count} similar products for comparison")
            
    except Exception as e:
        print(f"Error in auto_compare_product: {e}")


@app.route("/")
def index():
    products = get_all_products()
    return render_template("index.html", products=products)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            flash("Please provide a product URL", "error")
            return redirect(url_for("add"))
        
        try:
            from scraper import get_product_details
            details = get_product_details(url)
            target_price_str = request.form.get("target_price", "").strip()
            target_price = float(target_price_str) if target_price_str else None
            
            product_id = add_product(details["name"], details["store"], url, target_price)
            # Add the initial price to history
            from db import add_price
            add_price(product_id, details["price"])
            
            # Automatically find and add similar products from other stores
            auto_compare_product(product_id, details["name"], details["store"])
            
            flash(f"Product '{details['name']}' added successfully with automatic price comparison!", "success")
            return redirect(url_for("index"))
        except Exception as e:
            flash(f"Error adding product: {str(e)}", "error")
            return redirect(url_for("add"))

    return render_template("add_product.html")


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("index"))
    
    history = get_price_history(product_id)
    
    # Check if we need to refresh the price (if last check was more than 5 minutes ago)
    should_refresh = False
    if history:
        last_checked = datetime.fromisoformat(history[-1]["checked_at"])
        time_since_last_check = datetime.now() - last_checked
        if time_since_last_check.total_seconds() > 300:  # 5 minutes
            should_refresh = True
    else:
        should_refresh = True
    
    if should_refresh:
        try:
            from scraper import get_price
            latest_price = get_price(product['url'], product['store'])
            # Store it in history
            from db import add_price
            add_price(product_id, latest_price)
            # Refresh history
            history = get_price_history(product_id)
        except Exception as e:
            print(f"Error fetching price for {product['name']}: {e}")
    
    chart_img = create_price_history_chart(history, product_id)
    
    # Get comparison products from the same group
    comparison_products = []
    if product and product['group_id']:
        from db import get_product_comparison
        comparison_products = get_product_comparison(product['group_id'])
        # Remove current product from comparison
        comparison_products = [p for p in comparison_products if p['id'] != product_id]
    
    # Get latest price
    latest_price = None
    if history:
        latest_price = history[-1]["price"]  # Last price from history
        best_price = min((p['current_price'] for p in comparison_products if p['current_price']), default=None)
    
    return render_template(
        "product_detail.html",
      product=product,
        history=history,
        chart_img=chart_img,
        latest_price=latest_price,
        comparison_products=comparison_products,
        best_price=best_price
    )


@app.route("/run_check")
def run_check():
    run_price_check()
    flash("Price check completed successfully!")
    return redirect(url_for("index"))

from flask import Flask, render_template, request, redirect, url_for, flash
from db import (
    init_db, get_all_products, add_product, get_product,
    update_product, delete_product_db, get_price_history
)

@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product = get_product(product_id)
    if request.method == "POST":
        name = request.form["name"]
        store = request.form["store"]
        url = request.form["url"]
        target_price = request.form.get("target_price")
        if target_price:
            target_price = float(target_price)
        else:
            target_price = None

        update_product(product_id, name, store, url, target_price)
        flash("Product updated successfully!")
        return redirect(url_for("index"))

    return render_template("edit_product.html", product=product)


@app.route("/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    try:
        delete_product_db(product_id)
        flash("Product deleted successfully!", "success")
    except ValueError as e:
        flash(f"Error deleting product: {e}", "error")
    except Exception as e:
        flash(f"Unexpected error: {e}", "error")
    return redirect(url_for("index"))


@app.route("/compare")
def compare():
    """Show all product comparison groups."""
    groups = get_all_comparison_groups()
    return render_template("compare.html", groups=groups)


@app.route("/compare/<group_id>")
def compare_group(group_id):
    """Show price comparison for a specific product group."""
    products = get_product_comparison(group_id)
    if not products:
        flash("No products found in this comparison group.", "error")
        return redirect(url_for("compare"))
    
    # Find the best (lowest) price
    best_price = min((p['current_price'] for p in products if p['current_price']), default=None)
    
    return render_template("compare_detail.html", 
                         products=products, 
                         group_id=group_id,
                         best_price=best_price)


@app.route("/add_to_group/<int:product_id>", methods=["POST"])
def add_to_group(product_id):
    """Add a product to a comparison group."""
    group_id = request.form.get("group_id")
    if group_id:
        try:
            update_product_group(product_id, group_id)
            flash("Product added to comparison group!", "success")
        except Exception as e:
            flash(f"Error adding to group: {e}", "error")
    else:
        flash("Please provide a group ID.", "error")
    return redirect(url_for("product_detail", product_id=product_id))


@app.route("/create_comparison", methods=["POST"])
def create_comparison():
    """Create a new comparison group with selected products."""
    product_ids = request.form.getlist("product_ids")
    group_name = request.form.get("group_name")
    
    if not product_ids or not group_name:
        flash("Please select products and provide a group name.", "error")
        return redirect(url_for("index"))
    
    # Generate a unique group_id from the group name
    import hashlib
    group_id = hashlib.md5(group_name.encode()).hexdigest()[:8]
    
    try:
        for product_id in product_ids:
            update_product_group(int(product_id), group_id)
        flash(f"Comparison group '{group_name}' created successfully!", "success")
        return redirect(url_for("compare_group", group_id=group_id))
    except Exception as e:
        flash(f"Error creating comparison: {e}", "error")
        return redirect(url_for("index"))


@app.route("/find_similar/<int:product_id>")
def find_similar_products(product_id):
    """Find similar products on other stores."""
    product = get_product(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("index"))
    
    similar_products = search_similar_products(product['name'], exclude_store=product['store'])
    
    return render_template("find_similar.html", 
                         product=product, 
                         similar_products=similar_products)


@app.route("/auto_compare/<int:product_id>", methods=["POST"])
def auto_compare(product_id):
    """Automatically create comparison by adding similar products."""
    product = get_product(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("index"))
    
    selected_stores = request.form.getlist("stores")
    group_name = request.form.get("group_name", product['name'])
    
    if not selected_stores:
        flash("Please select at least one store to compare.", "error")
        return redirect(url_for("find_similar_products", product_id=product_id))
    
    # Generate group_id
    import hashlib
    group_id = hashlib.md5(group_name.encode()).hexdigest()[:8]
    
    # Add current product to group
    update_product_group(product_id, group_id)
    
    # Add similar products from selected stores
    similar_products = search_similar_products(product['name'], exclude_store=product['store'])
    
    added_count = 1  # Current product
    
    for store in selected_stores:
        # Find the matching similar product
        for sim_product in similar_products:
            if sim_product['store'] == store:
                try:
                    # Add the similar product to database
                    new_product_id = add_product(
                        name=sim_product['name'],
                        store=sim_product['store'], 
                        url=sim_product['url']
                    )
                    update_product_group(new_product_id, group_id)
                    added_count += 1
                except Exception as e:
                    flash(f"Error adding {store} product: {e}", "error")
                break
    
    flash(f"Auto-comparison created! Added {added_count} products to comparison group.", "success")
    return redirect(url_for("compare_group", group_id=group_id))


@app.route("/run_check_group/<group_id>")
def run_check_group(group_id):
    """Run price check for all products in a comparison group."""
    try:
        products = get_product_comparison(group_id)
        updated_count = 0
        
        for product in products:
            try:
                from scraper import get_price
                from db import add_price
                
                print(f"Checking: {product['name']} [{product['store']}]")
                current_price = get_price(product['url'], product['store'])
                add_price(product['id'], current_price)
                updated_count += 1
                print(f"Updated price: ₹{current_price}")
                
                # Add delay
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"Error updating {product['name']}: {e}")
        
        flash(f"Updated prices for {updated_count} products in comparison group.", "success")
        
    except Exception as e:
        flash(f"Error running group price check: {e}", "error")
    
    return redirect(url_for("compare_group", group_id=group_id))


if __name__ == "__main__":
    print("Starting Smart Price Tracker...")
    app.run(host='127.0.0.1', port=8000, debug=False, use_reloader=False)