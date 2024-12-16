# Builder stage for dependencies
FROM python:3.11-slim-bookworm as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim-bookworm

WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY . .

# Expose ports
EXPOSE 5000

# Healthcheck for Flask app
HEALTHCHECK CMD curl --fail http://localhost:5000 || exit 1

# Run the app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "avauth_proxy.app:app"]
