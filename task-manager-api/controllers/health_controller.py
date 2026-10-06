from datetime import datetime

from flask import jsonify

from config.constants import API_VERSION


def health():
    return jsonify({'status': 'ok', 'timestamp': str(datetime.now())}), 200


def index():
    return jsonify({'message': 'Task Manager API', 'version': API_VERSION}), 200
