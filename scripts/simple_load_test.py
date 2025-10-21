#!/usr/bin/env python3
"""
Simple load tester (no external deps)

Usage examples:
  - GET root:
      python scripts/simple_load_test.py --url http://127.0.0.1:6030/ --total 300 --concurrency 60

  - POST dense search:
      python scripts/simple_load_test.py --url http://127.0.0.1:6030/search/dense \
        --method POST --data '{"query_text":"테스트","limit":3}' --total 50 --concurrency 10
"""

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--url', required=True, help='Target URL')
    p.add_argument('--method', default='GET', choices=['GET', 'POST'], help='HTTP method')
    p.add_argument('--data', default=None, help='JSON string for POST body')
    p.add_argument('--concurrency', type=int, default=10, help='Concurrent workers')
    p.add_argument('--total', type=int, default=100, help='Total requests')
    p.add_argument('--timeout', type=float, default=20.0, help='Per-request timeout seconds')
    return p.parse_args()


def main():
    args = parse_args()
    body = None
    headers = {'Connection': 'keep-alive'}
    if args.method == 'POST':
        headers['Content-Type'] = 'application/json'
        if args.data:
            body = args.data.encode('utf-8')

    latencies = []
    status = {}
    errors = 0
    start = time.monotonic()

    def one(_):
        t0 = time.monotonic()
        req = Request(args.url, data=body, headers=headers, method=args.method)
        try:
            with urlopen(req, timeout=args.timeout) as resp:
                _ = resp.read(0)
                code = resp.getcode()
        except HTTPError as e:
            code = e.code
        except URLError as e:
            return None, time.monotonic() - t0, f'URLError: {e.reason}'
        except Exception as e:
            return None, time.monotonic() - t0, f'Error: {e}'
        return code, time.monotonic() - t0, None

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = [ex.submit(one, i) for i in range(args.total)]
        for fut in as_completed(futs):
            code, lat, err = fut.result()
            if err:
                errors += 1
            else:
                latencies.append(lat)
                status[code] = status.get(code, 0) + 1

    dur = time.monotonic() - start
    ok = sum(v for k, v in status.items() if 200 <= k < 400)
    rps = ok / dur if dur > 0 else 0

    latencies.sort()
    print(f'Total {args.total}, Concurrency {args.concurrency}, Duration {dur:.3f}s, OK {ok}, Errors {errors}')
    print('Status:', status)
    if latencies:
        import statistics
        avg = statistics.mean(latencies)
        p50 = latencies[int(0.50 * len(latencies)) - 1]
        p90 = latencies[int(0.90 * len(latencies)) - 1]
        p95 = latencies[int(0.95 * len(latencies)) - 1]
        p99 = latencies[int(0.99 * len(latencies)) - 1]
        print(f'RPS: {rps:.1f}')
        print(f'Latency avg: {avg*1000:.1f} ms, p50: {p50*1000:.1f} ms, p90: {p90*1000:.1f} ms, p95: {p95*1000:.1f} ms, p99: {p99*1000:.1f} ms')


if __name__ == '__main__':
    main()

