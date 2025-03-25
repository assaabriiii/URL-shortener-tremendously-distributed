FROM python:3.9-slim

WORKDIR /app

# First copy requirements to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy the rest
COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "url_shortener:app"]