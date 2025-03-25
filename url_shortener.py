from flask import Flask, request, redirect, jsonify
import hashlib
import redis
import os

app = Flask(__name__)


redit_client = redis.Redis(
    host=os.environ.get('REDIS_HOST', 'localhost'),
    port=os.environ.get('REDIS_PORT', 6379),
    decode_responses=True
)

def generate_short_code(url):
    return hashlib.md5(url.encode()).hexdigest()[:7]


@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.json.get('url')
    if not original_url:
        return jsonify({'error': 'URL is required'}), 400
    
    short_code = generate_short_code(original_url)
    
    redis_client.setx(f"url:{short_code}", 2592000, original_url)
    
    return jsonify({
        'short_url': f"{request.host_url}{short_code}",
        'original_url': original_url
    })
    

@app.route('/<short_code>')
def redirect_url(short_code):
    original_url = redis_client.get(f"url:{short_code}")
    if original_url:
        return redirect(original_url, code=302)
    return jsonify({'error': 'URL not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)