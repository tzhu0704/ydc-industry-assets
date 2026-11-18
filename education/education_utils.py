"""Evidence checks for educational retrieval. No OCR or semantic entailment is claimed."""
import json
import re
from urllib.parse import urlparse


def normalize(text):
    return ' '.join(text.split())


def allowed_url(url, domains):
    parsed = urlparse(url)
    host = (parsed.hostname or '').lower()
    return parsed.scheme == 'https' and any(host == d or host.endswith('.' + d) for d in domains)


def evidence_from_hits(hits, domains):
    evidence = []
    for hit in hits:
        if not allowed_url(hit.get('url', ''), domains):
            continue
        hls = (hit.get('contents') or {}).get('highlights') or []
        text = '\n'.join(hls) if hls else hit.get('description', '')
        if len(normalize(text)) < 60:
            continue
        evidence.append(dict(id=f'S{len(evidence)+1}', url=hit['url'], title=hit.get('title',''), text=text))
    return evidence


def parse_json(text):
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())
    return json.loads(text)


def validate_lesson(result, evidence):
    errors = []
    sources = {s['id']: s for s in evidence}
    if not isinstance(result, dict):
        return ['response must be a JSON object']
    if not all(isinstance(result.get(k), str) and result[k].strip() for k in ('answer_en','answer_zh')):
        errors.append('both answer languages are required')
    claims = result.get('claims', [])
    if not isinstance(claims, list) or not claims:
        errors.append('at least one evidence-backed claim is required')
        return errors
    for claim in claims:
        if not isinstance(claim, dict):
            errors.append('claim must be an object'); continue
        src = sources.get(claim.get('source_id'))
        quote = claim.get('quote', '')
        if not src:
            errors.append('unknown source id')
        elif not isinstance(quote, str) or len(normalize(quote)) < 25 or normalize(quote) not in normalize(src['text']):
            errors.append('quote is missing, too short, or not present verbatim')
        if not all(isinstance(claim.get(k),str) and claim[k].strip() for k in ('explanation_en','explanation_zh')):
            errors.append('claim explanations must be bilingual')
    if not isinstance(result.get('gaps'), list):
        errors.append('gaps must be a list')
    return errors


def content_status(item, min_chars=300):
    """Application-level status, independent of HTTP success; threshold is a demo policy."""
    if not isinstance(item, dict):
        return 'invalid_item', ''
    if item.get('error') or item.get('status') in ('error','failed'):
        return 'provider_error', ''
    body = item.get('markdown') or (item.get('contents') or {}).get('markdown') or ''
    if not isinstance(body, str) or not body.strip():
        return 'empty_body', ''
    if len(normalize(body)) < min_chars:
        return 'short_body', body
    if re.search(r'access denied|verify you are human|enable javascript and cookies|just a moment', body[:600], re.I):
        return 'blocked_body', body
    return 'usable', body


def route_content(items, expected_urls, min_chars=300):
    """Match by URL, never by position; reject duplicates, missing entries and foreign URLs."""
    out=[]
    for url in expected_urls:
        matches=[i for i in items if isinstance(i,dict) and i.get('url') == url]
        if len(matches) != 1:
            out.append(dict(url=url, status='missing_item' if not matches else 'duplicate_item', chars=0))
            continue
        status, body=content_status(matches[0], min_chars)
        out.append(dict(url=url,status=status,chars=len(body)))
    return out


def math_check(coefficients, roots):
    a,b,c=coefficients
    if a == 0 or not isinstance(roots,list) or len(roots)!=2 or len(set(roots))!=2:
        return False
    return all(isinstance(x,(int,float)) and not isinstance(x,bool) and abs(a*x*x+b*x+c)<1e-9 for x in roots)


def textbook_excerpt(body, limit=60000):
    """Skip a pre-heading cookie/navigation preamble; preserve source wording after heading."""
    match=re.search(r'(?m)^# [^\n]+',body)
    start=match.start() if match else 0
    text=body[start:start+limit]
    return text, dict(raw_chars=len(body),skipped_preamble_chars=start,evidence_chars=len(text),truncated=start+len(text)<len(body))
