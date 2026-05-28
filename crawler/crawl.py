import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

# 우선순위 높은 키워드 (상단 노출)
PRIORITY_KEYWORDS = [
    "Z세대", "MZ세대", "잘파세대", "알파세대", "1020세대",
    "2030", "20대", "30대",
    "완판", "품귀현상", "유행", "품절대란",
    "거래액 증가", "거래액 하락", "트렌드", "유동인구 급증",
    "매진", "미국 Z세대", "일본 Z세대", "중국 Z세대", "해외 Z세대", "글로벌 Z세대",
    "틱톡 트렌드", "틱톡 해시태그",
]

# 우선순위 낮은 키워드 (하단 노출)
SECONDARY_KEYWORDS = [
    "팝업스토어", "숏폼", "청년층", "론칭",
    "K-푸드", "K-뷰티", "K-패션", "신제품 출시", "소비 트렌드", "구매 트렌드",
    "오픈 1호점", "코어 트렌드"
]

KEYWORDS = PRIORITY_KEYWORDS + SECONDARY_KEYWORDS

EXCLUDE_KEYWORDS = [
    # 정치/사회
    "정치", "정책", "사건", "사고", "수사", "재판", "선거", "국회", "대통령",
    "판세", "깜깜이", "여론조사", "후보",
    # 금융/주식
    "ETF", "레버리지", "코스피", "코스닥",
    "펀드", "채권", "증시", "배당", "공모", "IPO", "선물", "옵션",
    # 지자체/행정
    "시청", "구청", "민생대책", "점검회의", "지자체", "청렴", "공모전",
    # 부동산
    "분양", "청약", "아파트", "재개발", "재건축", "입주 예정",
    # 개인사
    "임신", "출산", "이혼",
]

STOP_WORDS = {
    '및', '와', '과', '이', '가', '을', '를', '은', '는', '의', '에', '로', '으로',
    '하는', '하고', '하며', '통해', '위해', '대한', '관련', '등', '도', '도록',
    '위한', '따른', '한', '된', '되는', '있는', '있다', '있어', '통한', '에서',
    '으로', '이라', '라고', '이고', '으며', '만에', '까지', '부터', '만큼'
}

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
    description = clean_html(item.get("description", ""))
    text = title + " " + description
    for word in EXCLUDE_KEYWORDS:
        if word in text:
            return False
    return True

def is_similar_title(new_title, existing_titles, threshold=3):
    new_words = set(new_title.split()) - STOP_WORDS
    for existing_title in existing_titles:
        existing_words = set(existing_title.split()) - STOP_WORDS
        common = new_words & existing_words
        if len(common) >= threshold:
            return True
    return False

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
    seen_titles = []

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

            title = clean_html(item.get("title", ""))

            if is_similar_title(title, seen_titles):
                continue

            seen_urls.add(url)
            seen_titles.append(title)
            all_items.append({
                "title": title,
                "url": url,
                "source": item.get("originallink", "").split("/")[2] if item.get("originallink") else "",
                "date": pub_date,
                "description": clean_html(item.get("description", "")),
                "keyword": keyword
            })

    priority_items = sorted(
        [a for a in all_items if a["keyword"] in PRIORITY_KEYWORDS],
        key=lambda x: x["date"], reverse=True
    )
    secondary_items = sorted(
        [a for a in all_items if a["keyword"] not in PRIORITY_KEYWORDS],
        key=lambda x: x["date"], reverse=True
    )
    all_items = priority_items + secondary_items

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
