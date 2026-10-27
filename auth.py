"""Fixed-text timing feature extraction and local demo templates."""
import pandas as pd
import numpy as np
import os
import pickle
import math
import re
from pathlib import Path
from sklearn.preprocessing import StandardScaler



TARGET     = "hello world"   # 目标字符串，与前端保持一致
TARGET_LEN = len(TARGET)     # 11

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
FEATURE_COUNT = TARGET_LEN * 3 - 2
_USER_ID = re.compile(r"[A-Za-z0-9_-]{1,64}", re.ASCII)
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
_SUFFIXES = {".csv", "_scaler.pkl", "_template.pkl", "_cov_inv.pkl", "_threshold.pkl"}


class InputError(ValueError):
    """Invalid input, safe to report without revealing local file paths."""


def validate_user_id(user_id):
    if (not isinstance(user_id, str) or not _USER_ID.fullmatch(user_id)
            or user_id.upper() in _RESERVED):
        raise InputError("user_id 只能包含 1–64 位英文字母、数字、下划线或短横线，且不能使用系统保留名称")
    return user_id


def safe_user_path(directory, user_id, suffix):
    validate_user_id(user_id)
    if suffix not in _SUFFIXES:
        raise InputError("文件类型不正确")
    root = Path(directory).resolve()
    candidate = root / (user_id + suffix)
    if candidate.is_symlink():
        raise InputError("不允许使用链接文件")
    resolved = candidate.resolve()
    if resolved.parent != root:
        raise InputError("文件位置不正确")
    return resolved
# ─────────────────────────────────────────────────────────────


def extract_features(events):
    """Validate the exact text and pair each release with its press.

    Different keys may overlap, including a negative up-to-next-down interval.
    """
    if not isinstance(events, list) or len(events) != TARGET_LEN * 2:
        return None
    down_times, up_times, pressed = [], [], {}
    previous = -1.0
    for event in events:
        if not isinstance(event, dict) or set(event) != {"key", "action", "timestamp"}:
            return None
        key, action, raw_time = event["key"], event["action"], event["timestamp"]
        if not isinstance(key, str) or len(key) != 1 or action not in ("down", "up"):
            return None
        if type(raw_time) not in (int, float):
            return None
        try:
            timestamp = float(raw_time)
        except (OverflowError, ValueError):
            return None
        if not math.isfinite(timestamp) or timestamp < 0 or timestamp < previous:
            return None
        previous = timestamp
        if action == "down":
            index = len(down_times)
            if index >= TARGET_LEN or key != TARGET[index] or key in pressed:
                return None
            pressed[key] = index
            down_times.append(timestamp)
            up_times.append(None)
        else:
            index = pressed.pop(key, None)
            if index is None or timestamp <= down_times[index]:
                return None
            up_times[index] = timestamp
    if pressed or len(down_times) != TARGET_LEN or any(t is None for t in up_times):
        return None
    with np.errstate(over="ignore", invalid="ignore"):
        down, up = np.asarray(down_times), np.asarray(up_times)
        features = np.concatenate((up - down, np.diff(down), down[1:] - up[:-1]))
    return features if np.isfinite(features).all() else None


def validate_feature_matrix(data):
    if (data.ndim != 2 or data.shape[1] != FEATURE_COUNT or not np.isfinite(data).all()
            or np.any(data[:, :TARGET_LEN] <= 0)
            or np.any(data[:, TARGET_LEN:2 * TARGET_LEN - 1] < 0)):
        raise InputError("样本数值或格式无效，请备份旧数据后重新采集")


def load_user_data(user_id):
    """读取指定用户的全部历史特征数据，返回 numpy 数组。"""
    file_path = safe_user_path(DATA_DIR, user_id, ".csv")
    if not os.path.exists(file_path):
        return None
    try:
        data = pd.read_csv(file_path, header=None, dtype=float).values
    except (OSError, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError):
        raise InputError("无法读取有效样本，请检查本地采集数据") from None
    validate_feature_matrix(data)
    return data


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
    validate_user_id(user_id)
    if type(k) not in (int, float) or not math.isfinite(k) or k <= 0:
        raise InputError("阈值参数无效")
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
        dist      = float(np.sqrt(max(float(diff @ cov_inv @ diff), 0)))
        distances.append(dist)

    distances   = np.array(distances)
    dist_mean   = float(np.mean(distances))
    dist_std    = float(np.std(distances))
    threshold   = float(dist_mean + k * dist_std)

    if not math.isfinite(threshold) or threshold <= 0:
        return False, "样本变化不足，无法建立有效阈值，请按自然节奏重新采集"
    paths = {name:safe_user_path(MODEL_DIR,user_id,f"_{name}.pkl")
             for name in ("scaler","template","cov_inv","threshold")}
    Path(MODEL_DIR).mkdir(parents=True, exist_ok=True)

    with open(paths['scaler'], 'wb') as f:
        pickle.dump(scaler, f)
    with open(paths['template'], 'wb') as f:
        pickle.dump(template, f)
    with open(paths['cov_inv'], 'wb') as f:
        pickle.dump(cov_inv, f)
    with open(paths['threshold'], 'wb') as f:
        pickle.dump(threshold, f)

    return True, f"成功（数据{len(data)}条，自适应阈值={threshold:.3f}）"


def build_all_templates():
    """遍历 data/ 目录，为所有用户重新生成模板，返回结果字典。"""
    results = {}
    for path in sorted(Path(DATA_DIR).glob('*.csv')):
        try:
            user_id = validate_user_id(path.stem)
            safe_user_path(DATA_DIR, user_id, '.csv')
        except InputError:
            continue
        try:
            success, msg = build_template(user_id)
            results[user_id] = msg
        except (ValueError, OverflowError, OSError, FloatingPointError, np.linalg.LinAlgError):
            results[user_id] = "构建失败，请检查本地样本或目录权限"
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
    validate_user_id(user_id)
    feature_vector = np.asarray(feature_vector, dtype=float)
    validate_feature_matrix(feature_vector.reshape(1, -1))
    scaler_path = safe_user_path(MODEL_DIR, user_id, '_scaler.pkl')
    template_path = safe_user_path(MODEL_DIR, user_id, '_template.pkl')
    cov_inv_path = safe_user_path(MODEL_DIR, user_id, '_cov_inv.pkl')
    threshold_path = safe_user_path(MODEL_DIR, user_id, '_threshold.pkl')

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

    if (not isinstance(template, np.ndarray) or template.shape != (FEATURE_COUNT,)
            or not isinstance(cov_inv, np.ndarray) or cov_inv.shape != (FEATURE_COUNT, FEATURE_COUNT)
            or not np.isfinite(template).all() or not np.isfinite(cov_inv).all()
            or type(threshold) not in (int, float) or not math.isfinite(threshold) or threshold <= 0):
        raise InputError("本地模板无效，请使用本机采集数据重新构建")

    new_vec_scaled = scaler.transform(feature_vector.reshape(1, -1))[0]
    diff           = new_vec_scaled - template
    distance       = float(np.sqrt(max(float(diff @ cov_inv @ diff), 0)))
    if not math.isfinite(distance):
        raise InputError("认证数值无效，请重新采集")

    passed = bool(distance < threshold)
    return passed, distance, threshold
