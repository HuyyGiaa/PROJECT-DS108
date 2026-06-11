# 🛏️ Mattress Recommender System (Hệ thống gợi ý nệm)

Dự án này là một hệ thống thu thập, xử lý dữ liệu và gợi ý sản phẩm nệm. Hệ thống thực hiện một đường ống dữ liệu (data pipeline) hoàn chỉnh từ việc tự động thu thập thông tin trên các trang thương mại điện tử, tiền xử lý/chuẩn hóa dữ liệu thô, phân tích khám phá (EDA), cho đến việc xây dựng các đặc trưng (features) và triển khai một ứng dụng gợi ý sản phẩm cho người dùng.

## 📂 Cấu trúc thư mục (Project Structure)

Dự án được tổ chức theo cấu trúc sau nhằm đảm bảo tính module hóa và dễ dàng mở rộng:

```text
mattress-recommender/
├── crawlers/                  # Các script Python cào dữ liệu từ nhiều nguồn
│   ├── crawl-khonemtonghop.py
│   ├── crawl-thegioinem.py
│   ├── crawl-vuanem.py
│   └── crawl_thegioigiuongnem.py
├── data/                      # Quản lý vòng đời của dữ liệu
│   ├── raw/                   # Dữ liệu thô dạng JSON lấy từ crawlers
│   ├── processed/             # Dữ liệu đã qua bước làm sạch ban đầu (CSV)
│   └── final/                 # Dữ liệu cuối cùng và ma trận đặc trưng (NPZ, CSV)
├── models/                    # Lưu trữ các objects đã được huấn luyện (Pickle)
│   ├── oe_firmness.pkl        # Ordinal Encoder cho độ cứng
│   ├── ohe_brand.pkl          # One-Hot Encoder cho thương hiệu
│   ├── scaler.pkl             # Scaler chuẩn hóa dữ liệu số
│   ├── tfidf_desc.pkl         # TF-IDF Vectorizer cho văn bản mô tả
│   └── tfidf_mat.pkl          # Ma trận TF-IDF
├── notebooks/                 # Môi trường nghiên cứu và thử nghiệm (Jupyter)
│   ├── cleaning.ipynb
│   ├── eda.ipynb
│   └── preprocessing.ipynb
├── output/                    # Các biểu đồ trực quan hóa từ quá trình EDA
│   └── *.png                  # (Heatmaps, Boxplots, Distributions,...)
├── rcm_sys/                   # Ứng dụng hệ thống gợi ý (Recommender System)
│   ├── app.py                 # File chạy ứng dụng chính (ví dụ: Streamlit/Flask)
│   └── rcm_sys.py             # Core logic của hệ thống gợi ý
├── src/                       # Các module mã nguồn core được đóng gói
│   ├── cleaning.py            # Logic làm sạch dữ liệu
│   ├── data_loader.py         # Hàm hỗ trợ tải và đọc dữ liệu
│   └── preprocessing.py       # Logic chuẩn hóa và tạo đặc trưng
├── Dockerfile                 # Cấu hình containerization để deploy
├── config.py                  # Các biến cấu hình và hằng số của hệ thống
└── requirements.txt           # Danh sách các thư viện phụ thuộc
