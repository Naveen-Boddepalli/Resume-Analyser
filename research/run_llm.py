"""B5 and the LLM part of E6: zero-shot LLM fit judgement and counterfactual audit.

Budget (calls to ``mistral-small-latest``, temperature 0), approved by the user:

* 250 stratified test pairs                              -> baseline  (250)
* 36 of those pairs x 10 demographic name cells          -> names     (360)
* 36 pairs x 8 proxy/control lines                       -> proxies   (288)
* 30 repeated control calls                              -> run-to-run noise (30)
                                                              total   928

Responses are cached in ``research/cache/llm_calls.jsonl`` keyed by the hash of
(model, prompt), so interrupted runs resume without paying twice.

    .venv/bin/python -I research/run_llm.py baseline
    .venv/bin/python -I research/run_llm.py audit
"""

from __future__ import annotations

import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I does not add the script dir

import numpy as np
import pandas as pd
import requests
from common import CACHE, ROOT, SEED, load_data, save_json
from dotenv import dotenv_values

from resumatch.fairness import NAMES, PROXIES, with_line, with_name

MODEL = "mistral-small-latest"
CACHE_FILE = CACHE / "llm_calls.jsonl"
LABEL_NAMES = {"no fit": 0, "potential fit": 1, "good fit": 2}
_lock = threading.Lock()
_next_slot = [0.0]
MIN_INTERVAL = 0.35  # seconds between request starts (global)

PROMPT = """You are an experienced recruiter screening one candidate for one job.
Read the resume and the job description and judge how well the candidate fits the job.

Answer with a JSON object only, with exactly these keys:
  "fit":   one of "No Fit", "Potential Fit", "Good Fit"
  "score": integer 0-100 (0 = clearly unsuitable, 100 = ideal match)

RESUME:
{resume}

JOB DESCRIPTION:
{jd}
"""


def _env() -> tuple[str, str]:
    cfg = dotenv_values(ROOT / "backend" / ".env")
    return cfg["MISTRAL_API_KEY"] or "", cfg.get("MISTRAL_API_URL") or "https://api.mistral.ai/v1/chat/completions"


def _load_cache() -> dict[str, dict]:
    store: dict[str, dict] = {}
    if CACHE_FILE.exists():
        for line in CACHE_FILE.read_text().splitlines():
            rec = json.loads(line)
            store[rec["key"]] = rec
    return store


_CACHE = _load_cache()


def call_llm(resume: str, jd: str, tag: str = "") -> dict:
    prompt = PROMPT.format(resume=resume[:7000], jd=jd[:5000])
    key = hashlib.sha256((MODEL + "|" + tag + "|" + prompt).encode()).hexdigest()
    with _lock:
        if key in _CACHE:
            return _CACHE[key]
    api_key, url = _env()
    payload = {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": 60,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
    }
    err = ""
    for attempt in range(6):
        with _lock:
            now = time.time()
            start = max(now, _next_slot[0])
            _next_slot[0] = start + MIN_INTERVAL
        if start > now:
            time.sleep(start - now)
        try:
            r = requests.post(url, json=payload, headers={"Authorization": f"Bearer {api_key}"}, timeout=60)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2**attempt)
                continue
            r.raise_for_status()
            body = r.json()
            text = body["choices"][0]["message"]["content"]
            parsed = json.loads(text)
            fit = LABEL_NAMES.get(str(parsed.get("fit", "")).strip().lower(), -1)
            rec = {
                "key": key,
                "fit": fit,
                "score": float(parsed.get("score", np.nan)),
                "model": body.get("model", MODEL),
                "prompt_tokens": body.get("usage", {}).get("prompt_tokens"),
            }
            with _lock:
                _CACHE[key] = rec
                CACHE.mkdir(parents=True, exist_ok=True)
                with open(CACHE_FILE, "a") as fh:
                    fh.write(json.dumps(rec) + "\n")
            return rec
        except Exception as exc:  # noqa: BLE001 - network/parse errors are retried then recorded
            err = str(exc)[:120]
            time.sleep(2**attempt)
    return {"key": key, "fit": -1, "score": float("nan"), "model": MODEL, "error": err}


def run_many(jobs: list[tuple[str, str, str]], workers: int = 4) -> list[dict]:
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda a: call_llm(*a), jobs))


def stratified_sample(test: pd.DataFrame, n: int) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    parts = []
    for y, g in test.groupby("y"):
        k = int(round(n * len(g) / len(test)))
        parts.append(g.iloc[rng.choice(len(g), size=min(k, len(g)), replace=False)])
    return pd.concat(parts).sample(frac=1, random_state=SEED).reset_index(drop=True)


def baseline(test: pd.DataFrame) -> pd.DataFrame:
    sub = stratified_sample(test, 250)
    res = run_many([(r.resume_text, r.job_description_text, "") for r in sub.itertuples()])
    sub["llm_fit"] = [r["fit"] for r in res]
    sub["llm_score"] = [r["score"] for r in res]
    return sub


def main(mode: str) -> None:
    _, test = load_data()
    t0 = time.time()
    sub = baseline(test)
    ok = sub["llm_fit"] >= 0
    print(f"baseline: {int(ok.sum())}/{len(sub)} parsed in {time.time() - t0:.0f}s", flush=True)
    sub.drop(columns=["resume_text", "job_description_text"]).to_csv(
        CACHE.parent / "results" / "llm_baseline_predictions.csv", index=False
    )
    if mode == "baseline":
        return

    audit = sub.iloc[:36].reset_index(drop=True)
    jobs: list[tuple[str, str, str]] = []
    index: list[tuple[str, int]] = []
    for cell, names in NAMES.items():
        for i, r in enumerate(audit.itertuples()):
            jobs.append((with_name(r.resume_text, names[0]), r.job_description_text, ""))
            index.append((f"names:{cell}", i))
    for family, lines in PROXIES.items():
        for key, line in lines.items():
            for i, r in enumerate(audit.itertuples()):
                jobs.append((with_line(r.resume_text, line), r.job_description_text, ""))
                index.append((f"{family}:{key}", i))
    # run-to-run noise: repeat the original text with a different cache tag
    for i, r in enumerate(audit.iloc[:30].itertuples()):
        jobs.append((r.resume_text, r.job_description_text, "repeat"))
        index.append(("repeat", i))
    print(f"audit: {len(jobs)} calls", flush=True)
    res = run_many(jobs)
    table = pd.DataFrame(
        {
            "condition": [c for c, _ in index],
            "i": [i for _, i in index],
            "fit": [r["fit"] for r in res],
            "score": [r["score"] for r in res],
        }
    )
    table.to_csv(CACHE.parent / "results" / "llm_audit_raw.csv", index=False)
    payload = {"model_requested": MODEL, "n_pairs": int(len(audit)), "n_calls": int(len(jobs))}
    save_json("llm_audit_meta.json", payload)
    print(f"audit done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "baseline")
