# ydc-industry-assets

Runnable, industry-specific examples of wiring You.com's search APIs (Web Search,
Contents, Knowledge, Highlights) into an LLM-based agent. Each example is a
real, reproducible scenario — not a hypothetical — with a working script you can
run against your own API key and model.

This repo is organized by industry vertical: `ecommerce/` and `legal/` so far.

## Structure

```
ecommerce/
  you_api.py           # shared helpers: web_search, contents, chat, chat_with_search
  scenarios/
    01_sourcing_agent.py                    # supplier discovery + live FX landed-cost math
    02_shopping_assistant.py                # freshness-aware product recommendations
    03_trend_watch.py                       # multi-source trend/competitor-price synthesis
    04_supplier_risk_screening.py           # domain-scoped compliance/risk screening
    05_competitor_platform_intelligence.py  # knowledge + highlights in one call
    06_multiplatform_listing_check.py       # where to list a product, and at what price
    07_import_tariff_compliance.py          # HS code / tariff lookup, government sources only

legal/
  you_api.py           # same shared helpers, copied so each vertical stays self-contained
  scenarios/
    01_regulatory_qa.py          # cited answers grounded in official regulatory text
    02_court_and_rule_watch.py   # a weekly brief that flags stale items instead of trusting dates
    03_multi_country_check.py    # one comparison table across jurisdictions, gaps flagged not guessed
```

## Setup

You need a You.com API key (`YDC_API_KEY`). Get one at [you.com](https://you.com).

```bash
export YDC_API_KEY=your_key_here
cd ecommerce   # or legal
python3 scenarios/01_sourcing_agent.py
```

No third-party packages required — everything runs on the Python standard library.

### Which model do these scripts call?

By default, these scripts call You.com's Inference Router (`api.you.com`), which
proxies a number of open-weight models behind an OpenAI-compatible interface — so
the examples run with just a `YDC_API_KEY`, no separate model API key needed.

The scripts are not tied to any specific model. Set `YDC_EXAMPLE_MODEL` to try a
different one available through the router, or edit `you_api.py`'s `chat()` /
`chat_with_search()` to point at your own model provider directly — every scenario
script only depends on getting back an OpenAI-compatible `choices[0].message.content`
response.

## Two harness patterns

**Server-side** — pass a `web_search` tool in the chat request; the model decides
when to search, one round trip (`ecommerce/scenarios/02`, part of `05`).

```python
chat_with_search("What are the best noise-cancelling headphones under $300...")
```

**Client-side** — call Web Search / Contents yourself, assemble results into the
prompt, call the model separately. Full control over parameters: domain scoping,
freshness windows, extraction mode. Used by every other scenario in this repo.

```python
results = web_search(query, extraction_mode="highlights", include_domains=[...])
answer = chat(build_prompt(results))
```

## A gotcha worth knowing

`api.you.com` sits behind Cloudflare, which rejects Python's default
`urllib`/`requests` User-Agent with a `403 error code: 1010`. This is **not a rate
limit** — retrying with the same default UA keeps failing. `you_api.py` already
sets a normal-looking User-Agent on every request to avoid this; if you port this
code elsewhere, keep that header.

## Scenario notes — e-commerce

- **01 — Sourcing agent**: two Web Search calls (supplier discovery via highlights,
  live FX rate via `knowledge=core`), combined into one landed-cost-aware answer.
- **02 — Shopping assistant**: server-side search, freshness-aware retrieval.
- **03 — Trend watch**: Search → Contents → synthesis, the same pipeline pattern
  used for multi-source competitor/category monitoring.
- **04 — Supplier risk screening**: uses a fictional company name — no real
  customer data. Domain-scoped retrieval (`include_domains`) + highlights is what
  makes the screening result usable rather than just "inconclusive."
- **05 — Competitor platform intelligence**: `knowledge` and `highlights` enabled
  together in a single call — a structured financial record plus the specific news
  passages behind it, synthesized into one strategic brief.
- **06 — Multi-platform listing check**: a different question from 05 — not "how
  healthy is this named competitor" but "where should I list this product and at
  what price," compared across marketplaces in one search.
- **07 — Import tariff / HS code compliance**: domain-scoped to government trade
  sites only (`cbp.gov`, `usitc.gov`, `trade.gov`) so the answer is grounded in
  actual rulings and bulletins, not SEO content — and the prompt explicitly asks
  the model to flag what the sources don't confirm rather than fill gaps with a
  guess.

## Scenario notes — legal

- **01 — Regulatory Q&A**: domain-scoped to the regulator's own site
  (`eur-lex.europa.eu`, `europa.eu`) plus highlights, so the model answers from the
  actual legal text instead of a secondhand summary — and is told to flag truncated
  passages rather than complete them from general knowledge.
- **02 — Court & rule watch**: domain-scoped to legal-news aggregators (Lexology,
  National Law Review, JD Supra). Even scoped, search results mix genuinely recent
  items with older background articles — the prompt asks the model to check each
  source's own publish date and flag anything that isn't actually new, rather than
  presenting a stale article as this week's development.
- **03 — Multi-country check**: one search per jurisdiction, combined into a single
  comparison table. The model is asked to flag — not paper over — jurisdictions
  where the provided sources don't support a confident answer.
