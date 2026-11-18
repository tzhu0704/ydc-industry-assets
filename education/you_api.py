"""Standard-library API helpers for online-education examples.

Credentials come only from YDC_API_KEY. Samples exclude credentials and remain local.
Timeouts are per attempt, not an end-to-end SLA. There are at most two attempts,
with one-second backoff, only on transient HTTP/network failures.
"""
from __future__ import annotations
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SEARCH_URL='https://ydc-index.io/v1/search'
CONTENTS_URL='https://ydc-index.io/v1/contents'
CUSTOM_URL='https://ydc-index.io/v1/custom/s/search'
CHAT_URL='https://api.you.com/v1/chat/completions'
DEFAULT_MODEL=os.environ.get('YDC_EXAMPLE_MODEL','deepseek-v4.1-flash')


def _api_key():
    key=os.environ.get('YDC_API_KEY')
    if not key:
        raise RuntimeError('Set YDC_API_KEY in your environment.')
    return key


def _request(url, body=None, bearer=False, timeout=20):
    headers={'User-Agent':'curl/8.0'}
    headers['Authorization' if bearer else 'X-API-Key']=('Bearer ' if bearer else '')+_api_key()
    if body is not None:
        headers['Content-Type']='application/json'
    for attempt in range(2):
        req=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=timeout) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            # Invalid parameters and auth errors need fixes, not repeated requests.
            if exc.code not in (408,429,500,502,503,504) or attempt:
                raise
        except (TimeoutError,urllib.error.URLError):
            if attempt:
                raise
        time.sleep(1)


def web_search(query, extraction_mode=None, **params):
    body=dict(query=query,count=params.pop('count',10),**params)
    if extraction_mode:
        body['extraction']=dict(extraction_mode=extraction_mode)
    return _request(SEARCH_URL,body,timeout=20)


def web_search_hits(response):
    results=response.get('results',{})
    return results.get('web',[]) if isinstance(results,dict) else []


def contents(urls,formats=('markdown',)):
    return _request(CONTENTS_URL,dict(urls=urls,formats=list(formats)),timeout=25)


def chat(prompt, model=DEFAULT_MODEL):
    return _request(CHAT_URL,dict(model=model,messages=[dict(role='user',content=prompt)]),bearer=True,timeout=90)


def custom_search(engine, **params):
    url=CUSTOM_URL+'?'+urllib.parse.urlencode(dict(engine=engine,**params))
    return _request(url,timeout=25)


def clean_serp(obj):
    if isinstance(obj,dict):
        return {k:clean_serp(v) for k,v in obj.items() if k!='search_metadata' and 'serpapi' not in k.lower()
                and not (isinstance(v,str) and 'serpapi.com' in v)}
    if isinstance(obj,list):
        return [clean_serp(v) for v in obj]
    return obj


def save_sample(name,request,response):
    out=Path(__file__).resolve().parent/'samples'
    out.mkdir(exist_ok=True)
    (out/(name+'.json')).write_text(json.dumps(dict(request=request,response=clean_serp(response)),ensure_ascii=False,indent=2))
