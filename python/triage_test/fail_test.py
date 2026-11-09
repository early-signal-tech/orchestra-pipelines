"""Triage test task

Run by the "Triage Test Pipeline" Orchestra pipeline as task `fail_test`, via:

    project_dir: python/triage_test
    command:     python fail_test.py

It fails on purpose so the "Triage Example" auto-heal pipeline (triggered on any
FAILED pipeline) can be exercised end to end. FAIL_MODE picks the failure:

  bug        -> a genuine code bug (KeyError from a typo). Expected verdict: FIX.
                This is the only mode an agent should change code for.
  transient  -> a simulated upstream timeout that fails ~50% of the time.
                Expected verdict: RETRY. Intentional - do not "fix".
  auth       -> a simulated expired API credential. Expected verdict: ESCALATE.
                Intentional - do not "fix"; a human must rotate the credential.
  none       -> succeeds.

Standard library only; contacts no external system and writes no data.
"""

import os
import random
import sys

ORDERS = [
    {"order_id": 1, "amount": 10.0},
    {"order_id": 2, "amount": 25.5},
    {"order_id": 3, "amount": 4.5},
]


def total_order_amount(orders):
    return sum(order["amount"] for order in orders)


def main():
    mode = os.environ.get("FAIL_MODE", "bug")
    print(f"triage test: FAIL_MODE={mode}")

    if mode == "bug":
        print(f"total order amount: {total_order_amount(ORDERS)}")
    elif mode == "transient":
        if random.random() < 0.5:
            sys.exit("ConnectionError: read timed out after 30s calling orders API (HTTP 503 Service Unavailable)")
        print("orders API responded; nothing to do")
    elif mode == "auth":
        sys.exit("AuthenticationError: API token for service 'billing-api' has expired or been revoked (HTTP 401)")
    elif mode == "none":
        print("no failure requested")
    else:
        sys.exit(f"Unknown FAIL_MODE '{mode}' - expected bug, transient, auth or none")


if __name__ == "__main__":
    main()
