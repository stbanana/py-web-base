# routes/api_routes.py
from flask import Blueprint, jsonify, request
from runtime_logging import read_log_entries

api_bp = Blueprint('api', __name__)
api_test = Blueprint('test', __name__)

@api_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "pong"}), 200


@api_bp.route('/logs', methods=['GET'])
def get_logs():
    channel = request.args.get('channel', 'error')
    limit = request.args.get('limit', '100')
    try:
        limit_value = max(1, min(int(limit), 1000))
    except ValueError:
        limit_value = 100

    entries = read_log_entries(channel=channel, limit=limit_value)
    return jsonify({"channel": channel, "count": len(entries), "entries": entries}), 200