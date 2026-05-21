import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

KEYWORDS = [
    "Z세대", "MZ세대", "잘파세대", "알파세대", "1020세대", "2030세대",
    "매출 급증", "청년층", "완판", "품귀현상", "유행", "품절대란",
    "거래액 증가", "거래액 하락", "트렌드", "유동인구 급증",
    "매진", "론칭", "미국 Z세대", "일본 Z세대", "중국 Z세대",
    "틱톡 트렌드", "틱톡 해시태그", "팝업스토어", "숏폼",
    "K-푸드", "K-뷰티", "K-패션", "신제품 출시", "소비 트렌드", "구매 트렌드",
    "오픈 1호점", "코어 트렌드"
]

EXCLUDE_KEYWORDS = ["정치", "사건", "사고", "수사", "재판", "선거", "국회", "대통령"]

def fetch_news(keyword, display=10):
    enc_keyword = urllib.parse.quote(keyword)
    url = f"https://openapi.naver.com/v1/search/news.json?query={enc_keyword}&display={display}&sort=date"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", CLIENT_ID)
    request.add_header("X-Naver-Client-Secret", CLIENT_SECRET)
    try:
        response = urllib.request.urlopen(request)
        result = json.loads(response.read().decode("utf-8"))
        return result.get("items", [])
    except Exception as e:
        print(f"키워드 '{keyword}' 검색 실패: {e}")
        return []

def clean_html(text):
    import re
    return re.sub(r"<[^>]+>", "", text).strip()

def is_relevant(item):
    title = clean_html(item.get("title", ""))
    for word in EXCLUDE_KEYWORDS:
        if word in title:
            return False
    return True

def parse_date(pub_date_str):
    try:
        dt = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S +0900")
        return dt.strftime("%Y-%m-%d")
    except:
        return datetime.now().strftime("%Y-%m-%d")

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    all_items = []
    seen_urls = set()

    for keyword in KEYWORDS:
        items = fetch_news(keyword, display=10)
        for item in items:
            url = item.get("originallink") or item.get("link")
            if url in seen_urls:
                continue
            if not is_relevant(item):
                continue
            pub_date = parse_date(item.get("pubDate", ""))
            if pub_date not in [today, yesterday]:
                continue
            seen_urls.add(url)
            all_items.append({
                "title": clean_html(item.get("title", "")),
                "url": url,
                "source": item.get("originallink", "").split("/")[2] if item.get("originallink") else "",
                "date": pub_date,
                "description": clean_html(item.get("description", "")),
                "keyword": keyword
            })

    all_items.sort(key=lambda x: x["date"], reverse=True)

    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "articles.json")
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    existing_urls = {a["url"] for a in existing}
    new_items = [a for a in all_items if a["url"] not in existing_urls]

    combined = new_items + existing
    combined = combined[:300]

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"수집 완료: {len(new_items)}개 신규 기사 추가 (총 {len(combined)}개)")

if __name__ == "__main__":
    main()
