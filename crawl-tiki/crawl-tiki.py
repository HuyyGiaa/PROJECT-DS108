import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

START_URL = "https://tiki.vn/nem-bong-ep/c23380"
OUTPUT_JSON = "deals.json"
MAX_PAGES = None  # None means scrape all pages, or set a number like 5
WAIT_TIME = 2  # seconds to wait between pages

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
    """Gets all product deals from the current page."""
    """ # 1. Cơ chế cuộn trang để kích hoạt Lazy Load ảnh và thẻ HTML
        # Cuộn từ từ 3 lần để đảm bảo web load kịp
    for i in range(1, 10):
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/9});")
        time.sleep(1) # Chờ 1 giây mỗi lần cuộn"""
    # Wait for products to load (up to 10 seconds)

    # until the element with attribute data-component-type="s-search-result" is present
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'a.product-item[data-view-id="product_list_item"]')
        )
    )
    time.sleep(10)

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
            By.CSS_SELECTOR, "h3"
        ).get_attribute("textContent")

        # Giá
        """price = card.find_element(
            By.CSS_SELECTOR, "div.price-discount__price"
        ).text"""

        # Ảnh
        image_url = card.find_element(
            By.CSS_SELECTOR, "picture.webpimg-container source"
        ).get_attribute("srcset").split(",")[0].split()[0]

        link = card.get_attribute("href")
        seen.add(link)

        product_sold_number = None
        # Try lấy số lượng bán
        try:
            product_sold_number = card.find_element(By.CSS_SELECTOR, "span.quantity").text
        except: pass

        return {
            "product_name": product_name,
            # "price": price,
            "image_url": image_url,
            "link": link,
            "product_sold_number": product_sold_number,
        }

    except Exception as e:
        print("Lỗi khi cào Card:", e)
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

def get_new_products(driver, seen):
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

