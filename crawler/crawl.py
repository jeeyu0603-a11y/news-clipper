import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from itertools import groupby

CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

KEYWORD_PRIORITY = {
    # 1점 - 최우선
    "Z세대": 1, "MZ세대": 1, "잘파세대": 1, "알파세대": 1, "1020세대": 1, "Z세대 트렌드": 1,
    # 2점
    "미국 Z세대": 2, "일본 Z세대": 2, "중국 Z세대": 2, "해외 Z세대": 2, "글로벌 Z세대": 2,
    "틱톡 트렌드": 2, "틱톡 해시태그": 2, "트렌드": 2, "유행": 2,
    # 3점
    "완판": 3, "품귀현상": 3, "품절대란": 3,
    "거래액 증가": 3, "거래액 하락": 3, "유동인구 급증": 3, "매진": 3,
    "브랜드": 3, "1위": 3,
    # 4점
    "2030세대": 4, "20대": 4, "30대": 4,
    # 5점
    "팝업스토어": 5, "숏폼": 5, "청년층": 5, "론칭": 5,
    "K-푸드": 5, "K-뷰티": 5, "K-패션": 5,
    "신제품 출시": 5, "소비 트렌드": 5, "구매 트렌드": 5, "코어": 5,
}

KEYWORDS = list(KEYWORD_PRIORITY.keys())

ALLOWED_DOMAINS = [
    "biz.chosun.com",
    "hankyung.com",
    "magazine.hankyung.com",
    "mk.co.kr",
    "biz.heraldcorp.com",
    "mt.co.kr",
    "edaily.co.kr",
    "sedaily.com",
    "asiae.co.kr",
    "fnnews.com",
    "yna.co.kr",
    "newsis.com",
    "joongang.co.kr",
    "donga.com",
    "kmib.co.kr",
    "insight.co.kr",
    "dailypop.kr",
    "apparelnews.co.kr",
    "zdnet.co.kr",
    "etnews.com",
]

EXCLUDE_KEYWORDS = [
    # 정치
    "정치", "선거", "국회", "대통령", "대선", "총선", "여당", "야당",
    "여의도", "민주당", "국민의힘", "정당", "창당", "탄핵", "개헌",
    "의원", "당대표", "장관", "총리", "청와대", "대통령실",
    "공천", "출마", "당선", "판세", "깜깜이", "여론조사", "후보",
    # 법/수사/범죄
    "사건", "사고", "재판", "수사", "검찰", "경찰", "법원", "판결", "기소",
    "구속", "체포", "검거", "고소", "고발", "형사", "소송",
    "처벌", "징역", "벌금", "무죄", "유죄", "항소",
    "살해", "살인", "폭행", "보복", "강도", "절도", "납치", "방화", "피의자", "범행",
    # 금융/주식
    "ETF", "레버리지", "코스피", "코스닥",
    "펀드", "채권", "증시", "배당", "공모", "IPO", "선물", "옵션",
    # 부동산
    "분양", "청약", "아파트", "재개발", "재건축", "입주", "전세", "월세", "매매", "부동산", "임대", "LH",
    # 지자체/행정
    "구청", "민생대책", "점검회의", "지자체", "청렴", "공모전",
    # 순수 과학
    "논문", "학술", "임상시험", "우주", "천문", "물리", "화학반응", "유전자", "세포", "분자", "방사선", "지진", "화산",
    # 개인사
    "임신", "출산", "이혼",
    # 연예/엔터
    "컴백", "차트", "뮤직비디오", "음원", "앨범", "팬미팅", "콘서트", "배우", "캐스팅", "출연",
    "주인공", "주연", "조연", "맹활약", "열연", "극중", "촬영",
    # 예능/방송
    "예능", "방영", "편성", "첫방", "송출", "재개", "시즌",
]

STOP_WORDS = {
    '및', '와', '과', '이', '가', '을', '를', '은', '는', '의', '에', '로', '으로',
    '하는', '하고', '하며', '통해', '위해', '대한', '관련', '등', '도', '도록',
    '위한', '따른', '한', '된', '되는', '있는', '있다', '있어', '통한', '에서',
    '으로', '이라', '라고', '이고', '으며', '만에', '까지', '부터', '만큼'
}

def fetch_news(keyword, display=100):
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
    day_before = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    day_before2 = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

    all_items = []
    seen_urls = set()
    seen_titles = []

    total_raw = 0
    filtered_domain = 0
    filtered_exclude = 0
    filtered_date = 0
    filtered_keyword_title = 0
    filtered_duplicate = 0

    for keyword in KEYWORDS:
        items = fetch_news(keyword, display=100)
        for item in items:
            total_raw += 1
            url = item.get("originallink") or item.get("link")
            if url in seen_urls:
                filtered_duplicate += 1
                continue

            domain = url.split("/")[2] if url else ""
            if not any(allowed in domain for allowed in ALLOWED_DOMAINS):
                filtered_domain += 1
                continue

            if not is_relevant(item):
                filtered_exclude += 1
                continue

            pub_date = parse_date(item.get("pubDate", ""))
            if pub_date not in [today, yesterday, day_before, day_before2]:
                filtered_date += 1
                continue

            title = clean_html(item.get("title", ""))

            if keyword not in title:
                filtered_keyword_title += 1
                continue

            if is_similar_title(title, seen_titles):
                filtered_duplicate += 1
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

    print(f"=== 필터 단계별 결과 ===")
    print(f"총 수집 시도: {total_raw}개")
    print(f"도메인 필터 제거: {filtered_domain}개")
    print(f"제외 키워드 제거: {filtered_exclude}개")
    print(f"날짜 필터 제거: {filtered_date}개")
    print(f"키워드-제목 불일치 제거: {filtered_keyword_title}개")
    print(f"중복 제거: {filtered_duplicate}개")
    print(f"최종 통과: {len(all_items)}개")

    all_items_by_score = sorted(all_items, key=lambda x: KEYWORD_PRIORITY.get(x["keyword"], 99))
    sorted_items = []
    for score, group in groupby(all_items_by_score, key=lambda x: KEYWORD_PRIORITY.get(x["keyword"], 99)):
        sorted_items.extend(sorted(group, key=lambda x: x["date"], reverse=True))
    all_items = sorted_items

    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "articles.json")
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = []

    seen_combined = set()
    combined = []
    for item in all_items + existing:
        if item["url"] not in seen_combined:
            seen_combined.add(item["url"])
            combined.append(item)
    combined = combined[:300]

    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"수집 완료: 오늘 {len(all_items)}개 기사 수집 (총 {len(combined)}개 저장)")

if __name__ == "__main__":
    main()
