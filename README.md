# Keystroke Dynamics Authentication Demo

A Flask / NumPy coursework prototype for fixed-text timing features and local distance-based identity verification.

身份认证课程实验：浏览器采集 `hello world` 的真实按下 / 松开事件，服务器提取 31 维特征，用个人模板与马氏距离作演示判断。

## Run locally

Use Python 3.12 from the repository root:

```sh
python -m venv .venv
```

Activate with `.\.venv\Scripts\Activate.ps1` on Windows PowerShell, or `source .venv/bin/activate` on macOS / Linux. Then:

```sh
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. Select a demo user, type the fixed text naturally, release all keys, and collect at least **32 samples**; **50+** is recommended. Build the template before switching to authentication. Identical repeated samples cannot establish a usable threshold and are reported as insufficient variation.

The server binds to localhost with Flask debug mode disabled. Data and model folders are anchored to this project, not the shell's current working directory.

## Input and file boundaries

- User IDs accept 1–64 ASCII letters, digits, underscores or hyphens. Path syntax, whitespace, Windows reserved device names and other types are rejected.
- CSV and model paths are checked against their intended directory. Link files are rejected, including when listing users or building templates.
- Requests must be JSON objects containing exactly `user_id` and `events`; malformed data returns JSON errors. Request bodies are capped at 64 KiB.
- A sample has exactly 11 press and 11 release events. The press sequence must equal `hello world`, with finite nonnegative timestamps in event order.
- Every release must match its press and occur later. Different keys may overlap; a negative up-to-next-down interval can be valid. Repeated characters are paired separately.

These checks validate the event protocol; they do not prove a real person generated a submitted sample or prevent replay.

## Reproduce the checks

```sh
python -m unittest discover -s tests -v
```

The synthetic suite covers repeated letters, normal key rollover, wrong text order, malformed / nonfinite times, traversal identifiers, request size, linked files, corrupt CSVs and the collect → build → authenticate API flow. Temporary test state does not include real participant samples.

## Existing samples and templates

Back up your local CSVs and model files before updating. No script deletes or silently migrates them. Old CSV rows do not contain the original key-event sequence, so the new event validation cannot retrospectively prove old samples were valid. Recollect synthetic / consented samples and rebuild templates when evaluating the corrected feature extraction, especially if earlier samples used overlapping keys.

Model files remain local Python pickle files for compatibility. Only load templates you generated and control; do not accept downloaded or user-uploaded pickle models. Malformed local data is reported without exposing filesystem paths.

## Code map

- `index.html`: collection, reset, result and template-building feedback.
- `app.py`: bounded JSON input, collection / authentication / status endpoints.
- `auth.py`: shared identifier / path validation, event pairing, features and templates.
- `tests/`: synthetic feature, boundary and API regression tests.

## Limitations and provenance

This is coursework, not a production biometric authentication system. It does not establish population-level FAR / FRR, liveness, replay protection, robust rate limiting, encrypted templates or production authentication. Real participant CSVs and derived models are excluded and must not be published without an appropriate basis and consent.

AI tools assisted development and this fix. See [source history](docs/SOURCE_HISTORY.md) and [contribution guidance](CONTRIBUTING.md). Earlier snapshots preserve their original behavior; imported commits are not backdated.
