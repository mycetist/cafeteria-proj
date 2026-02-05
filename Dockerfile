# Use the same python image you were using
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# 1. Install System Dependencies (Done ONCE during build, not every restart)
RUN apt-get update && \
    apt-get install -y gcc default-libmysqlclient-dev pkg-config && \
    rm -rf /var/lib/apt/lists/*

# 2. Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your application code
COPY . .

# (Optional) The default command, though we will override this in compose to keep your DB logic
CMD ["python", "run.py", "--host=0.0.0.0", "--port=5000"]