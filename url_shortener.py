from flask import Flask, request, redirect, jsonify
import hashlib
import redis
import os
import time
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def create_redis_connection():
    max_retries = 5
    retry_delay = 1
    
    for i in range(max_retries):
        try:
            client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'redis1'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            client.ping()  # Test connection
            return client
        except redis.ConnectionError as e:
            logging.warning(f"Redis connection failed (attempt {i+1}): {e}")
            if i == max_retries - 1:
                raise
            time.sleep(retry_delay)
            retry_delay *= 2

redis_client = create_redis_connection()

@app.route('/health')
def health_check():
    try:
        redis_client.ping()
        return 'OK', 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return str(e), 500

def generate_short_code(url):
    return hashlib.md5(url.encode()).hexdigest()[:7]

@app.route('/shorten', methods=['POST'])
def shorten_url():
    try:
        original_url = request.json.get('url')
        if not original_url:
            return jsonify({'error': 'URL is required'}), 400
        
        short_code = generate_short_code(original_url)
        redis_client.setex(f"url:{short_code}", 2592000, original_url)
        
        return jsonify({
            'short_url': f"{request.host_url}{short_code}",
            'original_url': original_url
        })
    except Exception as e:
        logging.error(f"Shorten error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/<short_code>')
def redirect_url(short_code):
    try:
        original_url = redis_client.get(f"url:{short_code}")
        if original_url:
            return redirect(original_url, code=302)
        return jsonify({'error': 'URL not found'}), 404
    except Exception as e:
        logging.error(f"Redirect error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)