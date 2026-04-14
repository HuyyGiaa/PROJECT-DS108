import json
import time
import csv
from matplotlib import text
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ===== SETTINGS =====
START_URL = "https://vuanem.com/danh-muc/nem"
OUTPUT_JSON = "deals.json"
MAX_PAGES = None  # None means scrape all pages, or set a number like 5
WAIT_TIME = 2  # seconds to wait between pages


# ===== STEP 1: Setup Chrome Browser =====
def create_driver():
    """Creates and returns a Chrome browser that runs in the background."""
    # Setup browser options
    options = Options()
    options.add_argument("--headless=new")  # Run without opening a window
    options.add_argument("--no-sandbox") # Disable the security sandbox (may be needed in some environments)
    options.add_argument("--disable-dev-shm-usage") # Overcome limited resource problems (64MB by default for RAM usage)

    # Create and return the browser
    #(tự động kiểm tra và cài đặt driver Chrome phù hợp với phiên bản trình duyệt 
    #(bởi vì chorme liên tục cập nhật phiên bản mới 
    #nên việc tự động cài đặt driver sẽ giúp tránh lỗi không tương thích giữa driver và trình duyệt))
    service = Service(ChromeDriverManager().install()) 
    return webdriver.Chrome(service=service, options=options)


# ===== STEP 2: Scrape Products from Current Page =====
def scrape_page(driver):
    """Lấy tất cả các thẻ sản phẩm trên trang hiện tại."""
    
    all_deals = []
    
    try:
        # 1. Cơ chế cuộn trang để kích hoạt Lazy Load ảnh và thẻ HTML
        # Cuộn từ từ 3 lần để đảm bảo web load kịp
        for i in range(1, 4):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {i/3});")
            time.sleep(1) # Chờ 1 giây mỗi lần cuộn
            
        # 2. Chờ cho đến khi các thẻ sản phẩm xuất hiện trong HTML (Tối đa 10s)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".product-item"))
        )
        
        # 3. Gom tất cả các thẻ sản phẩm trên trang
        product_cards = driver.find_elements(By.CSS_SELECTOR, ".product-item")
        print(f"Đã tìm thấy {len(product_cards)} sản phẩm trên trang này.")

        # 4. Trích xuất dữ liệu từng thẻ
        for card in product_cards:
            deal = extract_deal(card)
            if deal:  # Chỉ thêm vào list nếu hàm trích xuất không bị lỗi (không trả về None)
                all_deals.append(deal)

    except Exception as e:
        print(f"Lỗi khi tải danh sách sản phẩm trên trang: {e}")

    return all_deals


# ===== STEP 3: Extract Data from One Product Card =====
def extract_deal(card):
    try:
        product_name = card.find_element(By.CSS_SELECTOR, ".product-card-content a[title]").get_attribute("title")
        price = card.find_element(By.CSS_SELECTOR, ".product-price").text
        image_url = card.find_element(By.CSS_SELECTOR, "img").get_attribute("src")
        link = card.find_element(By.CSS_SELECTOR, ".product-card-content a").get_attribute("href")

        # Khai báo sẵn các biến tránh lỗi nếu không tìm thấy
        product_sold_number = None
        rating_score = None
        total_reviews = None

        # Try lấy số lượng bán
        try:
            product_sold_number = card.find_element(By.CSS_SELECTOR, ".product-sold-number").text
        except: pass

        # Try lấy rating và số lượt đánh giá (Dựa trên class trong ảnh image_9e039f.jpg)
        try:
            rating_score = card.find_element(By.CSS_SELECTOR, ".rate-container .rate").text
            total_reviews = card.find_element(By.CSS_SELECTOR, ".rate-container .total").text
        except: pass

        return {
            "product_name": product_name,
            "price": price,
            "image_url": image_url,
            "link": link,
            "product_sold_number": product_sold_number,
            "rating": rating_score,
            "reviews": total_reviews
        }

    except Exception as e:
        print("Lỗi khi cào Card:", e)
        return None

