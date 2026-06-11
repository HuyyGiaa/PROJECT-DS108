# 🛏️ Mattress Recommender System (Hệ thống gợi ý giường nệm)

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 📖 1. Giới thiệu dự án
Trong bối cảnh thương mại điện tử phát triển, người dùng mua sắm nội thất (đặc biệt là giường nệm) thường gặp khó khăn do **dữ liệu bị phân mảnh** trên nhiều trang web khác nhau và thiếu tính chuẩn hóa. Thêm vào đó, các công cụ tìm kiếm hiện tại chủ yếu sử dụng "bộ lọc cứng" (hard-filter), thiếu linh hoạt và dễ dẫn đến việc trả về 0 kết quả nếu người dùng thiết lập tiêu chí quá khắt khe.

**Mattress Recommender System** là một giải pháp toàn diện nhằm giải quyết các vấn đề trên. Dự án xây dựng một *data pipeline* hoàn chỉnh: từ tự động thu thập dữ liệu (crawling) trên nhiều nền tảng, tiền xử lý, chuẩn hóa, đến việc trích xuất đặc trưng và xây dựng một **hệ thống gợi ý thông minh (Soft-match)**. Hệ thống giúp hợp nhất dữ liệu và gợi ý các sản phẩm tương tự hoặc thay thế dựa trên nhu cầu thực tế của người dùng.

## 🚀 2. Các tính năng chính (Key Features)
* **Automated Data Crawling:** Tự động thu thập và cập nhật dữ liệu nệm từ các trang web lớn như: *Vua Nệm, Thế Giới Nệm, Kho Nệm Tổng Hợp, Thế Giới Giường Nệm*.
* **Data Cleaning & Standardization:** Xử lý dữ liệu nhiễu, điền khuyết giá trị (missing values) và chuẩn hóa các thuộc tính không đồng nhất (giá, chất liệu, độ cứng,...).
* **Feature Engineering:** * Xử lý văn bản mô tả bằng TF-IDF Vectorizer.
  * Mã hóa các biến phân loại: One-Hot Encoding (cho Thương hiệu), Ordinal Encoding (cho Độ cứng).
  * Chuẩn hóa dữ liệu số (Scaling).
* **Content-Based Recommendation:** Gợi ý sản phẩm có độ tương đồng cao dựa trên các đặc trưng kết hợp (đặc trưng số và văn bản).
* **Interactive Data Visualization:** Cung cấp các biểu đồ phân tích sâu (EDA) về phân phối giá, thương hiệu, chất liệu và ma trận tương quan.

## 🛠️ 3. Công nghệ sử dụng (Tech Stack)
* **Ngôn ngữ:** Python
* **Thu thập dữ liệu:** `Selenium`
* **Xử lý & Học máy:** `Pandas`, `NumPy`, `Scikit-learn`
* **Trực quan hóa:** `Matplotlib`, `Seaborn`
* **Triển khai & Môi trường:** `Docker`, `Jupyter Notebook`

