# ydc-industry-assets

Runnable, industry-specific examples of wiring You.com's search APIs (Web Search,
Contents, Knowledge, Highlights) into an LLM-based agent. Each example is a
real, reproducible scenario — not a hypothetical — with a working script you can
run against your own API key and model.

This repo is organized by industry vertical: `ecommerce/`, `legal/`, `travel/` and `media/` so far.

## Industry catalogue

| Industry | Folder | Scenarios | Capabilities used |
|---|---|---|---|
| Cross-border e-commerce | [`ecommerce/`](ecommerce) | 7 | Highlights, Knowledge, domain scoping, freshness, Contents, server-side search |
| Legal | [`legal/`](legal) | 3 | Highlights, domain scoping, freshness |
| Travel | [`travel/`](travel) | 7 | Knowledge, Highlights, domain scoping, freshness, country/language, People Search |
| Media creation | [`media/`](media) | 7 | Knowledge, Highlights, Contents, domain scoping, freshness, image / video / reverse-image search |

24 scenarios in total. Each industry folder is self-contained (its own `you_api.py` and `scenarios/`),
so you can copy one folder without the others. Capabilities are read from the scenario source, so the
table shows what a script calls, not how well it works.

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

travel/
  you_api.py           # same shared helpers + knowledge_records, people_search, save_sample
  scenarios/
    01_trip_briefing.py            # weather + FX via knowledge=core, recent notices via highlights
    02_entry_policy_watch.py       # official domains only, freshness=year, language=ZH-HANS
    03_multilingual_poi_check.py   # zh/en/ja, country+freshness on/off, measured (no judge model)
    04_supplier_due_diligence.py   # People Search (/v1/people/search) + Web Search corroboration
    05_itinerary_replan.py         # knowledge forecast + highlights indoor options -> re-ordered plan
    06_multicurrency_budget.py     # knowledge FX per currency; conversion done in code (fx.py)
    07_market_intelligence.py      # Trip.com vs Booking: knowledge financial/traffic + highlights news
  fx.py                # deterministic FX parsing/conversion used by 06
  tests/test_fx.py     # offline unit tests (no key): python3 -m unittest discover -s tests

media/
  you_api.py           # shared helpers + custom_search (image / video / reverse-image) and clean_serp
  media_utils.py       # pure helpers: stock detection, media-URL filters, number checks, shot-script validator
  scenarios/
    01_shot_script.py              # shot (camera-movement) script from live facts, validated in code
    02_trend_radar.py              # freshness=week + Contents; audio ids extracted by code
    03_data_card_script.py         # knowledge numbers; every number in the voice-over checked in code
    04_reference_image_search.py   # text -> image, measured (no model)
    05_reference_video_search.py   # text -> video, measured (no model)
    06_licensed_source_search.py   # include_domains on open-reuse sources + Contents(html); licence never inferred
    07_image_provenance.py         # reverse image search grouped by source; stock-site triage
  tests/test_media.py  # 13 offline unit tests (no key)
```

## Setup

You need a You.com API key (`YDC_API_KEY`). Get one at [you.com](https://you.com).

```bash
export YDC_API_KEY=your_key_here
cd travel      # or ecommerce / legal
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

## Scenario notes — travel

- **01 — Trip briefing**: three Web Search calls on one endpoint. Weather and the CNY/JPY rate
  come back as `knowledge=core` records (provider + `as_of`); recent notices use highlights with
  `country=JP` and `freshness=month`. Weather is returned in °F — convert in the prompt or in code.
- **02 — Entry-policy watch**: `include_domains` limited to Japanese government / tourism-board sites,
  `freshness=year`, `language=ZH-HANS`. The prompt requires a "not confirmed" list instead of
  filling gaps; the live run rejected two retrieved pages that were not about entering Japan.
- **03 — Multilingual check**: no model in the loop. Prints, per language, the share of results with a
  page date and within 30 days, with and without `country` + `freshness`. Note `freshness` drops results
  whose `page_age` is unknown.
- **04 — Supplier due diligence**: People Search is a standalone endpoint
  (`POST https://ydc-index.io/v1/people/search`, body `{"query", "count"}`). Profiles carry
  `authenticity_score`, `consistency_score`, `source_count`, `last_updated_at`; the prompt makes the
  model report them and list anything the web search did not corroborate. Person records are redacted
  (`redact_person`) before they are written to `samples/`; `*.json` is git-ignored, so samples are not
  committed. Do not log or publish person data.
- **05 — Itinerary re-plan**: forecast from `knowledge=core`, indoor options from highlights with
  `country=JP` + `freshness=month`. The prompt lets the model move existing items or add only items the
  retrieved text names, quoting prices/closing days verbatim — an early run cited a source that did not
  contain the item, and this rule fixed it.
- **06 — Multi-currency budget**: one `knowledge=core` FX call per currency; `fx.parse_rate` extracts the
  rate (rejecting the wrong direction / no rate) and the arithmetic is done in code. The model only
  summarises the finished table.
- **07 — Market intelligence**: financial (Fiscal.ai, S&P Global), traffic (Semrush) and news for two
  companies. The prompt forbids comparing figures that differ in period or currency, and requires
  "date not given" for records with no `as_of` (the Semrush traffic record has none).
- Not verified: `knowledge=core` did not return people records in our probes; use People Search directly.

## Scenario notes — media creation

- **01 — Shot script**: Knowledge supplies sunset time and forecast, Highlights supplies what is open or closed now,
  and a drone-rules search is limited to official domains. The model returns a JSON shot list; code checks the
  camera-move vocabulary, that durations sum to the target, that every cited source id exists, that a drone shot
  cites a drone-rules source, and that the shoot window equals the golden-hour window computed from the sourced
  sunset time. A failing script is sent back once. The checks are structural: they do not prove a source supports
  a sentence.
- **02 — Trend radar**: `freshness=week` plus Contents; Instagram Reels audio ids are counted by code. Third-party lists.
- **03 — Data card**: `knowledge=core` records; code checks every number in the voice-over/on-screen text appears in
  the records, and that on-screen numbers also appear as digits in the voice-over.
- **04 / 05 — Reference image / video**: `GET /v1/custom/s/search?engine=google_images|google_videos`. No model; the
  script measures on-topic (key-term proxy), direct image URLs, distinct sources/platforms and stock-site share.
- **06 — Licence-aware retrieval**: `include_domains` on open-reuse sources, Contents as HTML for complete media URLs.
  Licence is always reported "not determined": wiki pages carry boilerplate licence text about the page, not the image.
- **07 — Image provenance**: `engine=google_lens` visual matches grouped by source; a triage signal, not a licence
  decision. Hosts that block fetching (e.g. Wikimedia) return no matches; the script tries the next candidate.
- `save_sample` strips provider-internal fields from SERP responses. Not built: creator discovery with People Search
  (results mixed in companies and unrelated roles in our tests).
