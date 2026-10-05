# Keystroke Dynamics Authentication Demo

A Flask/NumPy coursework prototype exploring fixed-text timing features and distance-based identity verification.

身份认证课程实验：浏览器采集固定文本 `hello world` 的按键事件，Python 提取 31 维时序特征，标准化后通过马氏距离及个人阈值判断。

## Run locally

Python 3.12:

```sh
python -m venv .venv
# Activate .venv for your shell.
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Use a simple demo ID, collect your own samples, then build a template. The existing template builder needs at least 32 samples (50+ recommended). Real participant CSVs and derived pickle templates are excluded; they must not be published without an appropriate basis and consent.

## Inspect

- `index.html`: collection and verification UI.
- `app.py`: collection, authentication and template endpoints.
- `auth.py`: feature extraction, normalization, covariance and distance threshold.

## Limitations

This prototype is not a production biometric authentication system. No representative population evaluation, liveness/replay protection, robust rate limiting or template encryption is claimed. Only load model pickle files you generated locally. The initial coursework feature extraction and endpoint input handling require review before any wider use; imported snapshots retain the original implementation for transparency.

## Development and provenance

This is an educational project developed with AI assistance. See [source history](docs/SOURCE_HISTORY.md) for the original records and local version snapshots. Imported commits are not backdated. Follow [CONTRIBUTING](CONTRIBUTING.md) for future changes.

本项目用于课程学习与求职作品展示，开发和本次仓库整理使用了 AI 辅助。可运行代码与验证记录不等于所有代码均由本人独立手写，也不代表生产系统经验。历史说明中的本机路径与旧验收记录仅供追溯。
