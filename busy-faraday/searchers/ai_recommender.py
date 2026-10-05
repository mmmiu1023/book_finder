import os
import json
import re
import urllib.parse
from bs4 import BeautifulSoup
import requests
from config import DEFAULT_HEADERS

class AIRecommender:
    def __init__(self, api_key=None, provider="gemini"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.provider = provider

    def recommend_books(self, user_query):
        """
        Takes user query/mood/interests and returns a list of recommended book titles,
        authors, genres, and reasons for recommendation.
        """
        if not user_query:
            return []

        # 1. Try real LLM if api_key is available
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                prompt = f"""
당신은 최고의 도서 큐레이터 및 사서 AI입니다.
사용자의 질문과 관심사에 가장 정확하게 부합하는 대표적인 실제 도서 3권을 엄선하여 추천해 주세요.
사용자 요청: "{user_query}"

응답은 반드시 아래 JSON 배열 형식으로만 반환해야 합니다:
[
  {{
    "title": "도서의 정확한 실제 제목",
    "author": "저자명",
    "genre": "분야/장르",
    "reason": "사용자의 질문에 부합하는 구체적이고 전문적인 추천 이유 (2~3문장)"
  }}
]
"""
                response = model.generate_content(prompt)
                text = response.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                parsed = json.loads(text)
                if isinstance(parsed, list) and len(parsed) > 0:
                    return parsed
            except Exception as e:
                print(f"[AIRecommender] LLM generation error: {e}")

        # 2. Intelligent Topic-Aware & Real Live Book Search
        return self._intelligent_search_recommend(user_query)

    def _intelligent_search_recommend(self, query):
        """
        Extracts core subject and queries live bookstores for exact matching books.
        """
        q = query.lower()

        # Specific well-known curated domains
        if any(w in q for w in ["사이코패스", "소시오패스", "범죄심리", "프로파일", "살인마", "악인"]):
            return [
                {
                    "title": "괴물의 심연",
                    "author": "제임스 팰런",
                    "genre": "뇌과학/심리학",
                    "reason": "사이코패스 뇌를 연구하던 신경과학자가 자신의 뇌가 사이코패스와 동일하다는 충격적 사실을 발견하고, 유전과 환경이 사이코패스를 어떻게 만드는지 파헤친 걸작입니다."
                },
                {
                    "title": "진단명 사이코패스",
                    "author": "로버트 D. 헤어",
                    "genre": "범죄심리학",
                    "reason": "사이코패스 진단 척도(PCL-R)를 개발한 세계 최고의 권위자가 일상과 사회 속에 숨어 있는 사이코패스의 특성과 위험성을 체계적으로 밝힌 고전입니다."
                },
                {
                    "title": "사이코패스는 일상에 산다",
                    "author": "케빈 더튼",
                    "genre": "심리학",
                    "reason": "옥스퍼드대 심리학 교수가 사이코패스의 냉혹함, 두려움 없음 등의 특성이 외과의사, CEO 등 특정 직업군에서 어떻게 발현되는지 다각도로 흥미롭게 조명합니다."
                }
            ]
        elif any(w in q for w in ["자존감", "불안", "우울", "마음", "인간관계", "지치", "번아웃"]):
            return [
                {
                    "title": "자존감 수업",
                    "author": "윤홍균",
                    "genre": "심리학/자기계발",
                    "reason": "정신건강의학과 전문의가 자존감이 무너져 상처받은 마음을 스스로 회복하고 단단하게 가꾸는 실천적인 방법들을 다정하게 안내합니다."
                },
                {
                    "title": "죽고 싶지만 떡볶이는 먹고 싶어",
                    "author": "백세희",
                    "genre": "에세이/심리",
                    "reason": "겉으로는 멀쩡해 보이지만 속은 불안과 우울에 시달리는 현대인들의 마음에 깊은 공감과 위로를 건네는 진솔한 상담 기록입니다."
                },
                {
                    "title": "미움받을 용기",
                    "author": "기시미 이치로, 고가 후미타케",
                    "genre": "인문/철학",
                    "reason": "아들러 심리학을 통해 타인의 인정에 얽매이지 않고 온전히 나 자신으로 살아가는 자유와 행복의 길을 제시합니다."
                }
            ]

        # Dynamic search: Extract core keywords from conversational Korean
        search_kw = self._clean_keywords(query)
        live_books = self._search_live_books(search_kw)
        if live_books:
            return live_books

        # Secondary search if first query failed
        words = search_kw.split()
        if len(words) > 1:
            for single_word in words:
                if len(single_word) >= 2:
                    sub_books = self._search_live_books(single_word)
                    if sub_books:
                        return sub_books

        return [
            {
                "title": f"{search_kw} 관련 추천 도서",
                "author": "추천 도서",
                "genre": "주제별 도서",
                "reason": f"'{search_kw}' 키워드와 관련하여 서점 검색 탭에서 상세 도서를 확인해보세요."
            }
        ]

    def _clean_keywords(self, prompt):
        """Extract core search nouns from natural language prompt."""
        # Strip fillers at the start (e.g. 음..., 어..., 음ㅁㅁ)
        p = re.sub(r'^[음어아그\sㄱ-ㅎㅏ-ㅣ]+', '', prompt).strip()
        
        # Conversational endings
        patterns = [
            r'(쪽이고싶은데|쪽으로|쪽이고|쪽이|쪽)',
            r'(읽고싶다고|읽고싶은데|읽고싶어|읽고싶다|보고싶다|보고싶어|보고싶은데)',
            r'(알고싶은데|알고싶다|알고싶어|알려줘|알려주세요|가르쳐줘)',
            r'(추천해줘|추천해|추천좀|추천|부탁해|해줘)',
            r'(관련해서|관련된|관련|대해서|대해|관한)',
            r'(배우고싶은데|배우고싶다|배우고싶어|공부하고싶어|공부)',
            r'(어떤|무슨|좋을까|좋은|책이|책|있을까|있나요|하고싶은데|싶은데|싶어|싶다)'
        ]
        for pat in patterns:
            p = re.sub(pat, ' ', p)
            
        p = re.sub(r'(의|를|을|에|에서|로|으로|과|와|도)\b', ' ', p)
        p = p.replace("사이코 패스", "사이코패스")
        p = re.sub(r'[^\w\s]', ' ', p)
        words = [w.strip() for w in p.split() if len(w.strip()) >= 2]
        return " ".join(words) if words else prompt.strip()

    def _search_live_books(self, keyword):
        """Query Aladin for top live books matching the extracted keyword."""
        books = []
        if not keyword:
            return books
        try:
            url = f"https://www.aladin.co.kr/search/wsearchresult.aspx?SearchWord={urllib.parse.quote(keyword)}"
            r = requests.get(url, headers=DEFAULT_HEADERS, timeout=6)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                boxes = soup.select(".ss_book_box")
                for box in boxes[:3]:
                    title_elem = box.select_one("a.bo3, a.bo_title")
                    if not title_elem:
                        continue
                    title = title_elem.text.strip()
                    title = re.sub(r'\[.*?\]', '', title).strip()

                    info_elem = box.select_one(".ss_book_list ul li:nth-child(2)") or box.select_one(".ss_book_list ul li:nth-child(3)")
                    author_text = info_elem.text.strip() if info_elem else "저자 정보"
                    author = author_text.split("|")[0].strip() if "|" in author_text else author_text

                    books.append({
                        "title": title,
                        "author": author,
                        "genre": f"{keyword} 추천도서",
                        "reason": f"'{keyword}'에 관심 있는 독자들이 많이 찾는 대표 도서입니다."
                    })
        except Exception as e:
            print(f"[AIRecommender] Live book search error: {e}")

        return books
