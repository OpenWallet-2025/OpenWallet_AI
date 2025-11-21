# version 0.1.1
# 작성일: 2025-11-20
# Open Wallet - Trend Summary
# GPU 아키텍처 자동 감지 및 CPU 폴백 추가 버전

from __future__ import annotations
import argparse, hashlib, json, os, re, sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import feedparser, requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

@dataclass
class Article:
    url: str
    title: str
    source: str
    published_at: Optional[str]
    content: str

@dataclass
class TrendSummary:
    period_start: str
    period_end: str
    keywords: List[str]
    bullets: List[str]
    key_stats: List[str]
    risks: List[str]
    opportunities: List[str]
    sources: List[str]
    model: str
    raw_response: dict

def iso_now() -> str: return datetime.now(timezone.utc).isoformat()
def to_date_iso(dt: datetime) -> str: return dt.date().isoformat()
def clamp_len(text: str, max_chars: int = 20000) -> str: return text if len(text) <= max_chars else text[:max_chars]

# 데베 일단 SQLite로 만들었습니다.
SCHEMA_SQL = """CREATE TABLE IF NOT EXISTS articles(
id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE, title TEXT, source TEXT,
published_at TEXT, content TEXT, inserted_at TEXT);
CREATE TABLE IF NOT EXISTS summaries(
id INTEGER PRIMARY KEY AUTOINCREMENT, period_start TEXT, period_end TEXT, keywords TEXT,
bullets TEXT, key_stats TEXT, risks TEXT, opportunities TEXT, sources TEXT,
model TEXT, raw_response TEXT, created_at TEXT);"""

def init_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA_SQL)
    return conn

def upsert_article(conn, a: Article):
    conn.execute(
        """INSERT INTO articles(url,title,source,published_at,content,inserted_at)
           VALUES(?,?,?,?,?,?)
           ON CONFLICT(url) DO UPDATE SET
             title=excluded.title, source=excluded.source,
             published_at=excluded.published_at, content=excluded.content""",
        (a.url, a.title, a.source, a.published_at, a.content, iso_now())
    )

