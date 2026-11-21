"""Run the fictional study or rebuild its results from recorded API responses."""
import argparse
from datetime import datetime, timezone
from fcntl import LOCK_EX, LOCK_NB, flock
from hashlib import sha256
import json
from math import comb, sqrt
from pathlib import Path
import random
from time import sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .design import CASES, CONDITIONS, MONITOR, breach, prompt, scenario, verdict

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PRICING = json.loads((ROOT / "experiment/prices.json").read_text())
RATES = PRICING["rates_per_million"]
MODELS = tuple(RATES)
CAP = 2.50
SAMPLES = 3
MAX_REPLY = 64
MAX_VERDICT = 12


def save(path, value):
    scratch = path.with_suffix(".tmp")
    scratch.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    scratch.replace(path)


def usd(model, usage):
    rate = RATES[model]
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    return (
        (usage["prompt_tokens"] - cached) * rate["input"]
        + cached * rate["cached"]
        + usage["completion_tokens"] * rate["output"]
    ) / 1_000_000


def reserve(model, messages, maximum):
    # UTF-8 bytes conservatively bound text tokens. Allow extra chat framing.
    input_limit = sum(len(msg["content"].encode()) + 32 for msg in messages) + 64
    return usd(model, {"prompt_tokens": input_limit, "completion_tokens": maximum})


def msg(role, content):
    return {"role": role, "content": content}


def monitor_messages(system, history):
    return [msg("system", MONITOR), msg("user", json.dumps({
        "house_rule": system, "conversation": history[1:],
    }, ensure_ascii=False))]


def budget_estimate():
    total = 0
    for model in MODELS:
        for index in range(len(CASES)):
            system, turns, _ = scenario(index)
            for condition in CONDITIONS:
                history = [msg("system", system)]
                indices = [len(turns) - 1] if condition == "D" else range(len(turns))
                for turn in indices:
                    history.append(msg("user", prompt(index, condition, turn)))
                    total += reserve(model, history, MAX_REPLY)
                    # This estimate assumes three UTF-8 bytes per generated token.
                    history.append(msg("assistant", " " * (3 * MAX_REPLY)))
                if condition in ("B", "C"):
                    total += reserve(model, monitor_messages(system, history), MAX_VERDICT)
    return total * SAMPLES


class Cache:
    def __init__(self, live):
        self.live = live
        self.data = {}
        self.spend = 0.0
        self.estimated = budget_estimate()
        for path in sorted((RESULTS / "raw").glob("*.jsonl")):
            for line in path.read_text().splitlines():
                row = json.loads(line)
                if row["key"] in self.data:
                    raise ValueError(f"Duplicate cache key {row['key']}")
                self.data[row["key"]] = row
                self.spend += usd(row["response"]["model"], row["response"]["usage"])

    def chat(self, model, index, condition, sample, step, messages, maximum):
        key = f"{model}/{index+1:02}/{condition}/{sample+1}/{step}"
        payload = {
            "model": model, "messages": messages, "temperature": 0.7,
            "max_completion_tokens": maximum,
            "seed": 222200 + index * 10 + sample,
        }
        if model.startswith("gpt-5.4"):
            payload["reasoning_effort"] = "none"
            # The GPT-5.4 chat endpoint does not guarantee seed support.
            del payload["seed"]
        if step == "monitor":
            payload["temperature"] = 0
        body = json.dumps(payload, sort_keys=True).encode()
        digest = sha256(body).hexdigest()
        if key in self.data:
            row = self.data[key]
            if row["request_sha256"] != digest:
                raise ValueError(f"Request changed for cached call {key}")
        else:
            if not self.live:
                raise ValueError(f"Missing recorded call {key}")
            if self.spend + reserve(model, messages, maximum) > CAP:
                raise RuntimeError("Stopping before the next call would exceed the $2.50 budget")
            response = call(body)
            row = {
                "key": key, "request_sha256": digest,
                "recorded_utc": datetime.now(timezone.utc).isoformat(),
                "response": response,
            }
            path = RESULTS / "raw" / f"{model}.jsonl"
            with path.open("a") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                f.flush()
            self.data[key] = row
            self.spend += usd(response["model"], response["usage"])
        return row["response"]["choices"][0]["message"]["content"] or ""

    def save_spend(self):
        save(ROOT / "spend.json", {
            **PRICING, "estimated_usd": round(self.estimated, 8), "cap_usd": CAP,
            "spend_usd": round(sum(
                usd(x["response"]["model"], x["response"]["usage"])
                for x in self.data.values()
            ), 8),
            "calls": len(self.data),
        })


def call(body):
    import os

    request = Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"],
                 "Content-Type": "application/json"},
    )
    for attempt in range(2):
        try:
            with urlopen(request, timeout=45) as response:
                return json.load(response)
        except HTTPError as error:
            detail = json.load(error).get("error", {})
            if error.code == 429 and detail.get("code") == "rate_limit_exceeded" and not attempt:
                sleep(5)
                continue
            raise RuntimeError(
                f"OpenAI HTTP {error.code}, type={detail.get('type')}, "
                f"code={detail.get('code')}, parameter={detail.get('param')}"
            ) from None


