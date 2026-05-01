import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

START_URL = ["https://nemgiakho.com/nem-cao-su"]
OUTPUT_JSON = "deals-nemgiakho.json"

def create_driver():
    """Creates and returns a Chrome browser that runs in the background."""
    # Setup browser options
    options = Options()
    options.add_argument("--headless=new")  # Run without opening a window
    options.add_argument("--no-sandbox") # Disable the security sandbox (may be needed in some environments)
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems (64MB by default for RAM usage)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
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
    product_card = driver.find_elements(
        By.CSS_SELECTOR, "ul.listsp > li"
    )

    all_deals_on_pages = []

    for card in product_card:
        deal = extract_deal(card)
        if deal and deal["link"] and deal["link"] not in seen:
            all_deals_on_pages.append(deal)
            seen.add(deal["link"])
    
    return all_deals_on_pages


def extract_deal(card):
    try:
        product_info = card.find_element(
            By.CSS_SELECTOR, "div.images"
        )

        product_name = product_info.find_element(
            By.CSS_SELECTOR, "a"
        ).get_attribute("title")
        
        link = product_info.find_element(
            By.CSS_SELECTOR, "a"
        ).get_attribute("href")

        image_url = card.find_element(
            By.CSS_SELECTOR, "img"
        ).get_attribute("src")

        return {
                "product_name": product_name,
                "image_url": image_url,
                "link": link,
            }
    
    except Exception as e:
        print(f"Lỗi khi cào sản phẩm {e}")


def scrape_variations(driver):
    description = ""
    price = None

    try:
        description = driver.find_element(
            By.CSS_SELECTOR, 'div.divdetail.detail'
        ).text
    
    except Exception as e:
        print(f"Lỗi khi tìm mô tả {e}")
        description = "Không có mô tả sản phẩm"

    variations_data = []
    
    size_count = len(driver.find_elements(
            By.CSS_SELECTOR, "select.listsize > option"
        )
    )

    for i in range(size_count):
        size_name = None
        thickness_name = None

        try:
            sizes = driver.find_elements(
                By.CSS_SELECTOR, "select.listsize > option"
            )

        except Exception as e:
            print(f"Lỗi khi tìm size {e}")

        size_btn = sizes[i]
        size = size_btn.get_attribute("textContent")
        size_part = size.split("x")
        
        try:
            if len(size_part) >= 2:
                size_name = f"{size_part[0]}x{size_part[1]}"

            if len(size_part) >= 3:
                thickness_name = size_part[2].replace("cm", "")
        
        except Exception as e:
            print(f"Lỗi khi chia size {e}")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", size_btn)
        driver.execute_script("arguments[0].click();", size_btn)
        time.sleep(2)

        raw_price = driver.find_element(
            By.CSS_SELECTOR, "p.giaban.price"
        ).get_attribute("textContent")
        price = int(raw_price.replace("₫", "").replace(".", ""))
        
        variations_data.append({
            "size": size_name,
            "thickness": thickness_name,
            "price": price,
        })

    
    print(f"Tìm thấy {size_count} kích thước")

    return {
        "description": description,
        "variations": variations_data
    }


def load_all_products(driver):
    load_btns = []

    load_btns = driver.find_elements(
        By.CSS_SELECTOR, 'div.viewmore-category:not(.hideim)'
    )

    while len(load_btns) > 0:
        for load_btn in load_btns:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_btn)
            driver.execute_script("arguments[0].click();", load_btn)
            time.sleep(1.5)
        
        load_btns = driver.find_elements(
            By.CSS_SELECTOR, 'div.viewmore-category:not(.hideim)'
        )

def save_to_json(deals, filename):
    """Lưu danh sách sản phẩm (bao gồm cả biến thể) vào file JSON."""

    if not deals:
        print("Không có dữ liệu để lưu.")
        return

    # Mở file với encoding="utf-8" để không bị lỗi font tiếng Việt
    with open(filename, "w", encoding="utf-8") as file:
        
        # Dùng json.dump để ghi dữ liệu
        # ensure_ascii=False: Bắt buộc phải có để giữ nguyên dấu tiếng Việt (không bị biến thành mã \u00e1)
        # indent=4: Lùi đầu dòng 4 khoảng trắng, giúp file JSON hiện ra có cấu trúc cây thụt lề cực kỳ dễ đọc bằng mắt thường
        json.dump(deals, file, ensure_ascii=False, indent=4)

    print(f"\nĐã lưu thành công {len(deals)} sản phẩm (cùng các biến thể) vào file {filename}")


def main():
    """Hàm chính điều phối toàn bộ quá trình cào dữ liệu 2 lớp.""" 

    print("Đang khởi động trình duyệt")
    driver = create_driver()

    # Mảng chứa toàn bộ dữ liệu cuối cùng
    all_products = []
    seen = set()

    try:
        # PHASE 1: CÀO LẤY THÔNG TIN CƠ BẢN VÀ LINK Ở TRANG DANH MỤC
        for URL in START_URL:
            print(f"\n[PHASE 1] Đang mở trang danh mục: {URL}")
            driver.get(URL)
            time.sleep(10)

            load_all_products(driver)

            print(f"Đang quét danh sách sản phẩm")

            products_on_page = scrape_page(driver, seen)
            all_products.extend(products_on_page)

            print(f"Thu thập được {len(products_on_page)} sản phẩm. (Tổng tạm thời: {len(all_products)})")

        # PHASE 2: CHUI VÀO TỪNG LINK ĐỂ CÀO MÔ TẢ & BIẾN THỂ SIZE
        print("\n==================================================")
        print(f"[PHASE 2] BẮT ĐẦU VÀO TỪNG LINK CỦA {len(all_products)} SẢN PHẨM ĐỂ CÀO SÂU")
        print("==================================================\n")
        seen = set()
        del_index = []
        # Duyệt qua từng sản phẩm đã gom được ở Phase 1
        for index, product in enumerate(all_products, start=1):
            product_url = product.get("link")

            if not product_url:
                continue


            print(f"[{index}/{len(all_products)}] Đang cào chi tiết: {product.get('product_name')}")
            print(f"link: {product.get("link")}")
            
                # Truy cập vào link chi tiết của sản phẩm
            driver.get(product_url)
            time.sleep(5) # Chờ trang chi tiết load

            # Cào mô tả và click chọn từng biến thể size/độ dày
            detail_data = scrape_variations(driver)

            # Nối dữ liệu cào sâu vào dữ liệu cơ bản
            product["description"] = detail_data["description"]
            product["variations"] = detail_data["variations"]

        for i in sorted(del_index, reverse=True):
            del all_products[i]
        
        print(f"Sản phẩm trùng lặp: {len(del_index)}")
        print(f"Tổng sản phẩm thu được: {len(all_products)}")

    finally:
        # Dù code chạy thành công hay văng lỗi giữa chừng, luôn phải đóng trình duyệt
        print("\nĐang đóng trình duyệt")
        driver.quit()

    save_to_json(all_products, OUTPUT_JSON)


if __name__ == "__main__":
    main()