def scrape_all_variations_on_page(driver):

    """Hàm cào toàn bộ thông tin: Đánh giá, Mô tả, Bình luận, và các Biến thể giá/size"""
    print("Đang cào đánh giá")
    rating_score = None
    total_reviews = None

    try:
        rating_score = driver.find_element(By.CSS_SELECTOR, "div[style='margin-right:4px;font-size:14px;line-height:150%;font-weight:500']").text
    except Exception:
        rating_score = None

    # Số lượng đánh giá
    try:
        total_reviews = driver.find_element(By.CSS_SELECTOR, "a.number[data-view-id='pdp_main_view_review']").text
    except Exception:
        total_reviews = None
    print("Đang cào mô tả sản phẩm")
    
    # Cào Mô tả sản phẩm
    # Cào Mô tả sản phẩm
    last_height = driver.execute_script("return document.body.scrollHeight")
    for i in range(10):  # giới hạn số lần scroll
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(2)  # chờ load sản phẩm mới
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height and i > 5:
            break
        
        last_height = new_height
    
    description = ""
    
    try:
        # Chờ tối đa 30s
        try:
            # Find the Next button
            seemore_button = driver.find_element(By.CSS_SELECTOR, 'a.btn-more')
            seemore_button.click()

        except Exception:
            print("Không có nút xem thêm")

        wait = WebDriverWait(driver, 30)
        
        # Dùng XPath: Tìm thẻ div chứa chữ "Mô tả sản phẩm", 
        # sau đó chọn thẻ div (chứa nội dung) là anh em ngay phía sau nó (following-sibling)
        description_xpath = "//div[contains(text(), 'Mô tả sản phẩm')]/following-sibling::div"
        
        card = wait.until(
            EC.presence_of_element_located((By.XPATH, description_xpath))
        )
        
        # Lấy tất cả các thẻ <p> bên trong khối mô tả đó
        paragraphs = card.find_elements(By.TAG_NAME, "p")
        description = "\n".join(
            p.get_attribute("textContent").strip() for p in paragraphs if p.get_attribute("textContent")
        )

    except Exception as e:
        print(f"\n[!] LỖI CÀO MÔ TẢ: {e}\n")
        description = "Không có mô tả"


    """Hàm này mô phỏng click vào các nút Size và Độ dày để lấy giá"""
    
    variations_data = []
    
    sizes_count = len(
        driver.find_elements(
            By.XPATH,
            "//div[@data-view-id='pdp_main_select_configuration' and (contains(@data-view-label, 'Kích') or contains(@data-view-label, 'kích'))]//div[@data-view-id='pdp_main_select_configuration_item']"
        )
    )
    thickness_count = len(
        driver.find_elements(
            By.CSS_SELECTOR, "div[data-view-id='pdp_main_select_configuration'][data-view-label*='dày'] [data-view-id='pdp_main_select_configuration_item']"
        )
    )
    print(f"Tìm thấy {sizes_count} kích thước và {thickness_count} độ dày.")

    #TH1: Có nút độ dày
    if sizes_count > 0:
        if thickness_count > 0:
            # Tìm lại mảng size ở mỗi vòng lặp 
            sizes = driver.find_elements(
                By.XPATH,
                "//div[@data-view-id='pdp_main_select_configuration' and (contains(@data-view-label, 'Kích') or contains(@data-view-label, 'kích'))]//div[@data-view-id='pdp_main_select_configuration_item']"
            )
            # Tìm lại mảng độ dài ở mỗi vòng lặp
            thicknesses = driver.find_elements(
                By.CSS_SELECTOR, "div[data-view-id='pdp_main_select_configuration'][data-view-label*='dày'] [data-view-id='pdp_main_select_configuration_item']"
            )
            for i in range(sizes_count):
                try:
                    size_btn = sizes[i]
                    size_name = size_btn.find_element(
                        By.CSS_SELECTOR, "span"
                    ).text 
                    
                    # Click size
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", size_btn)
                    try:
                        size_btn.click()
                    except:
                        driver.execute_script("arguments[0].click();", size_btn)
                    time.sleep(1)

                    # TH1: Có nút độ dày
                    for j in range(thickness_count):
                        try:
                            thick_btn = thicknesses[j] # Bốc đúng nút độ dày ở vị trí thứ j
                            thickness_name = thick_btn.find_element(
                                By.CSS_SELECTOR, "span"
                            ).text

                            # Click độ dày
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thick_btn)
                            try:
                                thick_btn.click()
                            except:
                                driver.execute_script("arguments[0].click();", thick_btn)
                            time.sleep(1.5) # Chờ giá update
                            
                            # Lấy giá trị
                            current_price = driver.find_element(
                                By.CSS_SELECTOR, "div.product-price__current-price"
                            ).text
                            
                            variations_data.append({
                                "size": size_name,
                                "thickness": thickness_name,
                                "price": current_price,
                            })
                        except Exception as e:
                            print(f"Lỗi khi cào độ dày thứ {j+1}: {e}")
                            continue
                except Exception as e:
                    print(f"Lỗi khi cào size thứ {i+1}: {e}")
                    continue

            # TH2: Không có nút độ dày (Chỉ có size)
        else:
            sizes = driver.find_elements(
                By.XPATH,
                "//div[@data-view-id='pdp_main_select_configuration' and (contains(@data-view-label, 'Kích') or contains(@data-view-label, 'kích'))]//div[@data-view-id='pdp_main_select_configuration_item']"
            )
            if len(re.split(r'[x*]', sizes[0].text)) == 3:
                for i in range(sizes_count):
                    try:
                        size_btn = sizes[i]
                        raw_size_name = size_btn.find_element(
                            By.CSS_SELECTOR, "span"
                        ).text 
                        
                        part = re.split(r'[x*]', raw_size_name.replace(" ", ""))
                        size_name = part[0] + 'x' + part[1]
                        thickness_name = part[2]

                        # Click size
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", size_btn)
                        try:
                            size_btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", size_btn)
                        time.sleep(1)
                        
                        current_price = driver.find_element(
                            By.CSS_SELECTOR, "div.product-price__current-price"
                        ).text

                        variations_data.append({
                            "size": size_name,
                            "thickness": thickness_name,
                            "price": current_price,
                        })

                    except Exception as e:
                        print(f"Lỗi khi cào size thứ {i+1}: {e}")
                        continue
            else:
                for i in range(sizes_count):
                    try:
                        size_btn = sizes[i]
                        size_name = size_btn.find_element(
                            By.CSS_SELECTOR, "span"
                        ).text 

                        # Click size
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", size_btn)
                        try:
                            size_btn.click()
                        except:
                            driver.execute_script("arguments[0].click();", size_btn)
                        time.sleep(1)
                        
                        raw_thicknesses = driver.find_element(By.CSS_SELECTOR, "h1").text.replace("/", " ")
                        thicknesses = [
                            f"{num}cm"
                            for num in map(int, re.findall(r"\d+(?=\s*cm)", raw_thicknesses))
                            if num < 30
                        ]   
                        current_price = driver.find_element(
                            By.CSS_SELECTOR, "div.product-price__current-price"
                        ).text

                        for thickness_name in thicknesses:
                            variations_data.append({
                                "size": size_name,
                                "thickness": thickness_name,
                                "price": current_price,
                            })

                    except Exception as e:
                        print(f"Lỗi khi cào size thứ {i+1}: {e}")
                        continue
    else:
        current_price = driver.find_element(
            By.CSS_SELECTOR, "div.product-price__current-price"
        ).text

        variations_data.append({
            "price": current_price,
        })

    return {
        "rating": rating_score,
        "review": total_reviews,
        "description": description,
        "variations": variations_data,
    }

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


