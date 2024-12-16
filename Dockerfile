# Use a slim base image for reduced image size
FROM python:3.11-slim-bookworm

# Set a working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application source code into the container
COPY . .

# Ensure proper permissions for logs and Nginx
RUN mkdir -p /app/logs && chmod -R 755 /app/logs

# Expose ports for the application and Nginx
EXPOSE 5000
EXPOSE 8000

# Default command to start the app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "avauth_proxy.app:app"]
