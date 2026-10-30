"""Synthetic collect/build/auth evidence. Not a biometric accuracy benchmark."""
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import numpy as np
import auth
import app as web


def synthetic_events(seed, shifted=False):
    rng = np.random.default_rng(seed)
    result, timestamp = [], 0.0
    for key in auth.TARGET:
        hold = float(rng.uniform(95, 135) if shifted else rng.uniform(25, 65))
        interval = float(rng.uniform(230, 330) if shifted else rng.uniform(100, 180))
        result.extend([{"key": key, "action": "down", "timestamp": timestamp},
                       {"key": key, "action": "up", "timestamp": timestamp + hold}])
        timestamp += interval
    return result


def run_evidence():
    """Only generated timings enter a temporary directory, never project data/."""
    cases = []

    def record(name, expected, actual):
        cases.append({"scenario": name, "expected": expected, "actual": actual,
                      "passed": expected == actual})

    train_seeds = list(range(80))
    heldout_seeds = list(range(1000, 1020))
    shifted_seeds = list(range(2000, 2020))
    features = auth.extract_features(synthetic_events(0))
    record("feature_count", 31, len(features))
    record("feature_identity", True, bool(np.allclose(features[11:21] - features[21:], features[:10])))
    invalid = synthetic_events(0)
    invalid[0]["key"] = "x"
    record("wrong_text_rejected", True, auth.extract_features(invalid) is None)
    invalid = synthetic_events(0)
    invalid[0]["timestamp"] = float("nan")
    record("nonfinite_time_rejected", True, auth.extract_features(invalid) is None)
    rollover = synthetic_events(0)
    rollover[1]["timestamp"] = rollover[2]["timestamp"] + 10
    rollover.sort(key=lambda e: e["timestamp"])
    feature_rollover = auth.extract_features(rollover)
    record("valid_negative_up_down_interval", True,
           feature_rollover is not None and bool(feature_rollover[21] < 0))

    with tempfile.TemporaryDirectory(prefix="keystroke-showcase-") as td:
        root = Path(td)
        with patch.object(auth, "DATA_DIR", root / "data"), \
             patch.object(auth, "MODEL_DIR", root / "models"), \
             patch.object(web, "DATA_DIR", root / "data"):
            with web.app.test_client() as client:
                body = lambda events: {"user_id": "synthetic_demo", "events": events}
                missing = client.post("/auth", json=body(synthetic_events(999)))
                record("missing_template_http", 400, missing.status_code)
                for seed in train_seeds:
                    response = client.post("/collect", json=body(synthetic_events(seed)))
                    if response.status_code != 200:
                        raise RuntimeError("synthetic sample collection failed")
                record("collected_samples", 80, client.get("/status").json.get("synthetic_demo"))
                build = client.post("/build_templates")
                record("template_build", {"http": 200, "built": 1, "failed": 0},
                       {"http": build.status_code, "built": build.json.get("built"), "failed": build.json.get("failed")})

                def scores(seeds, shifted=False):
                    results = []
                    for seed in seeds:
                        response = client.post("/auth", json=body(synthetic_events(seed, shifted)))
                        if response.status_code != 200:
                            raise RuntimeError("synthetic authentication failed")
                        results.append({"seed": seed, **response.json})
                    return results

                heldout = scores(heldout_seeds)
                shifted = scores(shifted_seeds, True)
                record("finite_heldout_scores", True, all(np.isfinite(r["distance"]) and r["threshold"] > 0
                                                         for r in heldout + shifted))
                record("heldout_does_not_append_training_samples", 80,
                       client.get("/status").json.get("synthetic_demo"))
                forged = client.post("/collect", json={"user_id": "../escape", "events": synthetic_events(0)})
                record("path_traversal_http", 400, forged.status_code)
                matrix = np.asarray([auth.extract_features(synthetic_events(seed)) for seed in train_seeds])
                covariance_rank = int(np.linalg.matrix_rank(np.cov(matrix.T)))

    return {"schema_version": 1, "generated_at": datetime.now(timezone.utc).isoformat(),
            "dependencies": {name: version(name) for name in ("Flask", "numpy", "pandas", "scikit-learn")},
            "scope": "Generated timings, one synthetic template; NOT real-user FAR/FRR, EER or population accuracy.",
            "passed": all(c["passed"] for c in cases), "cases": cases,
            "target": auth.TARGET, "feature_count": 31,
            "feature_groups": {"hold": 11, "down_down": 10, "up_down": 10},
            "feature_dependency": "DD[i] - UD[i] = H[i] for i=0..9; covariance can be singular.",
            "synthetic_covariance_rank": covariance_rank,
            "split": {"train_seeds": train_seeds, "heldout_same_generator_seeds": heldout_seeds,
                      "heldout_shifted_generator_seeds": shifted_seeds},
            "heldout_same_generator": {"accepted": sum(r["passed"] for r in heldout),
                                       "total": len(heldout), "samples": heldout},
            "heldout_shifted_generator": {"accepted": sum(r["passed"] for r in shifted),
                                          "total": len(shifted), "samples": shifted},
            "note": "Acceptance counts are observations, not pass criteria. Changing synthetic distributions is not adding real impostors."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Output exists; use a new evidence filename")
    report = run_evidence()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"passed": report["passed"], "cases": len(report["cases"]),
                      "same_generator_accepted": report["heldout_same_generator"]["accepted"],
                      "shifted_generator_accepted": report["heldout_shifted_generator"]["accepted"]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
