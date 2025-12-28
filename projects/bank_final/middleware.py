
from flask import request, jsonify
import time
request_history = {}
def rate_limit_check():
    ip = request.remote_addr
    now = time.time()
    if ip not in request_history: request_history[ip] = []
    request_history[ip] = [t for t in request_history[ip] if now - t < 60]
    if len(request_history[ip]) > 100: return jsonify({'error': 'Rate limit'}), 429
    request_history[ip].append(now)
