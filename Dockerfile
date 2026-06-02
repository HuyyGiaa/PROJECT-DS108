# Dùng Python 3.10 bản slim 
FROM python:3.10-slim

# Thiết lập thư mục làm việc mặc định
WORKDIR /app

# Tối ưu hóa log Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Cài đặt trình duyệt Chromium và các gói hỗ trợ để chạy Selenium ngầm trên Linux
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy file requirements và cài đặt các thư viện
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn project (trừ những thứ trong .dockerignore)
COPY . .

# Mở cổng 8501 của Streamlit
EXPOSE 8501

# Lệnh chạy giao diện ứng dụng
CMD ["streamlit", "run", "rcm_sys/app.py", "--server.port=8501", "--server.address=0.0.0.0"]