def insert_summary(conn, s: TrendSummary):
    conn.execute(
        """INSERT INTO summaries(period_start,period_end,keywords,bullets,key_stats,risks,
                                 opportunities,sources,model,raw_response,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (
            s.period_start, s.period_end,
            json.dumps(s.keywords, ensure_ascii=False),
            json.dumps(s.bullets, ensure_ascii=False),
            json.dumps(s.key_stats, ensure_ascii=False),
            json.dumps(s.risks, ensure_ascii=False),
            json.dumps(s.opportunities, ensure_ascii=False),
            json.dumps(s.sources, ensure_ascii=False),
            s.model, json.dumps(s.raw_response, ensure_ascii=False),
            iso_now()
        )
    )

# 뉴스 수집: Google News RSS
def google_news_rss_url(q, lang='ko', region='KR'):
    return f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl={lang}&gl={region}&ceid={region}:{lang}"

def collect_articles(keywords, days, max_articles):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out: List[Article] = []
    headers = {'User-Agent': 'Mozilla/5.0 (OpenWallet-TrendSummary)'}
    for kw in keywords:
        feed = feedparser.parse(google_news_rss_url(kw))
        for e in getattr(feed, 'entries', []):
            link = getattr(e, 'link', None)
            if not link:
                continue
            pub = getattr(e, 'published', None)
            pub_iso = None
            if pub:
                try:
                    dt = dateparser.parse(pub)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if dt < cutoff:
                        continue
                    pub_iso = dt.astimezone(timezone.utc).isoformat()
                except Exception:
                    pass
            try:
                r = requests.get(link, headers=headers, timeout=10)
                soup = BeautifulSoup(r.text, 'html.parser')
                text = ' '.join([p.get_text(' ', strip=True) for p in soup.find_all('p')])
                text = re.sub(r'\s+', ' ', text)
                if len(text) < 200:
                    continue
                out.append(Article(
                    url=link,
                    title=getattr(e, 'title', ''),
                    source=getattr(e, 'source', 'Google News'),
                    published_at=pub_iso,
                    content=clamp_len(text, 25000)
                ))
                if len(out) >= max_articles:
                    return out
            except Exception:
                continue
    return out

# 카나나 요약
def summarize_with_kanana(arts, model='kakaocorp/kanana-1.5-2.1b-instruct-2505'):
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    # RTX 50-시리즈 이상인지 감지하는 코드
    def pick_device_and_dtype():
        if torch.cuda.is_available():
            try:
                major, minor = torch.cuda.get_device_capability(0)
                print(f"[trend_summary] CUDA available. Capability: ({major},{minor}), Device: {torch.cuda.get_device_name(0)}")
                return "cuda", (torch.bfloat16 if major >= 10 else torch.float16)
            except Exception as e:
                print("[trend_summary] GPU detection failed:", e)
        print("[trend_summary] Falling back to CPU.")
        return "cpu", torch.float32

    device, dtype = pick_device_and_dtype()

    # Tokenizer / Model
    tok = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
    m = AutoModelForCausalLM.from_pretrained(
        model,
        dtype=dtype,                 # torch_dtype -> dtype (신규 arg)
        device_map="auto",           # 자동 배치 (GPU/CPU)
        trust_remote_code=True
    )

    # 기사 합본 (안전 여유 두고 자르기)
    joined = '\n\n'.join([f"# {a.title}\n{a.content}" for a in arts])
    # 모델/토크나이저에서 최대 길이 추정 후 0.9 여유
    max_ctx = getattr(m.config, "max_position_embeddings",
                      getattr(tok, "model_max_length", 32768))
    joined = joined[: int(max_ctx * 0.9)]

    # Chat template 
    messages = [
        {"role": "system", "content": "너는 한국어 경제/리테일/소비 트렌드 애널리스트다."},
        {"role": "user", "content":
            "다음 기사 모음을 JSON으로 요약하라. 키: bullets, key_stats, risks, opportunities\n" + joined}
    ]
    prompt_ids = tok.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(device)

    # 종료 토큰 탐색 (없으면 eos 사용)
    eot_id = None
    for tkn in ("<|eot_id|>", "<|eot|>"):
        try:
            tid = tok.convert_tokens_to_ids(tkn)
            if tid is not None and tid != tok.unk_token_id:
                eot_id = tid
                break
        except Exception:
            pass
    eos_id = eot_id if eot_id is not None else tok.eos_token_id

    gen_kwargs = dict(
        max_new_tokens=700,
        do_sample=False,
        eos_token_id=eos_id,
        pad_token_id=tok.eos_token_id
    )

    with torch.inference_mode():
        out = m.generate(prompt_ids, **gen_kwargs)

    txt = tok.decode(out[0], skip_special_tokens=True)


    js = {"bullets": [], "key_stats": [], "risks": [], "opportunities": []}
    mobj = re.search(r'\{[\s\S]*\}', txt)
    if mobj:
        try:
            js = json.loads(mobj.group(0))
        except Exception:
            pass

    end = to_date_iso(datetime.now(timezone.utc))
    start = to_date_iso(datetime.now(timezone.utc) - timedelta(days=7))
    return TrendSummary(
        start, end, [], js.get('bullets', []), js.get('key_stats', []),
        js.get('risks', []), js.get('opportunities', []),
        [a.url for a in arts], model, js
    )

# 런런런
def run(db, keywords, days, max_articles, model):
    c = init_db(db)
    arts = collect_articles(keywords, days, max_articles)
    for a in arts:
        upsert_article(c, a)
    s = summarize_with_kanana(arts, model)
    s.keywords = keywords
    insert_summary(c, s)
    c.commit()
    c.close()
    return s

# CLI
if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--keywords', required=True)
    p.add_argument('--days', type=int, default=7)
    p.add_argument('--max-articles', type=int, default=30)
    p.add_argument('--db', default='./openwallet_trends.db')
    p.add_argument('--model', default='kakaocorp/kanana-1.5-2.1b-instruct-2505')
    a = p.parse_args()

    s = run(a.db, [k.strip() for k in a.keywords.split(',') if k.strip()],
            a.days, a.max_articles, a.model)

    print(f"\n 기간: {s.period_start} ~ {s.period_end}\n")
    for b in s.bullets:
        print(" -", b)