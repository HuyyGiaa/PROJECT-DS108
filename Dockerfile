# 1. Dùng Python 3.13 bản slim theo đúng dự án của bạn
FROM python:3.13-slim

# 2. Thiết lập thư mục làm việc mặc định
WORKDIR /app

# 3. Tối ưu hóa log Python (giúp in log ra terminal ngay lập tức)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Cài đặt trình duyệt Chromium và các gói hỗ trợ để chạy Selenium ngầm trên Linux
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy file requirements và cài đặt các thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy toàn bộ mã nguồn project (trừ những thứ trong .dockerignore)
COPY . .

# 7. Mở cổng 8501 của Streamlit
EXPOSE 8501

# 8. Lệnh chạy giao diện ứng dụng (trỏ thẳng vào file trong thư mục rcm_sys)
CMD ["streamlit", "run", "rcm_sys/app.py", "--server.port=8501", "--server.address=0.0.0.0"]