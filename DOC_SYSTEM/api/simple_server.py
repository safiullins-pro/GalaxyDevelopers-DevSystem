#!/usr/bin/env python3

from flask import Flask, jsonify
from flask_cors import CORS
from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

app = Flask(__name__)
CORS(app)

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("Starting DOC_SYSTEM API on port 37777...")
    app.run(host='127.0.0.1', port=37777, debug=False)