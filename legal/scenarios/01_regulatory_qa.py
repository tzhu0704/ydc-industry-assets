"""Scenario 1 — Regulatory Q&A (client-side harness mode)

A lawyer asks a question about current law; the answer needs to be grounded in the
official text itself, not a summary blog post, with each claim traceable to the
specific article/section it comes from.

Domain-scoping to the regulator's own site (`eur-lex.europa.eu`, `europa.eu`) plus
highlights mode is what makes this usable: the model gets the actual legal text,
not a secondhand paraphrase.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from you_api import chat, web_search, web_search_hits

QUERY = "EU AI Act duties for general-purpose AI model providers"
OFFICIAL_DOMAINS = ["eur-lex.europa.eu", "europa.eu"]

PROMPT_TEMPLATE = """You are a legal research assistant for a law firm. A lawyer asked:
"{query}"

Answer using ONLY the official text below, citing each passage with its source URL so the
lawyer can verify it. If a passage is truncated and you cannot confirm what follows, say so
rather than completing it from general knowledge.

{context}
"""


def build_context(hits: list[dict]) -> str:
    blocks = []
    for i, hit in enumerate(hits[:5], 1):
        title = hit.get("title", "")
        url = hit.get("url", "")
        highlights = hit.get("contents", {}).get("highlights", [])
        text = " ".join(highlights[:2]) if highlights else hit.get("description", "")
        blocks.append(f"[{i}] {title} — {url}\n{text[:500]}")
    return "\n\n".join(blocks)


def main() -> None:
    print(f"Query: {QUERY}", file=sys.stderr)
    print(f"Domain scope: {OFFICIAL_DOMAINS}\n", file=sys.stderr)

    search_result = web_search(
        QUERY, extraction_mode="highlights", include_domains=OFFICIAL_DOMAINS, count=5
    )
    hits = web_search_hits(search_result)
    print(f"{len(hits)} hits", file=sys.stderr)

    prompt = PROMPT_TEMPLATE.format(query=QUERY, context=build_context(hits))
    answer = chat(prompt)

    with open("scenario1_search_result.json", "w") as f:
        json.dump(search_result, f, indent=2, ensure_ascii=False)
    with open("scenario1_answer.json", "w") as f:
        json.dump(answer, f, indent=2, ensure_ascii=False)

    print(answer["choices"][0]["message"]["content"])


if __name__ == "__main__":
    main()
