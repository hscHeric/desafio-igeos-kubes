#!/usr/bin/env python3
"""Small dependency-free load test for the producer endpoint."""

from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median
from sys import argv
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json


base_url = argv[1] if len(argv) > 1 else "http://localhost:8080"
total = int(argv[2]) if len(argv) > 2 else 40
workers = int(argv[3]) if len(argv) > 3 else 4


def publish(index):
    payload = json.dumps({"text": f"load-test-{index}"}).encode()
    request = Request(
        f"{base_url}/api/producer/messages",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = perf_counter()
    try:
        with urlopen(request, timeout=15) as response:
            response.read()
            return response.status, perf_counter() - started, ""
    except (HTTPError, URLError, TimeoutError, OSError) as error:
        return getattr(error, "code", 0), perf_counter() - started, type(error).__name__


started = perf_counter()
with ThreadPoolExecutor(max_workers=workers) as pool:
    results = list(pool.map(publish, range(total)))
elapsed = perf_counter() - started
latencies = sorted(result[1] for result in results)
successes = sum(result[0] == 202 for result in results)
failures = total - successes
p95 = latencies[max(0, int(len(latencies) * 0.95) - 1)]

print(f"requests={total} workers={workers} successes={successes} failures={failures}")
print(f"elapsed_seconds={elapsed:.3f} throughput_requests_per_second={total / elapsed:.2f}")
print(f"latency_seconds_mean={mean(latencies):.3f} median={median(latencies):.3f} p95={p95:.3f} max={max(latencies):.3f}")

if failures:
    for status, _, error in results:
        if status != 202:
            print(f"failure_status={status} error={error}")
    raise SystemExit(1)