## 📂 4. Cấu trúc thư mục (Project Structure)

    mattress-recommender/
    ├── crawlers/                  # Các kịch bản thu thập dữ liệu (Python scripts)
    │   ├── crawl-khonemtonghop.py
    │   ├── crawl-thegioinem.py
    │   ├── crawl-vuanem.py
    │   └── crawl_thegioigiuongnem.py
    ├── data/                      # Lưu trữ dữ liệu qua từng giai đoạn xử lý
    │   ├── raw/                   # Dữ liệu gốc thu thập từ web (.json)
    │   ├── processed/             # Dữ liệu đã qua làm sạch bước 1 (.csv)
    │   └── final/                 # Ma trận đặc trưng & dữ liệu sạch cuối cùng (.npz, .csv)
    ├── models/                    # Models & Encoders đã được huấn luyện
    │   ├── oe_firmness.pkl        # Model mã hóa thứ bậc (độ cứng)
    │   ├── ohe_brand.pkl          # Model mã hóa one-hot (thương hiệu)
    │   ├── scaler.pkl             # Model chuẩn hóa dữ liệu số
    │   ├── tfidf_desc.pkl         # Model vector hóa mô tả (TF-IDF)
    │   └── tfidf_mat.pkl          # Ma trận TF-IDF
    ├── notebooks/                 # Môi trường phân tích & thử nghiệm
    │   ├── cleaning.ipynb
    │   ├── eda.ipynb
    │   └── preprocessing.ipynb
    ├── output/                    # Kết quả trực quan hóa dữ liệu (EDA)
    │   ├── boxplot_*.png
    │   ├── categorical_distributions.png
    │   ├── heatmap_*.png
    │   └── scatter_matrix.png
    ├── rcm_sys/                   # Mã nguồn chính của Hệ thống gợi ý
    │   ├── app.py                 # File thực thi giao diện / API
    │   └── rcm_sys.py             # Lõi logic của hệ thống gợi ý
    ├── src/                       # Các module xử lý lõi (Core modules)
    │   ├── __init__.py
    │   ├── cleaning.py            # Logic làm sạch dữ liệu
    │   ├── data_loader.py         # Hàm hỗ trợ tải dữ liệu
    │   └── preprocessing.py       # Logic tiền xử lý và trích xuất đặc trưng
    ├── .dockerignore
    ├── .gitignore
    ├── config.py                  # Các biến hằng số cấu hình hệ thống
    ├── Dockerfile                 # File cấu hình đóng gói ứng dụng
    ├── README.md                  # Tài liệu mô tả dự án
    └── requirements.txt           # Danh sách các thư viện phụ thuộc

## ⚙️ 5. Hướng dẫn Cài đặt & Sử dụng (Getting Started)

### 5.1. Chạy trên môi trường Local
**Bước 1: Clone kho lưu trữ**
`git clone https://github.com/HuyyGiaa/mattress-recommender.git`
`cd mattress-recommender`

**Bước 2: Thiết lập môi trường ảo và cài đặt thư viện**
Tạo môi trường ảo:
`python -m venv venv`

Kích hoạt môi trường ảo (Windows):
`venv\Scripts\activate`

Cài đặt thư viện:
`pip install -r requirements.txt`

**Bước 3: Chạy Pipeline xử lý**
1. Cập nhật dữ liệu mới: `python crawlers/crawl-vuanem.py`
2. Chạy quá trình tiền xử lý bằng cách thực thi các file trong `src/` hoặc `notebooks/`.

**Bước 4: Khởi chạy Hệ thống gợi ý**
`cd rcm_sys`
`python app.py`

### 5.2. Chạy bằng Docker
Hệ thống đã được cấu hình sẵn `Dockerfile`. Triển khai nhanh bằng các lệnh sau:

Xây dựng Docker image:
`docker build -t mattress-rcm .`

Khởi chạy container:
`docker run -p 8000:8000 mattress-rcm` 

## 🧠 6. Phương pháp luận (Methodology)
* **Xây dựng Data Pipeline:** Dữ liệu thô từ các nguồn khác nhau được gộp lại và đưa qua quy trình làm sạch nhiễu.
* **Feature Representation:**
  * Thuộc tính phân loại hạng mục được chuyển đổi bằng `OneHotEncoder` và `OrdinalEncoder`.
  * Văn bản mô tả sản phẩm được biểu diễn thành các vector sử dụng `TfidfVectorizer`.
* **Similarity Computation:** Sử dụng phương pháp **Content-based Filtering**, tính toán độ đo tương đồng Cosine (Cosine Similarity) để so sánh khoảng cách giữa các vector đặc trưng, từ đó gợi ý Top-K sản phẩm phù hợp.

## 👨‍💻 7. Tác giả
* **Nguyễn Nhớ Bảo Huy** - GitHub: [@nnbaohuy-dev](https://github.com/nnbaohuy-dev)
* **Bùi Đức Gia Huy** - GitHub: [@HuyyGiaa](https://github.com/HuyyGiaa)

## 📜 8. Giấy phép (License)
Dự án được phân phối dưới giấy phép MIT. Xem chi tiết trong repository.