# ===== STEP 7: Main Program - Lắp ráp cỗ máy =====
def main():
    """Hàm chính điều phối toàn bộ quá trình cào dữ liệu 2 lớp.""" 

    print("Đang khởi động trình duyệt")
    driver = create_driver()

    # Mảng chứa toàn bộ dữ liệu cuối cùng
    all_products = []

    try:
        # PHASE 1: CÀO LẤY THÔNG TIN CƠ BẢN VÀ LINK Ở TRANG DANH MỤC
        print(f"\n[PHASE 1] Đang mở trang danh mục: {START_URL}")
        driver.get(START_URL)

        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(20):  # giới hạn số lần scroll
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)  # chờ load sản phẩm mới
            new_height = driver.execute_script("return document.body.scrollHeight")
            
            if new_height == last_height and i > 5:
                break
            
            last_height = new_height

        seen = set()
        products_on_page = scrape_page(driver, seen)
        all_products.extend(products_on_page)
        print(f"Thu thập được {len(products_on_page)} sản phẩm. (Tổng tạm thời: {len(all_products)})")
        
        while load_more_page(driver):
            last_height = driver.execute_script("return document.body.scrollHeight")
            for i in range(10):  # giới hạn số lần scroll
                driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(2)  # chờ load sản phẩm mới
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height and i > 5:
                    break
                
                last_height = new_height
                
            new_products = get_new_products(driver, seen)
            all_products.extend(new_products)
            print(f"Found {len(new_products)} deals (Total so far: {len(all_products)})")

        # PHASE 2: CHUI VÀO TỪNG LINK ĐỂ CÀO MÔ TẢ & BIẾN THỂ SIZE
        print("\n==================================================")
        print(f"[PHASE 2] BẮT ĐẦU VÀO TỪNG LINK CỦA {len(all_products)} SẢN PHẨM ĐỂ CÀO SÂU")
        print("==================================================\n")

        # Duyệt qua từng sản phẩm đã gom được ở Phase 1
        for index, product in enumerate(all_products, start=1):
            product_url = product.get("link")
            
            if not product_url:
                continue

            print(f"[{index}/{len(all_products)}] Đang cào chi tiết: {product.get('product_name')}")
            
            try:
                # Truy cập vào link chi tiết của sản phẩm
                driver.get(product_url)
                time.sleep(10) # Chờ trang chi tiết load

                # Cào mô tả và click chọn từng biến thể size/độ dày
                detail_data = scrape_all_variations_on_page(driver)

                # Nối dữ liệu cào sâu vào dữ liệu cơ bản
                product["description"] = detail_data["description"]
                product["rating"] = detail_data["rating"]
                product["review"] = detail_data["review"]
                product["variations"] = detail_data["variations"]

            except Exception as e:
                print(f" Lỗi khi cào chi tiết sản phẩm {product_url}: {e}")
                # Gán giá trị mặc định nếu trang này bị lỗi để không hỏng cấu trúc JSON
                product["description"] = "Lỗi khi tải"
                product["variations"] = []

    finally:
        # Dù code chạy thành công hay văng lỗi giữa chừng, luôn phải đóng trình duyệt
        print("\nĐang đóng trình duyệt")
        driver.quit()

    save_to_json(all_products, OUTPUT_JSON)


# Run the program
if __name__ == "__main__":
    main()
