"""
CodeLens async endpoint load test.

Simulates N concurrent users submitting code reviews through the async task
queue (POST /api/review/async) and polling for results (GET /api/tasks/{id}).

Usage:
    # default: 50 concurrent users against local stack
    python backend/scripts/load_test.py

    # custom concurrency and base URL
    python backend/scripts/load_test.py --n 20 --url http://localhost:8000

    # against a remote host
    python backend/scripts/load_test.py --n 100 --url https://your-api.example.com

Requirements (already in requirements.txt):
    httpx
    asyncio (stdlib)

The script registers a fresh test user so it can be run repeatedly without
manual setup. The test account is named load_test_<timestamp>@codelens.test.
"""

import argparse
import asyncio
import random
import string
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

# ── Configurable constants ────────────────────────────────────

DEFAULT_URL = "http://localhost:8000"
DEFAULT_N = 50
POLL_INTERVAL = 0.5      # seconds between status polls
POLL_TIMEOUT = 120.0     # give up on a task after this many seconds
MAX_CONNECTIONS = 100    # httpx connection pool limit

# ── Code snippet templates ─────────────────────────────────────
# Each request gets a unique snippet so cache misses are guaranteed,
# which means the Celery worker actually runs the LLM for each task.
# A random suffix is appended to every snippet to break SHA-256 equality.

_SNIPPET_TEMPLATES = [
    # security: eval
    """\
def process_input(user_data):
    result = eval(user_data)
    return result

def main():
    data = input("Enter expression: ")
    output = process_input(data)
    print(output)
""",
    # security: SQL injection
    """\
import sqlite3

def get_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()
""",
    # bug: bare except + == None
    """\
def fetch_data(url):
    try:
        import requests
        response = requests.get(url)
        data = response.json()
    except:
        data = None

    if data == None:
        return {}
    return data
""",
    # performance: wildcard import + long line
    """\
from os import *
from sys import *

def process_files(directory):
    results = []
    for filename in listdir(directory):
        full_path = path.join(directory, filename)
        if path.isfile(full_path) and path.getsize(full_path) > 0 and path.splitext(filename)[1] in [".txt", ".csv", ".json", ".xml", ".yaml", ".log"]:
            results.append(full_path)
    return results
""",
    # security: os.system + subprocess shell=True
    """\
import os
import subprocess

def run_command(user_input):
    os.system("echo " + user_input)
    result = subprocess.run("ls " + user_input, shell=True, capture_output=True)
    return result.stdout.decode()
""",
    # style: TODO markers + no docstrings
    """\
class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.cache = {}
        # TODO: add validation

    def process(self, items):
        # FIXME: this is slow for large inputs
        results = []
        for item in items:
            if item not in self.cache:
                self.cache[item] = self._transform(item)
            results.append(self.cache[item])
        return results

    def _transform(self, item):
        # HACK: temporary workaround
        return str(item).upper()
""",
    # mixed: nested ifs + repeated code
    """\
def calculate_discount(user, cart):
    if user is not None:
        if user.get("is_member"):
            if cart.get("total") > 100:
                if cart.get("item_count") > 5:
                    discount = cart["total"] * 0.20
                    cart["final"] = cart["total"] - discount
                    return cart["final"]
                else:
                    discount = cart["total"] * 0.10
                    cart["final"] = cart["total"] - discount
                    return cart["final"]
            else:
                discount = cart["total"] * 0.05
                cart["final"] = cart["total"] - discount
                return cart["final"]
    return cart.get("total", 0)
""",
    # security: hardcoded password
    """\
import requests

API_KEY = "sk-prod-abc123secretkey"
DB_PASSWORD = "admin1234"
BASE_URL = "https://api.example.com"

def authenticate():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(
        f"{BASE_URL}/auth",
        headers=headers,
        json={"db_pass": DB_PASSWORD},
    )
    return response.json()
""",
]


def _unique_snippet(index: int) -> str:
    """Return a snippet that is guaranteed unique (different SHA-256) per request."""
    template = _SNIPPET_TEMPLATES[index % len(_SNIPPET_TEMPLATES)]
    # Append a unique comment so the SHA-256 cache key is never reused
    salt = "".join(random.choices(string.ascii_lowercase, k=8))
    return template + f"\n# load_test uid={index} salt={salt}\n"


# ── Result tracking ───────────────────────────────────────────

@dataclass
class TaskResult:
    request_index: int
    task_id: Optional[str] = None
    submit_error: Optional[str] = None
    submit_ms: float = 0.0          # time to get 202 back
    total_ms: float = 0.0           # submit + all polls until complete
    status: str = "unknown"         # complete / failed / timeout / error
    poll_count: int = 0


# ── Core logic ────────────────────────────────────────────────

async def register_and_login(client: httpx.AsyncClient, base_url: str) -> str:
    """Register a fresh test user and return a JWT token."""
    ts = int(time.time())
    email = f"load_test_{ts}@codelens.test"
    password = "LoadTest!99"
    username = f"load_{ts}"

    reg = await client.post(
        f"{base_url}/api/auth/register",
        json={"email": email, "password": password, "username": username},
    )
    if reg.status_code not in (200, 201):
        raise RuntimeError(f"Registration failed {reg.status_code}: {reg.text}")

    login = await client.post(
        f"{base_url}/api/auth/login",
        json={"email": email, "password": password},
    )
    if login.status_code != 200:
        raise RuntimeError(f"Login failed {login.status_code}: {login.text}")

    token = login.json().get("access_token")
    if not token:
        raise RuntimeError(f"No access_token in login response: {login.text}")
    return token


