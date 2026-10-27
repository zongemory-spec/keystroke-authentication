from flask import Flask, request, jsonify
import csv
import os
import pickle
from pathlib import Path
from werkzeug.exceptions import RequestEntityTooLarge
from auth import (extract_features, authenticate_user, build_all_templates, DATA_DIR,
                  InputError, validate_user_id, safe_user_path)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024


@app.errorhandler(InputError)
def invalid_input(exc):
    return jsonify(status='error', error=str(exc)), 400


@app.errorhandler(RequestEntityTooLarge)
def oversized(_exc):
    return jsonify(status='error', error='请求过大，请只提交一次完整输入'), 413


def request_features():
    if not request.is_json:
        raise InputError('请发送 JSON 请求')
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != {'user_id', 'events'}:
        raise InputError('请求必须包含 user_id 和 events，且不能包含其他字段')
    uid = validate_user_id(data['user_id'])
    features = extract_features(data['events'])
    if features is None:
        raise InputError('按键数据无效，请完整输入 hello world 并松开全部按键后重试')
    return uid, features


@app.route('/')
def index():
    return Path(__file__).with_name('index.html').read_text(encoding='utf-8')


@app.route('/collect', methods=['POST'])
def collect():
    """
    采集接口：提取特征并追加写入用户对应的 CSV 文件。
    请求体：{ user_id: str, events: [...] }
    返回：{ status: 'ok', total: int } 或 { status: 'error', error: str }
    """
    user_id, features = request_features()

    # 追加保存到 CSV（无表头，纯数值行）
    file_path = safe_user_path(DATA_DIR, user_id, '.csv')
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open('a', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(features.tolist())
        with file_path.open(encoding='utf-8') as f:
            total = sum(1 for _ in f)
    except OSError:
        return jsonify(status='error', error='保存失败，请检查本地目录权限'), 500
    return jsonify({"status": "ok", "total": total})


@app.route('/auth', methods=['POST'])
def authenticate():
    """
    认证接口：单用户异常检测方案。
    请求体：{ user_id: str, events: [...] }
    返回：{ passed: bool, distance: float, threshold: float, claimed: str }
         或 { error: str }
    """
    user_id, features = request_features()
    try:
        passed, distance, threshold = authenticate_user(user_id, features)
    except InputError:
        raise
    except (OSError, ValueError, TypeError, AttributeError, EOFError, pickle.UnpicklingError):
        return jsonify(status='error', error='本地模板无法使用，请备份数据后重新构建'), 400

    if isinstance(distance, str):
        return jsonify({"error": distance}), 400

    return jsonify({
        "passed":    passed,
        "distance":  round(distance,  4),
        "threshold": round(threshold, 4),
        "claimed":   user_id
    })


@app.route('/build_templates', methods=['POST'])
def build_templates():
    """
    手动触发：为 data/ 下所有用户生成/更新模板。
    返回：{ status: 'ok', message: str, details: { user_id: msg } }
    """
    results = build_all_templates()
    built = sum(message.startswith('成功') for message in results.values())
    return jsonify({
        "status":  "ok",
        "message": "模板构建完成",
        "details": results,
        "built": built,
        "failed": len(results) - built
    })


@app.route('/status', methods=['GET'])
def status():
    """查看各用户已采集的样本数量。"""
    result = {}
    if os.path.isdir(DATA_DIR):
        for fname in os.listdir(DATA_DIR):
            if fname.endswith('.csv'):
                try:
                    uid = validate_user_id(fname[:-4])
                    file_path = safe_user_path(DATA_DIR, uid, '.csv')
                    with file_path.open(encoding='utf-8') as f:
                        result[uid] = sum(1 for _ in f)
                except (InputError, OSError, UnicodeError):
                    continue
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=False, port=5000)
