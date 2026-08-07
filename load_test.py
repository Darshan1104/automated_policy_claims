"""
Simple concurrent load test for the deployed /adjudicate endpoint.

This is what produces the p95 latency / throughput / cost numbers
for the resume -- not a demo, an actual measurement against the
deployed container.

Usage:
    python load_test.py --url https://<your-deployed-url>/adjudicate --requests 60 --concurrency 10

Install (not needed for the main app, just this script):
    pip install aiohttp
"""

import argparse
import asyncio
import statistics
import time

import aiohttp

SAMPLE_CLAIMS = [
    "A pipe burst in my kitchen and flooded the floor, causing $3,200 in damage to cabinets.",
    "My car was stolen from a parking garage on March 3rd, no witnesses.",
    "Water damage to my basement after heavy rain overwhelmed the sump pump.",
    "A tree fell on my roof during a storm, damaging shingles and a skylight.",
    "My laptop was stolen from my house during a break-in on June 14th.",
]


async def send_one(session, url, claim, results, errors):
    start = time.monotonic()
    try:
        async with session.post(
            url, json={"claim": claim}, timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            await resp.json()
            elapsed_ms = (time.monotonic() - start) * 1000
            if resp.status == 200:
                results.append(elapsed_ms)
            else:
                errors.append(f"HTTP {resp.status}")
    except Exception as e:
        errors.append(str(e))


async def run_load_test(url, total_requests, concurrency):
    results, errors = [], []
    sem = asyncio.Semaphore(concurrency)

    async def bound_send(claim, session):
        async with sem:
            await send_one(session, url, claim, results, errors)

    async with aiohttp.ClientSession() as session:
        tasks = [
            bound_send(SAMPLE_CLAIMS[i % len(SAMPLE_CLAIMS)], session)
            for i in range(total_requests)
        ]
        wall_start = time.monotonic()
        await asyncio.gather(*tasks)
        wall_elapsed = time.monotonic() - wall_start

    print("\n--- Load test results ---")
    print(f"Target:           {url}")
    print(f"Total requests:   {total_requests}")
    print(f"Concurrency:      {concurrency}")
    print(f"Successful:       {len(results)}")
    print(f"Errors:           {len(errors)}")
    print(f"Wall time:        {wall_elapsed:.2f}s")

    if results:
        print(f"Throughput:       {len(results) / wall_elapsed:.2f} req/s")
        results.sort()
        p50 = statistics.median(results)
        p95_index = max(0, int(len(results) * 0.95) - 1)
        p95 = results[p95_index]
        print(f"Latency p50:      {p50:.0f} ms")
        print(f"Latency p95:      {p95:.0f} ms")
        print(f"Latency min/max:  {min(results):.0f} / {max(results):.0f} ms")

    if errors:
        print(f"Sample errors:    {errors[:5]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Full URL to the /adjudicate endpoint")
    parser.add_argument("--requests", type=int, default=60)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()

    asyncio.run(run_load_test(args.url, args.requests, args.concurrency))