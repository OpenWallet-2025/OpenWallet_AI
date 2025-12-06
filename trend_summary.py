# trend_summary.py
# 2025-12-06
from __future__ import annotations
import argparse, json, re, time
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


def to_date_iso(dt: datetime) -> str:
    return dt.date().isoformat()

def clamp_len(text: str, max_chars: int = 20000) -> str:
    return text if len(text) <= max_chars else text[:max_chars]


def google_news_rss_url(q, lang="ko", region="KR"):
    return (
        f"https://news.google.com/rss/search?"
        f"q={requests.utils.quote(q)}&hl={lang}&gl={region}&ceid={region}:{lang}"
    )

def _safe_get(url: str, headers: dict, timeout: int = 10) -> Optional[str]:
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code >= 400:
            return None
        return r.text
    except Exception:
        return None

def collect_articles(keywords: List[str], days: int, max_articles: int) -> List[Article]:
    """
    - Google News RSS에서 기사 수집
    - pub_date 기준으로 최근 N일 + year == 2025 인 기사만 사용
    - 본문 길이 필터를 완화해서 '짧은 기사'도 최대한 받아들임
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out: List[Article] = []
    headers = {"User-Agent": "Mozilla/5.0 (OpenWallet-TrendSummary)"}

    MIN_CHARS = 10  

    print(f"[collect_articles] START keywords={keywords}, days={days}, cutoff={cutoff.isoformat()}")

    for kw in keywords:
        print(f"[collect_articles] ---- keyword='{kw}' ----")
        feed_url = google_news_rss_url(kw)
        print(f"[collect_articles] feed_url={feed_url}")

        feed = feedparser.parse(feed_url)
        entries = getattr(feed, "entries", [])
        print(f"[collect_articles] RSS entries={len(entries)}")

        for e in entries:
            link = getattr(e, "link", None)
            if not link:
                continue

            print(f"  [entry] fetch {link}")

            # 날짜 파싱
            pub = getattr(e, "published", None)
            pub_iso = None
            if pub:
                try:
                    dt = dateparser.parse(pub)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    # 2025년 기사만
                    if dt.year != 2025:
                        print(f"    -> year={dt.year}, not 2025, skip")
                        continue
                    if dt < cutoff:
                        print("    -> older than cutoff, skip")
                        continue
                    pub_iso = dt.astimezone(timezone.utc).isoformat()
                except Exception as ex:
                    print("    -> date parse error:", ex)
                    # 연도 모르면 2025 필터 못 거니까 그냥 skip
                    continue
            else:
                print("    -> no published date, skip")
                continue

            # ---- HTML 요청 ----
            html = _safe_get(link, headers=headers, timeout=10)
            if not html:
                print("    -> fetch failed, skip")
                continue

            try:
                soup = BeautifulSoup(html, "html.parser")

                # 1) <p> 텍스트 우선
                p_nodes = soup.find_all("p")
                p_text = " ".join(p.get_text(" ", strip=True) for p in p_nodes)
                p_text = re.sub(r"\s+", " ", p_text).strip()

                # 2) <p>가 너무 짧으면 전체 텍스트 fallback
                if len(p_text) >= MIN_CHARS:
                    text = p_text
                    print(f"    -> use p-text len={len(p_text)}")
                else:
                    full_text = soup.get_text(" ", strip=True)
                    full_text = re.sub(r"\s+", " ", full_text).strip()
                    print(
                        f"    -> p-text too short ({len(p_text)} chars), "
                        f"fallback full-text len={len(full_text)}"
                    )
                    text = full_text

                # 최종 길이 체크 (정말 1~2자짜리 쓰레기만 버림)
                if len(text) < MIN_CHARS:
                    print(f"    -> still too short (<{MIN_CHARS} chars), skip")
                    continue

                text = clamp_len(text, 25000)

                out.append(
                    Article(
                        url=link,
                        title=getattr(e, "title", "") or "",
                        source=(getattr(e, "source", None) or "Google News"),
                        published_at=pub_iso,
                        content=text,
                    )
                )
                print(f"    -> collected (len={len(text)} chars) total={len(out)}")

                if len(out) >= max_articles:
                    print(f"[collect_articles] reached max_articles={max_articles}, stop.")
                    return out

            except Exception as ex:
                print("    -> parse error:", ex)
                continue

        # soft rate-limit
        time.sleep(0.2)

    print(f"[collect_articles] FINAL collected={len(out)}")
    return out

def _safe_parse_to_json(txt: str):
    """모델이 JSON을 안 지켜도 최대한 구조화해서 반환."""
    # 코드블록/롤 태그 제거
    txt2 = re.sub(r"```[\s\S]*?```", "", txt, flags=re.MULTILINE)
    txt2 = re.sub(r"\b(system|user|assistant)\b\s*", "", txt2)
    
    m = re.search(r"\{[\s\S]*\}", txt2)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    
    def grab(section):
        pat = rf"{section}\s*[:：]\s*([\s\S]*?)(?:\n\s*\w+\s*[:：]|\Z)"
        mm = re.search(pat, txt2, flags=re.IGNORECASE)
        if not mm:
            return []
        block = mm.group(1)
        items = re.findall(r"^\s*[-*•]\s*(.+)$", block, flags=re.MULTILINE)
        if not items:
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            items = lines[:6]
        return [re.sub(r"\s+", " ", it).strip() for it in items if it.strip()]

    js = {
        "bullets": grab("bullets"),
        "key_stats": grab("key_stats"),
        "risks": grab("risks"),
        "opportunities": grab("opportunities"),
    }
    if any(js[k] for k in js):
        return js
    return {"bullets": [], "key_stats": [], "risks": [], "opportunities": []}


# Summarization (Kanana)

def _pick_device_and_dtype():
    """
    sm_120 (RTX 50xx) → 현재 안정판 PyTorch에 커널 미매칭 가능.
    가능하면 GPU(bfloat16/float16), 런타임 CUDA 에러 발생 시 CPU 폴백.
    """
    try:
        import torch

        if torch.cuda.is_available():
            try:
                major, minor = torch.cuda.get_device_capability(0)
                name = torch.cuda.get_device_name(0)
                print(f"[trend_summary] CUDA available. Capability: ({major},{minor}), Device: {name}")
                # Ampere+는 bfloat16 권장
                dtype = torch.bfloat16 if major >= 8 else torch.float16
                return "cuda", dtype
            except Exception as e:
                print("[trend_summary] GPU detection failed:", e)
        print("[trend_summary] Falling back to CPU.")
        return "cpu", None
    except Exception as e:
        print("[trend_summary] Torch import failed, forcing CPU.", e)
        return "cpu", None

def summarize_with_kanana(
    arts: List[Article],
    model: str = "kakaocorp/kanana-1.5-2.1b-instruct-2505",
) -> TrendSummary:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    device, dtype = _pick_device_and_dtype()

    tok = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
    # pad/eos 안전 설정
    if tok.pad_token_id is None and tok.eos_token_id is not None:
        tok.pad_token = tok.eos_token

    # 모델 로드
    model_kwargs = dict(trust_remote_code=True, device_map="auto")
    if device == "cuda":
        model_kwargs["torch_dtype"] = dtype or torch.bfloat16
    m = AutoModelForCausalLM.from_pretrained(model, **model_kwargs)

    # 기사 합본
    joined = "\n\n".join([f"# {a.title}\n{a.content}" for a in arts])
    max_ctx = getattr(m.config, "max_position_embeddings", getattr(tok, "model_max_length", 32768))
    joined = joined[: int(max_ctx * 0.9)]


    messages = [
        {
            "role": "system",
            "content": (
                "너는 한국어 경제/리테일/소비 트렌드 애널리스트다. "
                "반드시 '유효한 JSON 한 개'만 출력하라. "
                "말머리/설명/코드블록 없이, 아래 스키마 그대로 출력하라."
            ),
        },
        {
            "role": "user",
            "content": (
                "아래 기사 묶음을 요약해 bullets, key_stats, risks, opportunities 키를 포함한 JSON으로 내놔. "
                "가능하면 각 배열에 3~6개 항목을 넣고, 없으면 빈 배열을 넣어라.\n\n"
                + joined
                + "\n\n출력 JSON 예시:\n"
                "{\n"
                '  \"bullets\": [\"...\"],\n'
                '  \"key_stats\": [\"...\"],\n'
                '  \"risks\": [\"...\"],\n'
                '  \"opportunities\": [\"...\"]\n'
                "}\n"
            ),
        },
    ]
    prompt_ids = tok.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(device)

    
    eot_id = None
    for tkn in ("<|eot_id|>", "<|eot|>"):
        try:
            tid = tok.convert_tokens_to_ids(tkn)
            if tid is not None and tid != tok.unk_token_id:
                eot_id = tid
                break
        except Exception:
       	    pass
    eos_id = eot_id if eot_id is not None else (tok.eos_token_id or tok.pad_token_id)
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else eos_id

    gen_kwargs = dict(
        max_new_tokens=500,  # VRAM 안정성
        do_sample=False,
        eos_token_id=eos_id,
        pad_token_id=pad_id,
    )

    try:
        with torch.inference_mode():
            out = m.generate(prompt_ids, **gen_kwargs)
    except RuntimeError as e:
        # GPU 커널 문제 등 발생 시 CPU 폴백
        if "no kernel image is available for execution on the device" in str(e) or "CUDA error" in str(e):
            print("[trend_summary] CUDA runtime error detected. Falling back to CPU generate().")
            m = m.to("cpu")
            prompt_ids = prompt_ids.to("cpu")
            with torch.inference_mode():
                out = m.generate(prompt_ids, **gen_kwargs)
        else:
            raise


    new_tokens = out[0, prompt_ids.shape[-1] :]
    txt = tok.decode(new_tokens, skip_special_tokens=True)
    
    js = _safe_parse_to_json(txt)

    end = to_date_iso(datetime.now(timezone.utc))
    start = to_date_iso(datetime.now(timezone.utc) - timedelta(days=7))
    return TrendSummary(
        period_start=start,
        period_end=end,
        keywords=[],
        bullets=js.get("bullets", []),
        key_stats=js.get("key_stats", []),
        risks=js.get("risks", []),
        opportunities=js.get("opportunities", []),
        sources=[a.url for a in arts],
        model=model,
        raw_response=js,
    )


def run(db: str, keywords: List[str], days: int, max_articles: int, model: str) -> TrendSummary:
    """
    메인 엔트리 (DB 없이 동작):
    - 기사 수집 (2025년 기사만, 최근 N일)
    - 기사 0건이면 데모 fallback 요약
    - 기사 있으면 Kanana 요약
    """
    print(f"[run] (DB unused) keywords={keywords}, days={days}, max_articles={max_articles}, model={model}")

    arts = collect_articles(keywords, days, max_articles)
    print(f"[run] collected articles={len(arts)}")

    # 기사 0건 대응: UI가 비지 않도록 데모용 요약 채움
    if not arts:
        end = to_date_iso(datetime.now(timezone.utc))
        start = to_date_iso(datetime.now(timezone.utc) - timedelta(days=days))

        joined_kw = ", ".join(keywords) if keywords else "소비 트렌드"
        print("[run] NO ARTICLES -> using demo fallback summary")

        demo_bullets = [
            f"'{joined_kw}' 키워드로 최근 {days}일간 (2025년 기준) 수집된 기사가 충분하지 않아, 대표적인 생활 소비 트렌드 예시를 대신 제공합니다.",
            "카페·소확행, 근거리 여행, 구독 다이어트처럼 일상에 밀접한 소비 패턴이 계속 관찰되고 있습니다.",
        ]
        demo_key_stats = [
            "2030 직장인 기준, '하루 한 잔' 카페 루틴은 유지되면서 리필·구독·편의점 커피 등 단가를 낮추는 선택이 늘고 있습니다.",
            "장거리 해외 여행보다 근교 소도시·당일치기 중심의 짧고 잦은 여행 지출 패턴이 증가하는 추세입니다.",
            "OTT·클라우드·교육 서비스 등 구독형 상품을 주기적으로 정리하는 '구독 다이어트' 수요가 커지고 있습니다.",
        ]
        demo_risks = [
            "사용하지 않는 구독이 누적될 경우, 인지하지 못한 고정비가 매달 지출을 압박할 수 있습니다.",
            "카페·외식, 여가·취미 지출이 소액이라도 자주 발생하면 예산 대비 체감보다 큰 지출로 이어질 수 있습니다.",
        ]
        demo_opps = [
            "정기 결제 캘린더와 연동해 '해지 후보 구독'을 자동 추천하는 기능에 대한 니즈가 존재합니다.",
            "카페·식비 예산을 '하루 한 잔 루틴'에 맞춰 미리 쪼개서 보여주면, 체감 관리 난이도가 낮아질 수 있습니다.",
            "근거리 여행 패턴을 분석해 '교통비 + 경험 위주 소비' 조합에 맞는 예산 가이드를 제안할 수 있습니다.",
        ]

        return TrendSummary(
            period_start=start,
            period_end=end,
            keywords=keywords,
            bullets=demo_bullets,
            key_stats=demo_key_stats,
            risks=demo_risks,
            opportunities=demo_opps,
            sources=[],
            model=model,
            raw_response={"note": "no_articles_demo"},
        )


    s = summarize_with_kanana(arts, model)
    s.keywords = keywords
    return s


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--keywords", required=True)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--max-articles", type=int, default=30)
    p.add_argument("--db", default="./openwallet_trends.db")  # 호환용 인자 (지금은 사용 안 함)
    p.add_argument("--model", default="kakaocorp/kanana-1.5-2.1b-instruct-2505")
    a = p.parse_args()

    s = run(
        a.db,
        [k.strip() for k in a.keywords.split(",") if k.strip()],
        a.days,
        a.max_articles,
        a.model,
    )

    print(f"\n기간: {s.period_start} ~ {s.period_end}\n")
    for b in s.bullets:
        print(" -", b)
        