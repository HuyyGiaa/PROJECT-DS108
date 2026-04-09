from playwright.sync_api import sync_playwright

def crawl_vuanem():
    with sync_playwright() as p:
        # headless=False để nó hiện hẳn cái trình duyệt lên cho bạn xem nó đang làm gì
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page()
        
        url = "https://vuanem.com/nem-cao-su-gummi-classic.html?sku=10302009"
        print("Đang mở trang web...")
        page.goto(url)

        # Đợi một chút cho web render xong giao diện (quan trọng)
        page.wait_for_timeout(3000) # Đợi 3 giây

        # LẤY DỮ LIỆU
        # Thay '.class-cua-gia-tien' bằng cái class bạn tìm được ở Bước 1
        price_selector = 'info__current-price' 
        
        try:
            # Tìm phần tử và lấy chữ bên trong nó
            price_text = page.locator(price_selector).first.inner_text()
            print(f"Giá nệm cào được là: {price_text}")
        except Exception as e:
            print("Không tìm thấy giá tiền, hãy kiểm tra lại CSS Selector!")

        browser.close()

if __name__ == "__main__":
    crawl_vuanem()