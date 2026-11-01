"""Scenario 2 — Shopping assistant (server-side harness mode)

The model decides when to search, server-side — one request, one response, with
the live web search folded in automatically.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat_with_search

QUERY = "What are the best noise-cancelling headphones under $300 based on this month's reviews?"


def main() -> None:
    print(f"Query: {QUERY}\n", file=sys.stderr)
    result = chat_with_search(QUERY)

    with open("scenario2_result.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(result["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
