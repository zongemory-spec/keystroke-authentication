import pandas as pd
import numpy as np
import os
import pickle
from sklearn.preprocessing import StandardScaler



TARGET     = "hello world"   # 目标字符串，与前端保持一致
TARGET_LEN = len(TARGET)     # 11

DATA_DIR  = "data"
MODEL_DIR = "models"

os.makedirs(DATA_DIR,  exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
# ─────────────────────────────────────────────────────────────


def extract_features(events):

    # 按顺序分离 down / up 序列
    down_seq = [(e['key'], e['timestamp']) for e in events if e['action'] == 'down']
    up_seq   = [(e['key'], e['timestamp']) for e in events if e['action'] == 'up']

    # 维度校验：down 和 up 数量必须都等于目标字符串长度
    if len(down_seq) != TARGET_LEN or len(up_seq) != TARGET_LEN:
        return None

    # ── Dwell Time：按字符逐一匹配（正确处理重复字符）──
    dwell_times = []
    for i, ch in enumerate(TARGET):
        # 找出该字符所有出现的 down/up 时间戳列表
        d_list = [t for k, t in down_seq if k == ch]
        u_list = [t for k, t in up_seq   if k == ch]
        if i < len(d_list) and i < len(u_list):
            dwell_times.append(u_list[i] - d_list[i])
        else:
            dwell_times.append(0.0)  # 异常情况补零，后续维度校验会拦截

    # ── DD Flight Time：相邻两次按下的时间差 ──
    dd_times = [
        down_seq[i][1] - down_seq[i - 1][1]
        for i in range(1, len(down_seq))
    ]

    # ── UD Flight Time：上一键弹起到当前键按下的时间差 ──
    ud_times = [
        down_seq[i][1] - up_seq[i - 1][1]
        for i in range(1, len(up_seq))
    ]

    return np.array(dwell_times + dd_times + ud_times)  # shape: (31,)


def load_user_data(user_id):
    """读取指定用户的全部历史特征数据，返回 numpy 数组。"""
    file_path = os.path.join(DATA_DIR, f"{user_id}.csv")
    if not os.path.exists(file_path):
        return None
    return pd.read_csv(file_path, header=None).values  # shape: (n_samples, 31)


def build_template(user_id, k=1.7):
    """
    为指定用户构建身份模板：
    1. 读取该用户所有历史数据
    2. 用 StandardScaler 归一化（fit on 训练数据）
    3. 计算归一化后的均值向量作为"模板"
    4. 计算协方差矩阵的逆（用于马氏距离）
    5. 根据本人历史马氏距离分布计算自适应阈值：threshold = mean + k * std
    6. 将 scaler、template、cov_inv 和 threshold 保存到 models/ 目录

    """
    data = load_user_data(user_id)
    if data is None or len(data) < 32:
        return False, "数据量太少（马氏距离至少需要32条，建议50条以上）"

    scaler      = StandardScaler()
    scaled_data = scaler.fit_transform(data)
    template    = np.mean(scaled_data, axis=0)

    if len(scaled_data) > 31:
        cov_matrix = np.cov(scaled_data.T)
        cov_inv    = np.linalg.pinv(cov_matrix)
    else:
        cov_inv = np.eye(scaled_data.shape[1])

    distances = []
    for row in scaled_data:
        diff      = row - template
        dist      = float(np.sqrt(diff @ cov_inv @ diff))
        distances.append(dist)

    distances   = np.array(distances)
    dist_mean   = float(np.mean(distances))
    dist_std    = float(np.std(distances))
    threshold   = float(dist_mean + k * dist_std)

    with open(os.path.join(MODEL_DIR, f"{user_id}_scaler.pkl"),    'wb') as f:
        pickle.dump(scaler, f)
    with open(os.path.join(MODEL_DIR, f"{user_id}_template.pkl"),  'wb') as f:
        pickle.dump(template, f)
    with open(os.path.join(MODEL_DIR, f"{user_id}_cov_inv.pkl"),    'wb') as f:
        pickle.dump(cov_inv, f)
    with open(os.path.join(MODEL_DIR, f"{user_id}_threshold.pkl"), 'wb') as f:
        pickle.dump(threshold, f)

    print(f"[{user_id}] 距离均值={dist_mean:.3f}  标准差={dist_std:.3f}  阈值={threshold:.3f}")
    return True, f"成功（数据{len(data)}条，自适应阈值={threshold:.3f}）"


def build_all_templates():
    """遍历 data/ 目录，为所有用户重新生成模板，返回结果字典。"""
    results = {}
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".csv"):
            user_id = filename.replace(".csv", "")
            success, msg = build_template(user_id)
            results[user_id] = msg
            print(f"[build_template] {user_id}: {msg}")
    return results


def authenticate_user(user_id, feature_vector):
    """
    单用户异常检测（马氏距离版本）：
    1. 加载该用户的 scaler、template、cov_inv 和 personalized threshold
    2. 对新输入归一化
    3. 计算与模板的马氏距离
    4. 距离 < threshold 则通过，否则拒绝

    返回: (passed: bool | None, distance: float | str, threshold: float)
      - passed=None 表示发生错误，distance 为错误信息字符串
      - passed=True/False 时，distance 为 float 距离值，threshold 为该用户的专属阈值
    """
    scaler_path    = os.path.join(MODEL_DIR, f"{user_id}_scaler.pkl")
    template_path  = os.path.join(MODEL_DIR, f"{user_id}_template.pkl")
    cov_inv_path   = os.path.join(MODEL_DIR, f"{user_id}_cov_inv.pkl")
    threshold_path = os.path.join(MODEL_DIR, f"{user_id}_threshold.pkl")

    if not os.path.exists(scaler_path) or not os.path.exists(template_path) or not os.path.exists(cov_inv_path) or not os.path.exists(threshold_path):
        return None, "该用户尚未构建模板，请先采集数据并点击构建模板", None

    with open(scaler_path,    'rb') as f:
        scaler    = pickle.load(f)
    with open(template_path,  'rb') as f:
        template  = pickle.load(f)
    with open(cov_inv_path,   'rb') as f:
        cov_inv   = pickle.load(f)
    with open(threshold_path, 'rb') as f:
        threshold = pickle.load(f)

    new_vec_scaled = scaler.transform(feature_vector.reshape(1, -1))[0]
    diff           = new_vec_scaled - template
    distance       = float(np.sqrt(diff @ cov_inv @ diff))

    print(f"[auth] user={user_id}  distance={distance:.4f}  threshold={threshold:.4f}")

    passed = bool(distance < threshold)
    return passed, distance, threshold