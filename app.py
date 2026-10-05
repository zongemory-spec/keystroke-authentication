from flask import Flask, request, jsonify
import csv
import os
from auth import extract_features, authenticate_user, build_all_templates, DATA_DIR

app = Flask(__name__)


@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/collect', methods=['POST'])
def collect():
    """
    采集接口：提取特征并追加写入用户对应的 CSV 文件。
    请求体：{ user_id: str, events: [...] }
    返回：{ status: 'ok', total: int } 或 { status: 'error', error: str }
    """
    data    = request.json
    user_id = (data.get('user_id') or '').strip()
    events  = data.get('events', [])

    if not user_id:
        return jsonify({"status": "error", "error": "缺少 user_id"}), 400
    if not events:
        return jsonify({"status": "error", "error": "没有收到按键数据"}), 400

    # 特征提取（含维度校验）
    features = extract_features(events)
    if features is None:
        return jsonify({
            "status": "error",
            "error": "按键数据不完整或维度不对，请重新输入完整的目标文本"
        }), 400

    # 追加保存到 CSV（无表头，纯数值行）
    file_path = os.path.join(DATA_DIR, f"{user_id}.csv")
    with open(file_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(features.tolist())

    # 统计该用户当前总条数
    with open(file_path, 'r', encoding='utf-8') as f:
        total = sum(1 for _ in f)

    print(f"[collect] user={user_id}  total={total}")
    return jsonify({"status": "ok", "total": total})


@app.route('/auth', methods=['POST'])
def authenticate():
    """
    认证接口：单用户异常检测方案。
    请求体：{ user_id: str, events: [...] }
    返回：{ passed: bool, distance: float, threshold: float, claimed: str }
         或 { error: str }
    """
    data    = request.json
    user_id = (data.get('user_id') or '').strip()
    events  = data.get('events', [])

    if not user_id:
        return jsonify({"error": "缺少 user_id"}), 400
    if not events:
        return jsonify({"error": "没有收到按键数据"}), 400

    # 特征提取（与 /collect 使用同一函数，保证特征一致）
    features = extract_features(events)
    if features is None:
        return jsonify({
            "error": "按键数据不完整或维度不对，请重新输入完整的目标文本"
        }), 400

    # 单用户异常检测
    passed, distance, threshold = authenticate_user(user_id, features)

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
    return jsonify({
        "status":  "ok",
        "message": "模板构建完成",
        "details": results
    })


@app.route('/status', methods=['GET'])
def status():
    """查看各用户已采集的样本数量。"""
    result = {}
    if os.path.isdir(DATA_DIR):
        for fname in os.listdir(DATA_DIR):
            if fname.endswith('.csv'):
                uid       = fname[:-4]
                file_path = os.path.join(DATA_DIR, fname)
                with open(file_path, 'r', encoding='utf-8') as f:
                    result[uid] = sum(1 for _ in f)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)