def trial(cache, model, index, condition, sample):
    system, turns, marker = scenario(index)
    history = [msg("system", system)]
    indices = [len(turns) - 1] if condition == "D" else range(len(turns))
    for turn in indices:
        history.append(msg("user", prompt(index, condition, turn)))
        reply = cache.chat(model, index, condition, sample, turn + 1, history, MAX_REPLY)
        history.append(msg("assistant", reply))
    caught = None
    if condition in ("B", "C"):
        caught = verdict(cache.chat(model, index, condition, sample, "monitor",
                                    monitor_messages(system, history), MAX_VERDICT))
    return {
        "model": model, "sequence": index + 1, "condition": condition,
        "sample": sample + 1, "marker": marker,
        "breach": breach([x["content"] for x in history if x["role"] == "assistant"], marker),
        "caught": caught, "messages": history[1:],
    }


def proportion(count, total):
    p = count / total
    z2 = 1.95996398454 ** 2
    center = (p + z2 / (2 * total)) / (1 + z2 / total)
    margin = sqrt(z2 * (p * (1 - p) + z2 / (4 * total)) / total) / (1 + z2 / total)
    return {"count": count, "n": total, "rate": p,
            "ci": [max(0, center - margin), min(1, center + margin)]}


def paired(trials):
    deltas = []
    for index in range(1, len(CASES) + 1):
        rates = {}
        for condition in ("B", "C"):
            group = [t for t in trials if t["sequence"] == index and t["condition"] == condition]
            rates[condition] = sum(t["breach"] for t in group)
        deltas.append(rates["C"] - rates["B"])
    wins = sum(d > 0 for d in deltas)
    losses = sum(d < 0 for d in deltas)
    n = wins + losses
    p = min(1, 2 * sum(comb(n, k) for k in range(min(wins, losses) + 1)) / 2**n)
    reps = len(trials) // (len(CASES) * len(CONDITIONS))
    return {
        "difference": sum(deltas) / (len(CASES) * reps), "p": p,
        "days_higher": wins, "minutes_higher": losses, "ties": len(CASES) - n,
        "by_sequence": [
            {"sequence": index, "difference": delta / reps}
            for index, delta in enumerate(deltas, start=1)
        ],
    }


def summarize(trials, cache):
    groups = {}
    for name in ["All models", *MODELS]:
        group = [x for x in trials if x["model"] == name or name == "All models"]
        conditions = {}
        for condition, label in CONDITIONS.items():
            subset = [x for x in group if x["condition"] == condition]
            result = {"label": label, "breach": proportion(sum(t["breach"] for t in subset), len(subset))}
            if condition in ("B", "C"):
                result["monitor"] = proportion(sum(t["caught"] is True for t in subset), len(subset))
                result["monitor"]["unparsed"] = sum(t["caught"] is None for t in subset)
            conditions[condition] = result
        groups[name] = {"conditions": conditions, "paired": paired(group)}
    # Preselect the first sequence and sample on both models regardless of outcome.
    example = [t for t in trials if t["sequence"] == 1 and t["sample"] == 1
               and t["condition"] in ("B", "C")]
    recorded = sorted(row["recorded_utc"] for row in cache.data.values())
    return {
        "title": "Slow Burn", "n": len(trials), "sequences": len(CASES),
        "samples": SAMPLES, "models": MODELS, "date": recorded[0][:10],
        "end_date": recorded[-1][:10], "temperature": 0.7,
        "spend_usd": round(cache.spend, 8), "groups": groups, "example": example,
    }


def run(args):
    cache = Cache(args.live)
    print(f"Projected estimate: ${cache.estimated:.4f}. Cap: ${CAP:.2f}. Cached calls: {len(cache.data)}.")
    if cache.estimated > CAP and args.live:
        raise RuntimeError("Estimate exceeds the budget")
    trials = []
    try:
        for index in range(len(CASES)):
            order = [(model, condition, sample) for model in MODELS
                     for condition in CONDITIONS for sample in range(SAMPLES)]
            random.Random(2222 + index).shuffle(order)
            for model, condition, sample in order:
                trials.append(trial(cache, model, index, condition, sample))
            if args.live:
                print(f"Sequence {index+1}/{len(CASES)} complete. Accrued: ${cache.spend:.4f}.")
        if args.audit:
            for index in range(len(CASES)):
                # One fixed transcript per sequence, balanced across conditions and models.
                model = MODELS[(index // 4) % len(MODELS)]
                condition = tuple(CONDITIONS)[index % 4]
                selected = next(t for t in trials if t["sequence"] == index + 1
                                and t["model"] == model and t["condition"] == condition
                                and t["sample"] == index % SAMPLES + 1)
                print(json.dumps(selected, ensure_ascii=False))
        else:
            summary = summarize(trials, cache)
            save(RESULTS / "summary.json", summary)
            print(f"{len(trials)} transcripts. Token-based spend: ${cache.spend:.8f}.")
    finally:
        if args.live or not args.audit:
            cache.save_spend()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--estimate", action="store_true")
    mode.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if args.estimate:
        print(f"Projected token spend: ${budget_estimate():.4f}. Cap: ${CAP:.2f}.")
        return
    with (RESULTS / ".live.lock").open("a") as lock:
        try:
            flock(lock, LOCK_EX | LOCK_NB)
        except BlockingIOError:
            parser.exit(1, "Another run is using this study cache.\n")
        run(args)


if __name__ == "__main__":
    main()