# ===== STEP 4: Scrape All Variations on Product Page =====
def scrape_all_variations_on_page(driver):

    """Hàm cào toàn bộ thông tin: Mô tả, Bình luận, và các Biến thể giá/size"""
    print("Đang cào mô tả sản phẩm")
    
    # Cào Mô tả sản phẩm
    # description = ""
    try:
        description = driver.find_element(By.ID, "content-product-characteristics").text
    except:
        description = "Không có mô tả"


    """Hàm này mô phỏng click vào các nút Size và Độ dày để lấy giá"""
    
    variations_data = []
    
    sizes_count = len(driver.find_elements(By.CSS_SELECTOR, "button.info__size-option"))
    thickness_count = len(driver.find_elements(By.CSS_SELECTOR, "button.info__thickness-option"))
    print(f"Tìm thấy {sizes_count} kích thước và {thickness_count} độ dày.")

    for i in range(sizes_count):
        try:
            # Tìm lại mảng size ở mỗi vòng lặp 
            sizes = driver.find_elements(By.CSS_SELECTOR, "button.info__size-option")
            size_btn = sizes[i]
            size_name = size_btn.get_attribute("data-size") 
            
            # Click size
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", size_btn)
            driver.execute_script("arguments[0].click();", size_btn)
            time.sleep(1)

            # TH1: Có nút độ dày
            if thickness_count > 0:
                for j in range(thickness_count):
                    try:
                        # Tìm lại mảng độ dài ở mỗi vòng lặp
                        thicknesses = driver.find_elements(By.CSS_SELECTOR, "button.info__thickness-option")
                        thick_btn = thicknesses[j] # Bốc đúng nút độ dày ở vị trí thứ j
                        thickness_name = thick_btn.get_attribute("data-thickness")
                        
                        # Click độ dày
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thick_btn)
                        driver.execute_script("arguments[0].click();", thick_btn)
                        time.sleep(1.5) # Chờ giá update
                        
                        # Lấy giá trị
                        current_price = driver.find_element(By.CSS_SELECTOR, ".info__current-price").text
                        current_sku = driver.find_element(By.ID, "variant-sku").get_attribute("value")
                        
                        variations_data.append({
                            "size": size_name,
                            "thickness": thickness_name,
                            "price": current_price,
                            "sku": current_sku
                        })
                    except Exception as e:
                        print(f"Lỗi khi cào độ dày thứ {j+1}: {e}")
                        continue

            # TH2: Không có nút độ dày (Chỉ có size)
            else:
                try:
                    current_price = driver.find_element(By.CSS_SELECTOR, ".info__current-price").text
                    current_sku = driver.find_element(By.ID, "variant-sku").get_attribute("value")
                    
                    variations_data.append({
                        "size": size_name,
                        "thickness": None,
                        "price": current_price,
                        "sku": current_sku
                    })
                except Exception as e:
                    pass
        except Exception as e:
            print(f"Lỗi khi cào size thứ {i+1}: {e}")
            continue
                
    return {
        "description": description,
        "variations": variations_data
    }

# ===== STEP 5: Go to Next Page =====
def go_to_next_page(driver):
    """Chuyển sang trang tiếp theo dựa vào thuộc tính data-page. Trả về True nếu thành công."""

    try:
        # Tìm thẻ li đang active (trang hiện tại)
        active_li = driver.find_element(By.CSS_SELECTOR, "li.active[data-page]")
        
        # Lấy số trang hiện tại và cộng thêm 1
        current_page = int(active_li.get_attribute("data-page"))
        next_page = current_page + 1
        
        # Thử tìm thẻ li của trang tiếp theo
        try:
            # Tìm thẻ li có data-page bằng next_page
            next_li = driver.find_element(By.CSS_SELECTOR, f"li[data-page='{next_page}']")
            
            # Phải click vào thẻ <a> nằm trong thẻ li thì web mới chuyển trang
            next_link = next_li.find_element(By.TAG_NAME, "a")
            
            # Cuộn chuột đến nút đó để không bị lỗi che khuất
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_link)
            time.sleep(1) 
            
            # Click chuyển trang
            driver.execute_script("arguments[0].click();", next_link)
            print(f"Đang chuyển sang trang {next_page}...")
            
            time.sleep(3) # Chờ 3s cho trang mới tải xong
            return True
            
        except Exception:
            print("Đã đến trang cuối cùng. Không còn trang tiếp theo.")
            return False

    except Exception as e:
        print(f"Lỗi khi tìm phân trang: {e}")
        return False


# ===== STEP 6: Save All Deals to CSV File =====
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
        time.sleep(3) # Chờ trang load ban đầu

        page_number = 1
        while True:
            print(f"Đang quét danh sách sản phẩm trang {page_number}")

            # Lấy các thẻ sản phẩm (Step 2)
            products_on_page = scrape_page(driver)
            all_products.extend(products_on_page)

            print(f"Thu thập được {len(products_on_page)} sản phẩm. (Tổng tạm thời: {len(all_products)})")

            # Kiểm tra giới hạn trang 
            if MAX_PAGES and page_number >= MAX_PAGES:
                print(f"Đã đạt giới hạn test {MAX_PAGES} trang.")
                break

            # Bấm sang trang tiếp theo (gọi Step 5)
            if not go_to_next_page(driver):
                break

            page_number += 1

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
                time.sleep(2) # Chờ trang chi tiết load

                # Cào mô tả và click chọn từng biến thể size/độ dày
                detail_data = scrape_all_variations_on_page(driver)

                # Nối dữ liệu cào sâu vào dữ liệu cơ bản
                product["description"] = detail_data["description"]
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


    