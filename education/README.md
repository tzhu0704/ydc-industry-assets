# Online education: retrieval for learning agents

Six reproducible workflows, using public textbook and science sources. Run from this folder:

```bash
# Supply your key through the environment; do not paste it into code or samples.
python3 scenarios/01_grounded_math.py
python3 scenarios/02_concept_correction.py
python3 scenarios/03_fulltext_lesson.py
python3 scenarios/04_bilingual_learning.py
python3 scenarios/05_learning_diagrams.py
python3 scenarios/06_resilient_reading.py
python3 -m unittest discover -s tests
```

Set `YDC_API_KEY` beforehand. Only the Python standard library is needed. `YDC_EXAMPLE_MODEL` can override the default Inference Router model. A model call is separate from search and incurs its own usage.

| Workflow | Input | You.com APIs | Application output / checks |
|---|---|---|---|
| 01 | Typed quadratic exercise | Web Search + Highlights on OpenStax | Bilingual hints and solution; code independently checks the supplied roots by substitution |
| 02 | Free-fall misconception | Web Search + Highlights on OpenStax | Contrast ideal free fall with air resistance; quoted evidence |
| 03 | Photosynthesis mini-lesson | Search, then Contents | Full-text-backed explanation and comprehension checks |
| 04 | Why seasons change | EN and ZH-HANT searches on NASA / a public science museum | Bilingual glossary and explanation; original-language quotes |
| 05 | Water-cycle diagram query | Image search | Candidates from science agencies with source pages; teacher review before use |
| 06 | Scientific hypothesis vs theory | Search, Contents, usable-body gate | Per-URL body checks, alternate URL or excerpt-only fallback; offline injected failures separately labeled |

The input exercise in 01 is authored for this demo, not an exact match found online. OCR, image understanding and handwriting recognition must be supplied by the host learning app; no such capability is tested here. Roots are checked independently of the model's wording; read the solution before reuse.

For model scenarios, `run.py` saves every successful API request and response, the full prompt, evidence, output and validation attempts in `samples/`. These JSON files are gitignored. Failures stop the run rather than fabricating a successful sample. Quotes are checked verbatim with whitespace normalization, and citations must point to supplied sources. These checks do **not** prove semantic entailment, full citation coverage, pedagogical quality or learning gains.

Contents is checked per URL: missing or duplicate entries, provider errors, empty/short bodies and obvious challenge pages do not qualify as usable full text. The 300-character gate is a demo policy, not an API guarantee; a long irrelevant page may still pass. The harness tries up to three allowed source URLs, then explicitly labels an excerpt-only lesson. Scenario 06 injects empty, short and missing fixture entries offline; it does not claim the live provider failed. It does not stress-test regions, large PDFs or SLA behavior.

Image search returns candidates; this example neither inspects diagram labels nor establishes licensing. Knowledge and People Search are not required for these workflows. The retrieval task is finding instructional evidence, rather than discovering student profiles.

Sources are public pages. No learner records, credentials, customer names or internal performance reports are included. API schemas and public data can change; rerun with your own evaluation set.