async def run_single(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    index: int,
) -> TaskResult:
    """Submit one review task and poll until complete. Returns a TaskResult."""
    result = TaskResult(request_index=index)
    headers = {"Authorization": f"Bearer {token}"}
    code = _unique_snippet(index)

    # ── Submit ──
    t0 = time.perf_counter()
    try:
        resp = await client.post(
            f"{base_url}/api/review/async",
            json={"code": code, "language": "python"},
            headers=headers,
        )
        result.submit_ms = (time.perf_counter() - t0) * 1000

        if resp.status_code != 202:
            result.submit_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
            result.status = "error"
            result.total_ms = result.submit_ms
            return result

        result.task_id = resp.json().get("task_id")
    except Exception as exc:
        result.submit_error = str(exc)
        result.status = "error"
        result.total_ms = (time.perf_counter() - t0) * 1000
        return result

    # ── Poll ──
    deadline = time.perf_counter() + POLL_TIMEOUT
    while time.perf_counter() < deadline:
        await asyncio.sleep(POLL_INTERVAL)
        result.poll_count += 1
        try:
            poll = await client.get(
                f"{base_url}/api/tasks/{result.task_id}",
                headers=headers,
            )
            if poll.status_code != 200:
                continue
            data = poll.json()
            state = data.get("status", "")
            if state == "complete":
                result.status = "complete"
                break
            if state == "failed":
                result.status = "failed"
                break
            # pending / processing → keep polling
        except Exception:
            pass  # transient network error — keep polling

    else:
        result.status = "timeout"

    result.total_ms = (time.perf_counter() - t0) * 1000
    return result


async def run_load_test(base_url: str, n: int) -> None:
    limits = httpx.Limits(max_connections=MAX_CONNECTIONS, max_keepalive_connections=MAX_CONNECTIONS)
    timeout = httpx.Timeout(30.0, connect=10.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        # ── Auth ──
        print(f"Registering test user at {base_url} …")
        try:
            token = await register_and_login(client, base_url)
        except RuntimeError as exc:
            print(f"  FATAL: {exc}")
            return
        print(f"  OK — token acquired\n")

        # ── Fire N concurrent tasks ──
        print(f"Firing {n} concurrent requests to POST /api/review/async …")
        wall_start = time.perf_counter()
        tasks = [run_single(client, base_url, token, i) for i in range(n)]
        results: list[TaskResult] = await asyncio.gather(*tasks)
        wall_elapsed = time.perf_counter() - wall_start

    # ── Report ──
    completed  = [r for r in results if r.status == "complete"]
    failed     = [r for r in results if r.status == "failed"]
    timed_out  = [r for r in results if r.status == "timeout"]
    errored    = [r for r in results if r.status == "error"]

    total_ms_values = [r.total_ms for r in completed]
    submit_ms_values = [r.submit_ms for r in results if r.submit_error is None]

    avg_total   = sum(total_ms_values) / len(total_ms_values) if total_ms_values else 0
    min_total   = min(total_ms_values) if total_ms_values else 0
    max_total   = max(total_ms_values) if total_ms_values else 0
    avg_submit  = sum(submit_ms_values) / len(submit_ms_values) if submit_ms_values else 0
    avg_polls   = sum(r.poll_count for r in completed) / len(completed) if completed else 0
    success_pct = len(completed) / n * 100

    print("\n" + "=" * 60)
    print("  LOAD TEST RESULTS")
    print("=" * 60)
    print(f"  Concurrency         : {n} users")
    print(f"  Wall-clock time     : {wall_elapsed:.2f}s")
    print()
    print(f"  Completed           : {len(completed):>4} / {n}  ({success_pct:.1f}%)")
    print(f"  Failed              : {len(failed):>4}")
    print(f"  Timed out           : {len(timed_out):>4}  (>{POLL_TIMEOUT:.0f}s)")
    print(f"  Submit errors       : {len(errored):>4}")
    print()
    print(f"  Submit latency (202): avg {avg_submit:.0f}ms")
    print(f"  Total task time     : avg {avg_total/1000:.2f}s  "
          f"min {min_total/1000:.2f}s  max {max_total/1000:.2f}s")
    print(f"  Avg polls per task  : {avg_polls:.1f}  (interval={POLL_INTERVAL}s)")
    print("=" * 60)

    if errored:
        print("\nSubmit errors (first 5):")
        for r in errored[:5]:
            print(f"  [{r.request_index}] {r.submit_error}")

    if failed:
        print(f"\nFailed tasks (first 5 task IDs):")
        for r in failed[:5]:
            print(f"  [{r.request_index}] task_id={r.task_id}")

    if timed_out:
        print(f"\nTimed-out tasks (first 5 task IDs):")
        for r in timed_out[:5]:
            print(f"  [{r.request_index}] task_id={r.task_id}")


# ── Entry point ───────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CodeLens async endpoint load test",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--n", type=int, default=DEFAULT_N,
                        help="Number of concurrent users / requests")
    parser.add_argument("--url", default=DEFAULT_URL,
                        help="Base URL of the CodeLens API (no trailing slash)")
    args = parser.parse_args()

    asyncio.run(run_load_test(base_url=args.url.rstrip("/"), n=args.n))


if __name__ == "__main__":
    main()
