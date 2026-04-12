import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

START_URL = [
    "https://tiki.vn/nem-bong-ep/c23380",
    "https://tiki.vn/nem-lo-xo/c23378",
    "https://tiki.vn/nem-foam/c23382",
    "https://tiki.vn/nem-hoi/c23386",
    "https://tiki.vn/nem-cao-su/c67523",
    "https://tiki.vn/nem-da-tang-hybrid/c67524",
]
OUTPUT_CSV = "deals.csv"
MAX_PAGES = None  # None means scrape all pages, or set a number like 5
WAIT_TIME = 2  # seconds to wait between pages

def create_driver():
    """Creates and returns a Chrome browser that runs in the background."""
    # Setup browser options
    options = Options()
    options.add_argument("--headless=new")  # Run without opening a window
    options.add_argument("--no-sandbox") # Disable the security sandbox (may be needed in some environments)
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems (64MB by default for RAM usage)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
    # Create and return the browser
    #(tự động kiểm tra và cài đặt driver Chrome phù hợp với phiên bản trình duyệt 
    #(bởi vì chorme liên tục cập nhật phiên bản mới 
    #nên việc tự động cài đặt driver sẽ giúp tránh lỗi không tương thích giữa driver và trình duyệt))
    service = Service(ChromeDriverManager().install()) 
    return webdriver.Chrome(service=service, options=options)


def scrape_page(driver, seen):
    """Gets all product deals from the current page."""

    # Wait for products to load (up to 10 seconds)
    # until the element with attribute data-component-type="s-search-result" is present
    WebDriverWait(driver, 30).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'a.product-item[data-view-id="product_list_item"]')
        )
    )
    time.sleep(5)

    product_cards = driver.find_elements(
        By.CSS_SELECTOR, 'a.product-item[data-view-id="product_list_item"]'
    )

    # Extract data from each product card
    all_deals = []
    for card in product_cards:
        deal = extract_deal(card, seen)
        if deal:  # Only add if we got valid data
            all_deals.append(deal)

    return all_deals


# ===== STEP 3: Extract Data from One Product Card =====
def extract_deal(card, seen):
    try:
        # Tên sản phẩm (từ attribute title)
        product_name = card.find_element(
            By.CSS_SELECTOR, "div.content h3"
        ).text

        # Giá
        price = card.find_element(
            By.CSS_SELECTOR, "div.price-discount__price"
        ).text

        # Ảnh
        image_url = card.find_element(
            By.CSS_SELECTOR, "picture.webpimg-container source"
        ).get_attribute("srcset").split(",")[0].split()[0]

        # Số lượng đã bán
        sold_elements = card.find_elements(By.CSS_SELECTOR, "span.quantity")

        product_sold_number = sold_elements[0].text if sold_elements else None

        # Link sản phẩm
        link = card.get_attribute("href")
        seen.add(link)

        return {
            "product_name": product_name,
            "price": price,
            "image_url": image_url,
            "link": link,
            "product_sold_number": product_sold_number
        }

    except Exception as e:
        print("Error:", e)
        return None
    
def load_more_page(driver):
    """Clicks the 'Next' button. Returns True if successful, False if no more pages."""

    try:
        # Find the Next button
        seemore_button = driver.find_element(By.CSS_SELECTOR, 'div[data-view-id="category_infinity_view.more"]')
        seemore_button.click()
        return True

    except Exception:
        # Button not found, so we're on the last page
        return False

def get_new_deals(driver, seen):
    new_deals = []

    cards = driver.find_elements(
        By.CSS_SELECTOR,
        'a.product-item[data-view-id="product_list_item"]'
    )

    for card in cards:
        link = card.get_attribute("href")

        if link and link not in seen:
            new_deals.append(extract_deal(card, seen))

    return new_deals

def save_to_csv(deals, filename):
    """Saves the list of deals to a CSV file."""

    if not deals:
        print("No deals to save.")
        return

    # Open file and write data
    with open(filename, "w", newline="", encoding="utf-8") as file:
        # Get column names from first deal
        columns = deals[0].keys()
        writer = csv.DictWriter(file, fieldnames=columns)

        # Write header row
        writer.writeheader()

        # Write all deals
        writer.writerows(deals)

    print(f"\nSaved {len(deals)} deals to {filename}")


# ===== STEP 6: Main Program - Put It All Together =====
def main():
    """Main function that runs the entire scraper."""

    # Start the browser
    print("Starting browser...")
    driver = create_driver()

    # This will store all deals from all pages
    all_deals = []
    try:
        # Open the Amazon deals page
        for URL in START_URL:
            print(f"Opening {URL}")
            driver.get(URL)
            time.sleep(5)

            seen = set()
            deals_on_page = scrape_page(driver, seen)
            all_deals.extend(deals_on_page)
            print(f"Found {len(deals_on_page)} deals (Total so far: {len(all_deals)})")
            
            while load_more_page(driver):
                time.sleep(10)
                new_deals = get_new_deals(driver, seen)
                all_deals.extend(new_deals)
                print(f"Found {len(new_deals)} deals (Total so far: {len(all_deals)})")

    finally:
        # Always close the browser when done
        print("Closing browser...")
        driver.quit()

    # Save all deals to CSV file
    save_to_csv(all_deals, OUTPUT_CSV)


# Run the program
if __name__ == "__main__":
    main()