#!/usr/bin/env python3
"""
Experience API Endpoint
Предоставляет доступ к извлеченному опыту через REST API
"""

from flask import Flask, jsonify
from flask_cors import CORS
import json
from pathlib import Path

app = Flask(__name__)
CORS(app)

BASE_DIR = Path("/Volumes/Z7S/development/GalaxyDevelopers/DevSystem")

@app.route('/api/experience', methods=['GET'])
def get_experience():
    """Возвращает данные извлеченного опыта"""
    experience_file = BASE_DIR / "interface" / "experience_data.json"
    if experience_file.exists():
        with open(experience_file, 'r') as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Experience data not found"}), 404

@app.route('/api/patterns', methods=['GET'])
def get_patterns():
    """Возвращает список активных паттернов"""
    patterns_dir = BASE_DIR / "DOCUMENTS" / "PATTERNS"
    patterns = []
    if patterns_dir.exists():
        for pattern_file in patterns_dir.glob("*.md"):
            patterns.append({
                "name": pattern_file.stem,
                "path": str(pattern_file)
            })
    return jsonify({"patterns": patterns})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "experience_api"})

if __name__ == '__main__':
    print("🚀 Starting Experience API on port 5556...")
    app.run(host='0.0.0.0', port=5556, debug=False)